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
import shutil
import os
from litp.core.rpc_commands import run_rpc_command
from litp.core.litp_logging import LitpLogger

log = LitpLogger()

SUCCESS = 0
valid_campaign_status = ["INITIAL", "EXECUTING", "COMPLETED", "COMMITTED"]
WWW_ROOT = "/var/www/html"
FILE_MODE = 0605


class CmwMcoApiException(Exception):
    pass


class CmwMcoApi(object):
    '''
    '''

    def __init__(self):
        self.node = None
        self.agent = "cmw_mco_api"

    def set_node(self, nodename):
        self.node = nodename

    def _get_mco_cmw_command(self, agent, action, nodes, args=None):
        command = "\"mco rpc {0} {1} ".format(agent, action)
        if args is not None:
            for a, v in args.iteritems():
                command += "{0}={1} ".format(a, v)
        for node in nodes:
            command += "-I {0} ".format(node)
        command += "\""
        return command

    def _gen_err_str(self, agent, action, nodes, args=None):
        return "Failure to execute command: {0}"\
            .format(self._get_mco_cmw_command(agent, action, nodes, args))

    def _raise_error(self, err_str, result):
        ex = err_str
        if result is not None:
            ex += " " + str(result["retcode"])
            if "err" in result:
                ex += " " + str(result["err"])
        raise CmwMcoApiException(ex)

    def _call_mco(self, agent, mco_action, args=None, timeout=None, n=None):
        """
        general method to run MCollective commands using run_rpc_command
        and perform error handling based on MCollective issues
        """
        nodes = n if n else [self.node]

        log.trace.info('Running MCO command {0}'.\
            format(self._get_mco_cmw_command(agent, mco_action, nodes, args)))
        results = run_rpc_command(nodes, agent, mco_action, args, timeout)

        if len(results) != len(nodes):
            err_msg = self._gen_err_str(agent, mco_action, nodes, args)
            err_msg += "Reason: Expected %s response, received %s"\
                % (len(nodes), len(results))
            log.trace.error(err_msg)
            raise CmwMcoApiException(err_msg)
        if set(results.keys()) != set(nodes):
            err_msg = self._gen_err_str(agent, mco_action, nodes, args)
            err_msg += "Response only received from the following nodes: "
            err_msg += ",".join(results.keys())
            log.trace.error(err_msg)
            raise CmwMcoApiException(err_msg)
        any_errors = False
        err_msg = self._gen_err_str(agent, mco_action, nodes, args)
        for node, result in results.iteritems():
            if result["errors"]:
                any_errors = True
                reason_str = (" node \"{0}\" reason: \"{1}\"")
                err_msg += reason_str.format(node, result["errors"])
        if any_errors:
            log.trace.error(err_msg)
            raise CmwMcoApiException(err_msg)
        if n is None:
            return results[self.node]["data"]
        else:
            return results

    def give_x_permission(self, path, file_name):
        mco_action = "give_file_execute_permission"
        args = {"path": path,
                "filename": file_name}
        result = self._call_mco("cmw_utils", mco_action, args)
        if not result["retcode"] == 0:
            err_str = ("Could not give file {0} on node {1} execute "
                       "permission".format(file_name, self.node))
            self._raise_error(err_str, result)

    def lde_config(self):
        mco_action = "lde_config"
        args = {}
        self._call_mco("cmw_utils", mco_action, args, timeout=600)

    def execute_script(self, path, file_name):
        mco_action = "execute_script"
        args = {"path": path,
                "script_name": file_name}
        result = self._call_mco("cmw_utils", mco_action, args, timeout=600)
        if result["retcode"] != 0:
            err_str = "problem executing script"
            self._raise_error(err_str, result)

    def check_file_exists(self, path, file_name):
        mco_action = "check_file_exists"
        file_exists = False
        args = {"path": path,
                "filename": file_name}
        result = self._call_mco("cmw_utils", mco_action, args)
        if result["retcode"] == 0:
            file_exists = True
        return file_exists

    def create_directory(self, path):
        mco_action = "create_directory"
        args = {"path": path}
        result = self._call_mco("cmw_utils", mco_action, args)
        if result["retcode"] != 0:
            err_str = ("could not create directory {0} on node {1}"
                       .format(path, self.node))
            self._raise_error(err_str, result)

    def delete_file(self, path, filename):
        mco_action = "delete_file"
        args = {"path": path,
                "filename": filename}
        result = self._call_mco("cmw_utils", mco_action, args)
        if result["retcode"] != 0:
            err_str = "Failed to to extract CMW installation files"
            self._raise_error(err_str, result)

    def unpack_tarfile(self, dest_path, filepath, filename):
        mco_action = "unpack_tarfile"
        args = {"path": filepath,
                "destpath": dest_path,
                "filename": filename}
        result = self._call_mco("cmw_utils", mco_action, args)
        if result["retcode"] != 0:
            err_str = "Failed to to extract CMW installation files"
            self._raise_error(err_str, result)

    def reboot_machine(self, nodes):
        result = self._call_mco("cmw_utils", "reboot_machine", None, n=nodes)
        _ = result

    def transfer_sdp(self, dest_node, dest_path, filepath, filename, ms_ip):
        self.node = dest_node
        fromfile = filepath + "/" + filename
        tmp_loc = tempfile.mkdtemp(prefix="vcstmp", dir=WWW_ROOT)
        os.chmod(tmp_loc, FILE_MODE)
        shutil.copy2(fromfile, tmp_loc)
        relative_path = tmp_loc[len(WWW_ROOT):]

        mco_action = "transfer_sdp_files"
        args = {"relative_path": relative_path,
                "dest_path": dest_path,
                "filename_list": filename,
                "md5_checksum_list": "md5",
                "ms_ip_addr": ms_ip}
        result = self._call_mco("cmw_campaign", mco_action, args)
        if result["retcode"] != 0:
            err_str = "Failed to copy lde check script to %s" % self.node
            self._raise_error(err_str, result)

#        shutil.rmtree(tmp_loc)

        return result["md5sum"]

    def import_sdp(self, filename, destpath="/tmp"):
        mco_action = "import_sdp_files"
        args = {"dest_path": destpath,
                "sdp_list": filename}
        result = self._call_mco("cmw_campaign", mco_action, args)
        if not result["retcode"] == SUCCESS:
            err_str = ("import_sdp: Failed to import {0} on node {1}"
                       .format(filename, self.node))
            self._raise_error(err_str, result)

    def get_campaign_status(self, campaign):
        mco_action = "get_status"
        args = {"campaign_name": campaign}
        result = self._call_mco("cmw_campaign", mco_action, args)
        if not result["retcode"] == SUCCESS:
            err_str = ("Problem getting campaign status for campaign {0}"
                       .format(campaign))
            self._raise_error(err_str, result)

#       expect a result of the form <campaign_name>=<state>
        result_prefix = campaign + "="
        if not result["out"].startswith(result_prefix):
            err_str = ("get_campaign_status: failed to get valid result for "
                        "get_status on node {0}. Expected \"{1}=<state>\""
                        " Received \"{2}\" "
                        .format(self.node, campaign, result["out"]))
            raise CmwMcoApiException(err_str)
        status = result["out"][len(result_prefix):]
        if not status in valid_campaign_status:
            err_str = ("Unrecognised campaign status: {0} for campaign {1} "
                       "on node {2}".format(status, campaign, self.node))
            raise CmwMcoApiException(err_str)
        return status

    def start_campaign(self, campaign):
        mco_action = "start_campaign"
        args = {"campaign_name": campaign}
        result = self._call_mco("cmw_campaign", mco_action, args)
        if not result["retcode"] == 0:
            err_str = ("Problem starting campaign {0} on node {1}"
                       .format(campaign, self.node))
            self._raise_error(err_str, result)

    def commit_campaign(self, campaign):
        mco_action = "commit_campaign"
        args = {"campaign_name": campaign}
        result = self._call_mco("cmw_campaign", mco_action, args)
        if not result["retcode"] == 0:
            err_str = ("Problem committing campaign {0} on node {1}"
                       .format(campaign, self.node))
            self._raise_error(err_str, result)

    def persist_configuration(self):
        mco_action = "persist_configuration"
        result = self._call_mco("cmw_campaign", mco_action)
        if not result["retcode"] == 0:
            err_str = ("Problem running cmw-configuration-persist"
                        "on node %s".format(self.node))
            self._raise_error(err_str, result)

    def remove_campaign(self, campaign):
        mco_action = "remove_campaign"
        args = {"campaign_name": campaign}
        result = self._call_mco("cmw_campaign", mco_action, args)
        if not result["retcode"] == 0:
            err_str = ("Problem removing campaign {0} on node {1}"
                       .format(campaign, self.node))
            self._raise_error(err_str, result)
