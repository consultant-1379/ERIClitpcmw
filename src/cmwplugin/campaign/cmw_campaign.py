##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import tempfile
from datetime import datetime
import shutil
import os
import lxml.etree as xml
import glob

from litp.core.litp_logging import LitpLogger
from cmwplugin.campaign.cmw_entities import cmwLSBComponent
log = LitpLogger()
from cmwplugin.campaign.amf_cgs_tools import AmfCgsTools
from cmwplugin.campaign.cmw_software import generate_sdp
from cmwplugin.campaign.cmw_software_manager import cmwSoftwareManager
from cmwplugin.campaign import cmw_constants


class cmwCampaign(object):
    '''
    :summary: Class holds Campaign information
    '''

    def __init__(self, campaign_name, bundles, sg=None):
        '''
        Constructor
        '''
        self.campaign_name = campaign_name
        self.bundles = bundles
        self.type = None
        self.sg = sg


class cmwCampaignGenerator(object):

    def __init__(self):
        self._workspace = None
        self.amf_cgs = None
        path = os.path.dirname(cmw_constants.__file__)
        self._templates = os.path.join(path, "./templates")

    def generate_nonamf(self, base_name, node_list, bundle_names):
        try:
            etf_path = os.path.join(self._workspace, "ETF.xml")
            shutil.copy2(os.path.join(self._templates, "ETF_bundle.xml"),
                         etf_path)
            campaign_name = self._get_nonamf_campaign_name(base_name)
            self.amf_cgs.do_generatenonamf(base_name)

            for bundle in bundle_names:
                self.amf_cgs.do_addswadd(bundle, node_list)

            self.amf_cgs.run_amfcgs()

        except Exception as e:
            log.trace.debug("AMF-CGS Exception: %s" % str(e))
            msg = ('Failed to run amf-cgs tool, check the logs '
                    'for more information')
            log.event.error(msg)

            raise Exception(msg)
        if not generate_sdp(campaign_name, self._workspace,
                     cmw_constants.LITP_SDP_REPO,
                     files=("campaign.xml", "ETF.xml")):
            raise Exception("Failed to create campaign %s" %
                                                campaign_name)
        return cmwCampaign(campaign_name, bundle_names)

    def generate_install(self, sg, campaign_name):
        self._workspace = tempfile.mkdtemp()
        print "************"
        print self._workspace
        print "************"
        tweak_app_type = False
        self.amf_cgs = AmfCgsTools(self._workspace)
        #campaign_name = self._get_install_campaign_name(sg.name)
        etf_path = os.path.join(self._workspace, "ETF.xml")
        # TODO: remove this from here to better test this in isolation
        shutil.copy2(sg.etf_file.path, etf_path)
        #cmwETFGenerator.update_etf_template(etf_path, campaign_name, "3PP")
        # TODO: do I really need to that here?
        scs_count = 0
        pls_count = 0
        for node in sg.node_list:
            if node.startswith("SC"):
                scs_count += 1
            elif node.startswith("PL"):
                pls_count += 1
        #print scs_count
        #print pls_count
        self.amf_cgs.do_createui(scs_count, pls_count)
        node_list = ",".join(sg.node_list)
        node_group = sg.name + "_NodeGroup"
        self.amf_cgs.do_addnodegroup(node_group, node_list)
        red_model = cmw_constants.REDUNDANCY_MODEL[sg.availability_model]

        self.amf_cgs.do_addsg(sg.name, red_model, node_group, sg.active_count,
                     sg.standby_count)
        active_assignments = sg.active_count
        # XXX Number of CSI's should be sg.active_count but CMW doesn't support
        # more than 1 CSI for NPI components
        no_of_csis = "1"
        #no_of_sus = sg.active_count + sg.standby_count

        si_name = sg.name + "-SI"
        self.amf_cgs.do_addsitemplate(si_name, sg.name,
                                    sg.svc_type, active_assignments)
        for comp in sg.comps:
            # TODO check how many CSI are needed
            self.amf_cgs.do_addcsitemplates(si_name, sg.name, comp.name,
                                                comp.cs_type,
                                                no_of_csis=no_of_csis)

        self.amf_cgs.do_generate_etfui()

        if sg.dependency:
            if red_model == "SA_AMF_2N_REDUNDANCY_MODEL":
                for dep in sg.dependency:
                    if dep:  # TODO:migrate this checks to validation
                        dep_si_name = dep + "-SI"
                        dep_config = os.path.join(
                                    cmw_constants.LITP_DATA_DIR,
                                    "configuration_%s.ac" % dep)
                        self.amf_cgs.do_addsidependency(si_name, dep_si_name,
                                                    dep_config, sg.app_name,
                                                    sg.app_name)
        self.amf_cgs.do_generate_conf()
        for comp in sg.comps:
            if isinstance(comp, cmwLSBComponent):
                do_cmd = "/sbin/chkconfig %s off" % comp.service_name
                undo_cmd = "/sbin/chkconfig %s on" % comp.service_name
                self.amf_cgs.do_addcampaignaction("1", do_cmd, undo_cmd,
                                                  node_list)
        # NEEDS to be called after the campaign is generated
        # I need add commands just for the ones that are not referenced on the
        # bundlereference of the comptype, so skipping the first
        for bundle in sg.bundles[1:]:
            self.amf_cgs.do_addswadd(bundle.name, node_list)

        self.amf_cgs.run_amfcgs()
        campaign_path = os.path.join(self._workspace, "campaign.xml")

        confs = os.path.join(cmw_constants.LITP_DATA_DIR, "configuration_*.ac")
        if glob.glob(confs):
            tweak_app_type = True

        # Tweak
        self._campaign_tweaks(campaign_path, campaign_name, tweak_app_type)
        camp_bundle = cmwSoftwareManager.create_sdp(campaign_name,
                                                    self._workspace,
                                                cmw_constants.LITP_SDP_REPO,
                                            files=("campaign.xml", "ETF.xml"))
        if not camp_bundle:
            raise Exception("Failed to create campaign %s" %
                                                campaign_name)

        # Copy configuration for use to inject si deps
        conf_path = "configuration_{0}.ac".format(sg.name)
        conf_path = os.path.join(cmw_constants.LITP_DATA_DIR, conf_path)
        shutil.copy2(self.amf_cgs.config_ac, conf_path)

        return cmwCampaign(campaign_name, sg.bundles + [camp_bundle], sg=sg)

    def _campaign_tweaks(self, campaign_path, campaign_name, tweak_app_type):
        campaign_xml = xml.parse(campaign_path)
        self.__fix_campaign_name(campaign_xml, campaign_name)
        self.__add_healtcheck(campaign_xml)
        self.__increase_timeouts(campaign_xml)
        self.__add_retries(campaign_xml)
        if tweak_app_type:
            #print "removing app type from campaign"
            self.__remove_app_type(campaign_xml)

        self._save_campaign(campaign_xml, campaign_path)

    def __remove_app_type(self, campaign_xml):
        """objectClassName="SaAmfApplication"
        """
        for app_type in campaign_xml.findall("//create"):
            if app_type.get('objectClassName') == 'SaAmfApplication':
                app_type.getparent().remove(app_type)

    def __increase_tolerance_time(self, campaign_xml, tolerance):
        """ """
        for time in \
            campaign_xml.findall(".//attribute[@name='saAmfToleranceTime']"):
            for value in time.getchildren():
                value.text = str(tolerance)

    def __add_healtcheck(self, campaign_xml):
        """
        http://devel.opensaf.org/wiki/AMF/ComponentMonitoring
        """
        # Defaults are not good, will probably come from the model
        def_interval = "10000000000"
        def_timeout = "60000000000"

        # The healthCheck tag should be placed before the swBundle
        for swbundle in campaign_xml.findall(".//swBundle"):
            comptype = swbundle.getparent()
            comptype.insert(comptype.index(swbundle),
            xml.XML("""<healthCheck
            safHealthcheckKey="safHealthcheckKey=osafHealthCheck"
            saAmfHealthcheckPeriod="{0}"
            saAmfHealthcheckMaxDuration="{1}"/>""".format(def_interval,
                                                          def_timeout)))

    def __fix_campaign_name(self, campaign_xml, campaign_name):
        root = campaign_xml.getroot()
        root.attrib["safSmfCampaign"] = "safSmfCampaign=" + campaign_name

    def __increase_timeouts(self, campaign_xml):
        """ """
        for comp in campaign_xml.findall(".//compTypeDefaults"):
            comp.attrib["saAmfCtDefCallbackTimeout"] = "10000000000000"
            comp.attrib["saAmfCtDefClcCliTimeout"] = "10000000000000"

    def __add_retries(self, campaign_xml):
        """
        https://cc-jira.rnd.ki.sw.ericsson.se/browse/CC-1147
        """
        for comp in \
            campaign_xml.findall(".//create[@objectClassName='SaAmfComp']"):
            comp.append(xml.XML("""<attribute
                        name="saAmfCompNumMaxInstantiateWithoutDelay"
                        type="SA_IMM_ATTR_SAUINT32T">
                        <value>5</value>
                        </attribute>"""))

    def _save_campaign(self, xml_obj, campaign_path):
        parser = xml.XMLParser(remove_blank_text=True)
        root = xml.XML(xml.tostring(xml_obj, encoding="UTF-8"), parser)
        with open(campaign_path, "w") as f:
            f.write(xml.tostring(root, encoding="UTF-8", pretty_print=True))

    def _get_nonamf_campaign_name(self, base_name):
        return "3PP-" + base_name + "_SMFInstall"

    def _get_upgrade_campaign_name(self, base_name):
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M')
        return base_name + "_Upgrade_" + timestamp

    def _get_install_campaign_name(self, base_name):
        return "3PP-" + base_name + "_Install"
