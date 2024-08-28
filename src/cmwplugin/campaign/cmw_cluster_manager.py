##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import traceback
import os

from cmwplugin.campaign.cmw_entities import cmwApp
from cmwplugin.campaign.cmw_entities import cmw2NServiceGroup
from cmwplugin.campaign.cmw_entities import cmwLSBComponent
from cmwplugin.campaign.cmw_entities import cmwNWayActiveServiceGroup
from cmwplugin.campaign.cmw_software_manager import cmwSoftwareManager
from cmwplugin.campaign.cmw_exec_manager import cmwExecutionManager
from cmwplugin.campaign.cmw_campaign import cmwCampaignGenerator
from cmwplugin.campaign.campaign_runner import CampaignRunner
from cmwplugin.campaign.cmw_etf import cmwETFGenerator
from litp.core.litp_logging import LitpLogger
from cmwplugin.campaign import cmw_constants, cmw_config
log = LitpLogger()


class cmwClusterManager(object):
    '''
    Main manager for CMW HA
    '''

    def __init__(self, primary_node, nodes, services_dict):
        '''
        Constructor
        '''
        self.primary_node = primary_node
        self.nodes = nodes
        self.services = services_dict
        self.apps = []
        self.campaigns = []
        self.etfs = []
        # FIXME: consolidate naming for this, cmw_ seems a bit long
        self.soft_mgr = cmwSoftwareManager()
        self.cmw_exec_mgr = cmwExecutionManager(primary_node)
        self.cmw_camp_gen = cmwCampaignGenerator()
        self.cmw_etf_gen = cmwETFGenerator()
        self._parse_data()

    def _parse_data(self):
        """
        parse_data
        """
        app = cmwApp("Litp_app")
        for item in self.services:
            print "Processing for Clustered service %s" % item
            base_name = item

            nodes = [node["amf-name"] for node in self.services[item]
                                                        ["nodes"].values()]
            deps = [svc["name"] for svc in \
                    self.services[item]["dependencies"].values()]
            active = self.services[item]["active"]
            standby = self.services[item]["standby"]
            apps = self.services[item]["applications"]
            if len(apps) > 1:
                raise Exception("No support for multiple applications")
            elif len(apps) < 1:
                raise Exception("You need at least one service")
            for service_id, service in apps.items():
                service_name = service["service_name"]
                cleanup_cmd = service["cleanup_command"]
                packages = service["packages"].values()

                if active == "1" and standby == "1":
                    if service["type"] not in ["service-base", "service"]:
                        raise Exception("2N only supported for 'service' type")
                    log.event.info("Service %s - 2N service: active %s " \
                                   "standby %s" % (service_id, active,
                                                   standby))
                    sg = cmw2NServiceGroup(base_name, "1.0.0")
                    sg.availability_model = "2n"
                elif int(active) >= 1 and standby == "0":
                    log.event.info("Service %s - NWayActive active %s " \
                                "standby %s" % (service_id, active, standby))
                    sg = cmwNWayActiveServiceGroup(base_name, int(active))
                    sg.availability_model = "nway-active"
                else:
                    msg = ("Just 1 active, 1 standy, or N active, 0 standby,"
                           " supported")
                    log.event.error(msg)
                    raise NotImplementedError(msg)

                sg.active_count = int(active)
                sg.standby_count = int(standby)
                comp = cmwLSBComponent(service_id, base_name,
                                       "1.0.0", service_name, cleanup_cmd)
                #sg.install_source = install_source
                # See if any commands has been overridden
                for command in ["start_command", "stop_command",
                                "status_command", "cleanup_command"]:
                    cmd_val = None
                    try:
                        cmd_val = service[command]
                    except KeyError:
                        continue
                    if cmd_val:
                        # Every command should be relative to /opt
                        setattr(comp, command, ".." + cmd_val)
                if not packages:
                    sg.bundles.append(self.soft_mgr.get_dummy_sdp())
                else:
                    for pkg in packages:
                        sg.bundles.append(self.soft_mgr.get_sdp(pkg))
                sg.comps.append(comp)
                sg.dependency.extend(deps)
                sg.node_list.extend(nodes)
                app.service_groups.append(sg)

        self.apps.append(app)

    def generate_campaigns(self):
        # TODO, update campaign
        for app in self.apps:
            for sg in app.service_groups:
                try:
                    campaign_name = \
                        self.cmw_camp_gen._get_install_campaign_name(
                                                                    sg.name)
                    sg.etf_file = self.cmw_etf_gen.generate_sg_etf(sg,
                                                                campaign_name)
                    sg.etf_file.write_to_disk()
                    self.campaigns.append(
                                        self.cmw_camp_gen.generate_install(sg,
                                                               campaign_name))
                    for bundle in sg.bundles:
                        if not self.soft_mgr.sdp_exists(bundle.name):
                            bundle.pack()
                except Exception as e:
                    log.event.error("Error while creating campaigns")
                    log.event.error(traceback.format_exc())
                    for campaign in self.campaigns:
                        self._clean_up(campaign)
                    raise e

    def execute_campaigns(self, primary_node, ms_ip):
        campaign_runner = CampaignRunner(primary_node,
                                         cmw_constants.LITP_SDP_REPO)
        cmw_conf = cmw_config.cmwConfig()
        # TODO: need to check if the list order is correct
        for campaign in self.campaigns:
            for bundle in campaign.bundles:
                if cmw_conf.read_plugin_config("imported_sdps", bundle.name) \
                                                                != bundle.path:
                    #FIXME where to put this in the node?
                    filepath, filename = os.path.split(bundle.path)
                    self.cmw_exec_mgr.transfer_files(primary_node,
                                                     ms_ip,
                                                     "/tmp",
                                                     filepath,
                                                     filename)
                    self.cmw_exec_mgr.import_sdps(primary_node,
                                                  filename)
                    cmw_conf.write_plugin_config("imported_sdps", bundle.name,
                                                 bundle.path)
            try:
                campaign_runner.execute_campaign(campaign.campaign_name)
            except:  # pylint: disable=W0702
                self._clean_up(campaign)
                raise

    def _clean_up(self, campaign):
        if campaign.sg:
            conf_path = "configuration_{0}.ac".format(campaign.sg.name)
            conf_file = os.path.join(cmw_constants.LITP_DATA_DIR,
                                                                conf_path)
            etf_path = "ETF_{0}.ac".format(campaign.sg.name)
            etf_file = os.path.join(cmw_constants.LITP_DATA_DIR,
                                                                etf_path)
            try:
                os.remove(conf_file)
                os.remove(etf_file)
            except:  # pylint: disable=W0702
                log.event.warning("Failed to remove data files for campaign "
                                  "%s" % campaign.campaign_name)
