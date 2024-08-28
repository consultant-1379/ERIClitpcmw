##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import os
import subprocess
import tempfile
import contextlib
import shutil
from litp.core.litp_logging import LitpLogger
log = LitpLogger()


@contextlib.contextmanager
def tempdir(prefix='tmp'):
    """
    A context manager for creating and then deleting a temiporary directory.
    """
    tmpdir = tempfile.mkdtemp(prefix=prefix)
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


class AmfCgsTools(object):
    """
    @summary: Set of handy methods to build command line and call
    amf-cgs, defined in L{self.cmd}.
    """

    def __init__(self, path_prefix):
        self.cmd = "amf-cgs"
        self.camp_params = {}
        self.exec_file = os.path.join(path_prefix, "generate.txt")
        self.etf_xml = os.path.join(path_prefix, "ETF.xml")
        self.etf_ui = os.path.join(path_prefix, "ETF.ui")
        self.config_ac = os.path.join(path_prefix, "configuration0.ac")
        self.install_uc = os.path.join(path_prefix, "campaign.uc")
        self.campaign_xml = os.path.join(path_prefix, "campaign.xml")

    def run_amfcgs(self):
        """
        Execute the campaign generation CLI with parameters
        """
        cmdline = "{0} --command readfromfile --file {1}".format(
            self.cmd,
            self.exec_file)

        with tempdir() as cwd:
            p = subprocess.Popen(cmdline,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True,
                                 cwd=cwd)
            stdout, stderr = p.communicate()

        if p.returncode != 0 or stderr:
            log.event.error("Failed to run command='{0}'".format(cmdline))
            e = Exception(stderr)
            e.returncode = p.returncode
            raise e
        return (p.returncode, stdout)

    def _check_rdn_size(self, safkey, value):
        """
        Validate the size of the RDN, opensaf RDNs has a limitation
        of 64 characters
        """
        rdn = ''.join((safkey, value))
        # CMW says it's 64 but in reality it's 63 characters!!!!
        assert not len(rdn) > 63, \
            'RDN {0} is too long, must be less than 63 characters'. \
            format(rdn)

    def do_amfcgs(self, command, params):
        """
        @summary: Append the commands to a file that after will be
        executed by amf-cgs
        @param command: Command to be added
        @type command: string
        @param params: Parameters to be passed with L{command}
        @type params: dict
        """
        cmdline = "--command {0} ".format(command)
        for k in params:
            cmdline += "--{0} {1} ".format(k, params[k])
        if "password" not in cmdline:
            log.trace.debug("CampaignGeneration: " + \
                       "Appending {0}".format(cmdline))
        try:
            with open(self.exec_file, "a") as f:
                f.write(cmdline + '\n')
        except IOError as e:
            raise RuntimeError('Exception with file: %s' % str(e))

    def do_createui(self, scs_count, pls_count):
        sc_pl = '{0} {1}'.format(scs_count, pls_count)
        params = {'input': sc_pl,
                  'file': self.etf_xml,
                  'outputfile': self.etf_ui}
        return self.do_amfcgs('createui', params)

    def do_addnodegroup(self, node_group, node_list):
        input_arg = '{0} {1}'.format(node_group, node_list)
        params = {'input': input_arg, 'file': self.etf_ui}
        return self.do_amfcgs('addnodegroup', params)

    def do_generatenonamf(self, output_name):
        params = {'outputfile': output_name, 'file': self.etf_xml}
        self.do_amfcgs('generatenonamf', params)

    def do_addsg(self, sg_name, red_model,
                 node_group, active_count,
                 standby_count):
        self._check_rdn_size("safSg=", sg_name)
        input_arg = '{0} {1} {2} {3} {4} 0'.format(sg_name,
                                              red_model,
                                              node_group,
                                              active_count,
                                              standby_count)
        params = {'input': input_arg, 'file': self.etf_ui}
        return self.do_amfcgs('addservicegroup', params)

    def do_addsitemplate(self, si_name, sg_name, service_type,
                         active_assignments=1):
        self._check_rdn_size("safSi=", si_name)
        self._check_rdn_size("safSvcType=", service_type)
        input_arg = '{0} {1} safSvcType={2} {3} 0 1'.format(si_name,
                                                        sg_name,
                                                        service_type,
                                                        active_assignments)
        params = {'input': input_arg, 'file': self.etf_ui}
        return self.do_amfcgs('addsitemplate', params)

    def do_addcsitemplates(self, si_name, sg_name, comp_name, comp_cstype,
                           no_of_csis=1):
        self._check_rdn_size("safCsi=", comp_name)
        self._check_rdn_size("safCSType=", comp_cstype)
        input_arg = '{0} {1} {2} safCSType={3} {4}'.format(si_name,
                                                         sg_name,
                                                         comp_name,
                                                         comp_cstype,
                                                         no_of_csis)
        params = {'input': input_arg, 'file': self.etf_ui}
        return self.do_amfcgs('addcsitemplates', params)

    def _do_generate(self, file_name, outputfile=None):
        if not outputfile:
            return self.do_amfcgs('generate', {'file': file_name
                                           })
        else:
            return self.do_amfcgs('generate', {'outputfile': outputfile,
                                               'file': file_name
                                           })

    def do_generate_etfui(self):
        return self._do_generate(self.etf_ui)

    def do_generate_conf(self):
        return self._do_generate(self.config_ac, self.campaign_xml)

    def do_addswadd(self, bundle_name, node_list):
        self._check_rdn_size("safSmfBundle=", bundle_name)
        node_list = " ".join(node_list.split(','))
        input_arg = "safSmfProc=SingleStepProc1 "
        input_arg += "safSmfBundle={0} {1}".format(bundle_name,
                                                   node_list)
        params = {"input": input_arg, "file": self.install_uc}
        return self.do_amfcgs('addswadd', params)

    def do_addcsiattribute(self, comp_name, si_name,
                           app_name, attr, value):
        self._check_rdn_size("safCsiAttr=", attr)
        input_arg = 'safCsi={0}-0,safSi={1}-0,'.format(comp_name, si_name)
        input_arg += 'safApp={0} safCsiAttr={1} "{2}"'.format(app_name,
                                                            attr,
                                                            value)
        params = {'input': input_arg, 'file': self.config_ac}
        return self.do_amfcgs('addcsiattribute', params)

    def do_addcsidependency(self, comp_name, dep_comp_name, si_name, app_name):
        input_arg = 'safCsi={0}-0,safSi={1}-0,safApp={2} '.format(comp_name,
                                                          si_name, app_name)
        input_arg += 'safCsi={0}-0,safSi={1}-0,safApp={2}'.format(
                                                          dep_comp_name,
                                                          si_name, app_name)
        params = {'input': input_arg, 'file': self.config_ac}
        return self.do_amfcgs('addcsidependency', params)

    def do_addsidependency(self, si_name, dep_si_name, dep_config,
                           app_name, dep_app_name, tolerance=999999999):
        # By default the tolerance time is something huge because
        # they only want to have runtime order and not dependency
        # between SIs
        input_arg = 'safSi={0}-0,safApp={1} '.format(si_name, app_name)
        input_arg += 'safSi={0}-0,safApp={1} {2}'.format(dep_si_name,
                                                  dep_app_name, tolerance)
        file_ = "{0} {1}".format(self.config_ac, dep_config)

        params = {'input': input_arg, 'file': file_}
        return self.do_amfcgs('addsidependency', params)

    def do_addcampaignaction(self, phase, do_cmd, undo_cmd, node_list):
        node_list = " ".join(node_list.split(','))
        input_arg = '{0} "{1}" "{2}" {3}'.format(phase, do_cmd, undo_cmd,
                                                 node_list)
        params = {"input": input_arg, "file": self.install_uc}
        return self.do_amfcgs('addcampaignaction', params)

    def do_gen_upgrade_campaign(self, immconf_file, etf_file):
        input_arg = '{0} {1}'.format(immconf_file, etf_file)
        params = {'input': input_arg}
        return self.do_amfcgs('upgradecampaign', params)
