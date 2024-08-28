##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

"""
Module contains CMWInstaller class which is used by CMWPlugin to validate
model for CMW installation on cluster nodes and create configuration for it
"""


from litp.core.execution_manager import (ConfigTask,
                                         CallbackExecutionException)
from litp.core.litp_logging import LitpLogger
from litp.core.validators import ValidationError
#from litp.core.mco_commands import run_mco_command
from cmwplugin.execution import patch_callback
from cmwplugin.utils import (patch_helper_callback,
                             valid_cluster_nodes)
from cmwplugin.cmw_mco_api import CmwMcoApi
import time
import socket
import os
log = LitpLogger()

REBOOT_WAIT_TIME = 60


@patch_helper_callback
class CmwInstaller(object):
    """
    Class validates and creates configuration for any CMW cluster in initial
    state. The configuration generated creates cmw cluster
    """

    cmw_install_files = "/var/www/html/cba/pkgs/cmw/latest/%s"
    cmw_source_files = "/opt/ericsson/nms/litp/etc/puppet/modules/cmw/files"
    check_cmw_setup_file = "/root/CMW/install.sh"
    check_cmw_installed = "/opt/coremw/bin/cmw-status"
    _max_waiting_time_for_node = 1800
    _chkcfg_script = "cmw_chkconfig"
    _lde_check_script = "cmw_check"
    _runtime_tar = "COREMW_RUNTIME.tar"

    def __init__(self):
        super(CmwInstaller, self).__init__()

    def validate_model(self, plugin_api_context):  # pylint: disable=W0613
        """
        Validates that the system is ready to install CMW
        by checking the model.  Cannot check whether the actual nodes
        are ready, because that work may be being done as an earlier
        phase in this plan.

        There being no work to do is not an error.
        """
        errors = []
        return errors

    def create_configuration(self, plugin_api_context, plugin, cluster):
        """
        Creates configuration in form of ConfigTask for all nodes in any
        CMW cluster that is in initial state
        Returns a list of ConfigTasks/CallbackTasks
        Will do same checks as validate_model and throw RuntimeErrors for all
        failures
        """

        tasks = []

        ms_server = plugin_api_context.query('ms')[0]
        ms_ip_addr = self._get_ms_ip_for_network(cluster.internal_network,
                                                 ms_server)

        if cluster.item_type_id == 'cmw-cluster' and cluster.is_initial():
            nodes = valid_cluster_nodes(cluster)
            hostnames = [node.hostname for node in nodes]

            primary_node = self._find_primary_node(cluster)
            if primary_node is None:
                raise RuntimeError("No node with specified with id 1")
            tasks.append(
                self.create_callback_task(
                    plugin,
                    cluster.software,
                    'Reboot nodes in cluster "{0}" to finalise LDE '
                    'install'.format(cluster.item_id),
                    self._reboot_nodes,
                    nodes=hostnames,
                )
            )
            tasks.append(
                self.create_callback_task(
                    plugin,
                    cluster.software,
                    'Check LDE is correctly installed in cluster "{0}"'.format(
                        cluster.item_id),
                    self._check_lde,
                    node=primary_node.hostname,
                    ms_ip=ms_ip_addr
                )
            )
            tasks.append(
                self.create_callback_task(
                    plugin,
                    cluster.software,
                    'Setup CMW install enivironment for cluster "{0}"'.format(
                        cluster.item_id),
                    self._set_up_install_environment,
                    node=primary_node.hostname,
                    ms_ip=ms_ip_addr
                )
            )
            tasks.append(
                self.create_callback_task(
                    plugin,
                    cluster.software,
                    'Install CMW on cluster "{0}"'.format(cluster.item_id),
                    self._install_CMW,
                    node=primary_node.hostname,
                )
            )
        return tasks

    def create_callback_task(self, *args, **kwargs):
        '''
        Function is overridden by  @patch_helper_callback to
        provide implementation
        '''
        pass

    @staticmethod
    @patch_callback
    def _check_lde(callback_api, node, ms_ip):  # pylint: disable=W0613
        '''
        Checks if LDE is installed and valid
        Raises CallbackExecutionException if there is a failure
        '''
        log.event.info("lde check on %s" % node)
        log.event.info("Copying check script to %s" % node)

        cmw_mco_cmd = CmwMcoApi()
        cmw_mco_cmd.transfer_sdp(node,
                                 "/root",
                                 CmwInstaller.cmw_source_files,
                                 CmwInstaller._lde_check_script,
                                 ms_ip)

        cmw_mco_cmd.give_x_permission("/root",
                                      CmwInstaller._lde_check_script)

        log.event.info("Running lde check on %s" % node)
        cmw_mco_cmd.execute_script("/root",
                                   CmwInstaller._lde_check_script)

    @staticmethod
    @patch_callback
    # pylint: disable=W0613
    def _set_up_install_environment(callback_api, node, ms_ip):
        '''
        Setups up install environment for CMW
        Raises CallbackExecutionException if there is a failure
        '''
        # First check that this hasn't already been done
        log.event.info("Check if installtion files exist on %s" % node)
        cmw_mco_cmd = CmwMcoApi()
        cmw_mco_cmd.set_node(node)
        filepath, filename = os.path.split(CmwInstaller.check_cmw_setup_file)
        file_exists = cmw_mco_cmd.check_file_exists(filepath,
                                                    filename)
        if file_exists:
            log.event.info("CMW install environment already present")
            return

        # Not already done
        log.event.info("Setting up CMW install environment")
        cmw_mco_cmd.create_directory("/root/CMW")

        cmw_runtime_tar = (CmwInstaller.cmw_install_files
                           % CmwInstaller._runtime_tar)
        if not os.path.exists(cmw_runtime_tar):
            CmwInstaller._raise_error("%s is not available" % cmw_runtime_tar)

        log.event.info("Copying CMW install files to %s" % node)
        filepath, filename = os.path.split(cmw_runtime_tar)
        cmw_mco_cmd.transfer_sdp(node,
                                 "/root",
                                 filepath,
                                 filename,
                                 ms_ip)

        log.event.info("Extracting CMW install files on %s" % node)

        cmw_mco_cmd.unpack_tarfile("/root/CMW",
                                   "/root",
                                   CmwInstaller._runtime_tar)

        log.event.info("Copying CMW chkconfig modification script")
        cmw_mco_cmd.transfer_sdp(node,
                                 "/root",
                                 CmwInstaller.cmw_source_files,
                                 CmwInstaller._chkcfg_script,
                                 ms_ip)
        cmw_mco_cmd.give_x_permission("/root",
                                      CmwInstaller._chkcfg_script)

    @staticmethod
    def _wait_for_callback(callback_api, callback, *args, **kwargs):
        '''
        Waits for node to reboot
        Raises CallbackExecutionException if there is a failure
        '''
        start_time = int(time.time())
        diff_step = 0
        while not callback(*args, **kwargs):
            if not callback_api.is_running():
                return
            diff_time = int(time.time()) - start_time
            if diff_time > CmwInstaller._max_waiting_time_for_node:
                raise CallbackExecutionException(
                    "Node has not come up within {0} seconds".format(
                        CmwInstaller._max_waiting_time_for_node)
                )
            if diff_time / 60 != diff_step:
                diff_step += 1
                log.trace.info("Waiting for boot. {0} seconds elapsed".format(
                    diff_time))

            time.sleep(1.0)

    @staticmethod
    @patch_callback
    def _reboot_nodes(callback_api, nodes):
        '''
        Reboots nodes using remote "shutdown -r now" command
        '''
        cmw_mco_cmd = CmwMcoApi()
#        for node in nodes:
#            callback_api.execute(node, "shutdown -r now")
        cmw_mco_cmd.reboot_machine(nodes)

        for node in nodes:
            CmwInstaller._wait_for_callback(callback_api,
                                            CmwInstaller._check_node,
                                            node)
            time.sleep(REBOOT_WAIT_TIME)

    @staticmethod
    def _check_node(node_ip):
        '''
        Checks if node is alive by using simple TCP connection to port 22.
        Timeouts after 2 seconds
        '''
        ssh_port = 22
        timeout = 2  # seconds
        try:
            sock = None
            sock = socket.create_connection(
                (node_ip, ssh_port),
                timeout)
            result = (sock is not None)
            if result:
                sock.close()
            return result
        except socket.error:
            if sock:
                sock.close()
                return False

    @staticmethod
    @patch_callback
    def _install_CMW(callback_api, node):  # pylint: disable=W0613
        '''
        Executes CMW installation using remote calls
        Raises CallbackExecutionException if there is a failure
        '''

        # First check that this hasn't already been done
        log.event.info("Checking if CMW is alreading installed")
        cmw_mco_cmd = CmwMcoApi()
        cmw_mco_cmd.set_node(node)
        filepath, filename = os.path.split(CmwInstaller.check_cmw_installed)
        cmw_mco_cmd.check_file_exists(filepath,
                                      filename)
#        args = {"path": "/root",
#                "filename": CmwInstaller.check_cmw_installed}

        # Not already done
        log.event.info("Running CMW install script")
        cmw_mco_cmd.execute_script("/root/CMW", "install.sh")

        log.event.info("Fixing CMW startup script ordering")
        cmw_mco_cmd.execute_script("/root",
                                   CmwInstaller._chkcfg_script)

    @staticmethod
    def _raise_error(message, code=None, details=None):
        msg = "%s" % message
        if code:
            msg = "%s, code %s" % (msg, code)
        if details:
            msg = "%s, message %s" % (msg, details)

        log.event.error(msg)
        raise CallbackExecutionException(msg)

    def _find_primary_node(self, cluster):
        for node in cluster.query("node"):
            if node.node_id == "1":
                return node
        return None

    @staticmethod
    def _get_ms_ip_for_network(network_name, ms):
        """
        Retrieves ip address of nfs server on a particular network
        """
        for iface in ms.network_interfaces:
            if iface.network_name == network_name:
                return iface.ipaddress


def find_initial_cmw_clusters(api_context):
    """
    Function finds all model items of cmw-cluster type that are in 'initial'
    state
    """
    clusters = api_context.query("cmw-cluster")
    clusters = [cluster for cluster in clusters if cluster.is_initial()]
    return clusters


def create_ocf_resource_agents_install_tasks(context_api):
    """Creates tasks installing OCF resource agents on nodes"""
    tasks = []
    clusters = find_initial_cmw_clusters(context_api)

    if clusters:
        tasks = [ConfigTask(
            node,
            node,
            "Install OCF resource-agents on nodes",
            "cmw::resource_agents",
            "resource-agents"
        ) for cluster in clusters for node in valid_cluster_nodes(cluster)]

    return tasks


def create_ssh_config_tasks(context_api):
    """Creates SSH configuration; returns a list of ConfigTasks"""

    tasks = []
    clusters = find_initial_cmw_clusters(context_api)

    if clusters:
        tasks += [ConfigTask(ms, ms,
                             "Configure SSH keymaster on MS",
                             "ssh::rootconfig",
                             "ssh-rootconfig",
                             master="true",
                             server="false",
                             client="false")
                  for ms in context_api.query("ms")]

        tasks += [ConfigTask(node, node,
                             "Configure SSH keys on nodes",
                             "ssh::rootconfig",
                             "ssh-rootconfig",
                             server="true",
                             client="true")
                  for cluster in clusters
                  for node in valid_cluster_nodes(cluster)]

    return tasks


def create_amf_cgs_install_tasks(context_api):
    """Returns a list of config tasks"""

    if find_initial_cmw_clusters(context_api):
        return [ConfigTask(ms, ms,
                           "Install AMF-CGS on MS",
                           "cba::cgs_install",
                           "cgs-install",
                           )
                for ms in context_api.query("ms")]
    return []


def validate_model_for_amf_cgs_install_tasks(context_api):
    """Returns a listo of validation errors"""
    errors = []
    if find_initial_cmw_clusters(context_api):
        ms_list = context_api.query("ms")
        for ms in ms_list:
            pkgs = [pkg.name for pkg in ms.query("package")
                    if pkg.name in ["jdk", "jre", "java-1.6.0-openjdk",
                                    "java-1.7.0-openjdk"]]
            if not pkgs:
                errors.append(ValidationError(
                    item_path=ms.get_vpath(),
                    error_message="Java not available for AMF-CGS, "
                    "please define a package item for it"))
    return errors
