##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################


import unittest
import mock
from itertools import chain, cycle

cb_task = mock.patch('cmwplugin.utils.CallbackTask')
validation_error = mock.patch('cmwplugin.cmwinstaller.ValidationError')
from litp.core.execution_manager import CallbackExecutionException
from cmwplugin.cmwinstaller import (CmwInstaller,
                                    create_ssh_config_tasks,
                                    create_amf_cgs_install_tasks)

cb_task.start()
#validation_error.start()


class TestCmwInstallerSingleCluster(unittest.TestCase):
    def setUp(self):
        self.plugin = mock.Mock()
        self.plugin.__callback__ = mock.Mock()
        self.cluster = mock.Mock()
        self.net_if = mock.Mock(ipaddress="10.10.10.100")
        self.ms = mock.Mock()
        self.ms.network_interfaces = [self.net_if]
        self.cluster.nodes = self._create_nodes([1, 2])
        self.cluster.is_initial.return_value = True
        self.cluster.item_type_id = 'cmw-cluster'

        def api_query(*args, **kwargs):
            if args[0] == "ms":
                return [self.ms]
            else:
                return []
        self.plugin_api_context = mock.Mock()
        self.plugin_api_context.query.side_effect = api_query

        def cluster_query(*args, **kwargs):
            if args[0] == "node":
                return self.cluster.nodes
            else:
                return []

        self.cluster.query.side_effect = cluster_query

        def query(*args, **kwargs):
            if args[0] == "cmw-cluster":
                return [self.cluster]
            else:
                return []

        self.helper = CmwInstaller()
        self.callback_task = mock.Mock(
            'litp.core.execution_manager.CallbackTask')

    def test_validate_model_does_nothing(self):
        self.assertEquals(self.helper.validate_model(True), [])

    def test_create_configuration_single_node(self):
        self.cluster.nodes = self._create_nodes([1])
        result = self.helper.create_configuration(self.plugin_api_context,
                                                  self.plugin,
                                                  self.cluster)
        self.assertEqual(4, len(result))
        #self.assertEqual(1, len(result))

    def test_create_configuration_two_nodes(self):
        self.cluster.nodes = self._create_nodes([1])
        result = self.helper.create_configuration(self.plugin_api_context,
                                                  self.plugin,
                                                  self.cluster)
        #self.assertEqual(1, len(result))
        self.assertEqual(4, len(result))

    def test_create_configuration_raises_error_missing_nodes_ids_1_and_2(self):
        # no 1 nor 2
        self.cluster.nodes = self._create_nodes([3, 7])
        self.assertRaises(RuntimeError,
                          self.helper.create_configuration,
                          self.plugin_api_context, self.plugin, self.cluster)

    def test_create_configuration_raises_error_missing_node_id_1(self):
        self.cluster.nodes = self._create_nodes([2, 7])

        self.assertRaises(RuntimeError,
                          self.helper.create_configuration,
                          self.plugin_api_context, self.plugin, self.cluster)

    def test_create_configuration_raises_error_no_nodes_defined(self):
        self.cluster.nodes = []
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin_api_context, self.plugin, self.cluster)

    def test_create_configuration_for_cluster_with_non_cmw_cluster(self):
        self.cluster.item_type_id = 'non-cmw-cluster'
        result = self.helper.create_configuration(self.plugin_api_context,
                                                  self.plugin,
                                                  self.cluster)
        self.assertEqual(0, len(result))

    def _create_nodes(self, node_ids):
        mocks = []
        for node_id in node_ids:
            mocks.append(self._create_node(node_id))
        return mocks

    def _create_node(self, node_id):
        return mock.Mock(node_id=str(node_id),
                         hostname="mn%d" % node_id)


def side_effect(*args, **kwargs):
    result = dict()
    result["retcode"] = 0
    d = dict()
    d["mn1"] = result
    return d

def make_cmd_api():
    api = mock.Mock()
    api.transfer_sdp = mock.Mock()
    api.give_x_permission = mock.Mock()
    api.check_file_exists = mock.Mock()
    api.check_file_exists.return_value = False
    api.execute_script = mock.Mock()
    api.create_directory = mock.Mock()
    api.unpack_tarfile = mock.Mock()
    return api

class TestCmwInstallerCallbacksSingleCluster(unittest.TestCase):

    def setUp(self):
        self.api_context = mock.Mock(
            'litp.core.callback_api.CallbackApi', autospec=True)()
        self.api_context.mco_command = mock.Mock(side_effect=side_effect)
        self.api_context.execute = mock.Mock(return_value=(0, "", ""))
        self.api_context.copy = mock.Mock(return_value=(0, "", ""))
        self.helper = CmwInstaller()

#    @mock.patch('cmwplugin.cmwinstaller.CmwInstaller')
#    def test_install(self, Installer):
#        Installer._check_lde = mock.Mock()
#        Installer._set_up_install_environment = mock.Mock()
#        Installer._install_CMW = mock.Mock()
#        CmwInstaller._install(self.api_context, "mn1", ["mn1"])
#        self.assertEquals(Installer._check_lde.call_count, 1)
#        self.assertEquals(Installer._set_up_install_environment.call_count,
#                          1)
#        self.assertEquals(Installer._install_CMW.call_count, 1)
    @mock.patch('cmwplugin.cmwinstaller.socket')
    def test_check_node(self, mock_socket):
        mock_socket.create_connection.return_value = None
        self.assertEquals(False, self.helper._check_node('10.10.10.1'))
        mock_socket.create_connection.return_value = mock.Mock()
        self.assertEquals(True, self.helper._check_node('10.10.10.1'))

    def test_raise_error(self):
        try:
            self.helper._raise_error('foo')
            assert False
        except CallbackExecutionException as err:
            self.assertEquals(
                'foo',
                err.message)

        try:
            self.helper._raise_error('foo', code='bar')
            assert False
        except CallbackExecutionException as err:
            self.assertEquals(
                'foo, code bar',
                err.message)

        try:
            self.helper._raise_error('foo', details='bar')
            assert False
        except CallbackExecutionException as err:
            self.assertEquals(
                'foo, message bar',
                err.message)

        try:
            self.helper._raise_error('foo', code='bar', details='baz')
            assert False
        except CallbackExecutionException as err:
            self.assertEquals(
                'foo, code bar, message baz',
                err.message)

    @mock.patch('cmwplugin.cmwinstaller.CmwMcoApi')
    def test_install_CMW(self, cmw_mco_api):
        api_list = [make_cmd_api()]
        cmw_mco_api.side_effect = api_list
        CmwInstaller._install_CMW(self.api_context, "mn1")
        api_list[0].check_file_exists.\
            assert_called_once_with('/opt/coremw/bin',
                                    'cmw-status')
        expected_calls = [mock.call('/root/CMW', 'install.sh'),
                          mock.call('/root', 'cmw_chkconfig')]
        self.assertTrue(api_list[0].execute_script.call_args_list ==
                        expected_calls)

#    def test_install_CMW_already_installed(self):
#        self.api_context.mco_command.side_effect = [{"mn1": {"retcode": 0}}]
#        CmwInstaller._install_CMW(self.api_context, "mn1")
#        self.assertEquals(self.api_context.mco_command.call_count, 1)

#    def est_install_CMW_raises_error_on_install_script_failure(self):
#        self.assertRaises(
#            CallbackExecutionException,
#            CmwInstaller._install_CMW,
#            self.api_context, "mn1")
#        self.assertEquals(self.api_context.mco_command.call_count, 2)

#    def est_install_CMW_raises_error_on_update_startup_scripts_failure(self):
#        self.api_context.mco_command.side_effect = [{"mn1": {"retcode": 1}},
#                                                    {"mn1": {"retcode": 0}},
#                                                    {"mn1": {"retcode": 1}}
#                                                    ]
#        self.assertRaises(
#            CallbackExecutionException,
#            CmwInstaller._install_CMW,
#            self.api_context, ["mn1"])
#        self.assertEquals(self.api_context.mco_command.call_count, 3)

    @mock.patch('cmwplugin.cmwinstaller.CmwMcoApi')
    def test_check_lde(self, cmw_mco_api):
        api_list = [make_cmd_api()]
        cmw_mco_api.side_effect = api_list
        CmwInstaller._check_lde(self.api_context, "mn1", "10.10.10.100")
        api_list[0].transfer_sdp.assert_called_once_with('mn1',
                                                         '/root',
                                                         '/opt/ericsson/nms/litp/etc/puppet/modules/cmw/files',
                                                         'cmw_check',
                                                         "10.10.10.100")
        api_list[0].give_x_permission.assert_called_once_with('/root',
                                                              'cmw_check')
        api_list[0].execute_script.assert_called_once_with('/root',
                                                           'cmw_check')

#    def est_lde_check_successful_copy_raises_error_on_check_script(self):
#        self.api_context.mco_command.side_effect = [{"mn1": {"retcode": 0}},
#                                                    {"mn1": {"retcode": 0}},
#                                                    {"mn1": {"retcode": 1, "err": "PROBLEM"}}]
#        self.assertRaises(CallbackExecutionException,
#                          self.helper._check_lde,
#                          self.api_context,
#                          "mn1")
#        self.assertEquals(self.api_context.mco_command.call_count, 3)
##        self.assertEquals(self.api_context.execute.call_count, 2)
##        self.assertEquals(self.api_context.copy.call_count, 1)

    @mock.patch("os.path.exists")
    @mock.patch('cmwplugin.cmwinstaller.CmwMcoApi')
    def test_set_up_install_environment_success(self, cmw_mco_api, mock_os_path):
        api_list = [make_cmd_api()]
        cmw_mco_api.side_effect = api_list
        CmwInstaller._set_up_install_environment(self.api_context,
                                                 "mn1", "10.10.10.100")
        api_list[0].check_file_exists.assert_called_once_with('/root/CMW',
                                                              'install.sh')
        api_list[0].create_directory.assert_called_once_with('/root/CMW')
        api_list[0].unpack_tarfile.assert_called_once_with('/root/CMW',
                                                           '/root',
                                                           'COREMW_RUNTIME.tar')
        api_list[0].give_x_permission.assert_called_once_with('/root',
                                                              'cmw_chkconfig')
        expected_calls = [mock.call('mn1',
                                    '/root',
                                    '/var/www/html/cba/pkgs/cmw/latest',
                                    'COREMW_RUNTIME.tar',
                                    '10.10.10.100'),
                          mock.call('mn1',
                                    '/root',
                                    '/opt/ericsson/nms/litp/etc/puppet/modules/cmw/files',
                                    'cmw_chkconfig',
                                    '10.10.10.100')]
        print api_list[0].transfer_sdp.call_args_list
        self.assertTrue(api_list[0].transfer_sdp.call_args_list ==
                        expected_calls)

    @mock.patch('cmwplugin.cmwinstaller.CmwMcoApi')
    def test_set_up_install_environment_files_exist(self, cmw_mco_api):
        api_list = [make_cmd_api()]
        cmw_mco_api.side_effect = api_list
        api_list[0].check_file_exists.return_value = True
        CmwInstaller._set_up_install_environment(self.api_context,
                                                 "mn1", "10.10.10.100")
        self.assertTrue(api_list[0].check_file_exists.call_count, 1)
        self.assertTrue(api_list[0].create_directory.call_count == 0)


class TestCreateSSHConfigTasks(unittest.TestCase):
    """Tests creation of SSH configuration tasks"""
    def setUp(self):
        self.context_api = mock.Mock(
            'litp.core.plugin_context_api.PluginApiContext', autospec=True)()

    @mock.patch('cmwplugin.cmwinstaller.ConfigTask')
    @mock.patch('cmwplugin.cmwinstaller.find_initial_cmw_clusters')
    def test_no_initial_cmw_clusters_create_no_tasks(self, find_fn,
                                                     config_task):
        find_fn.return_value = []
        result = create_ssh_config_tasks(self.context_api)
        self.assertEquals(0, len(result))
        self.assertEquals(0, self.context_api.query.call_count)
        self.assertEquals(0, config_task.query.call_count)

    @mock.patch('cmwplugin.cmwinstaller.ConfigTask')
    @mock.patch('cmwplugin.cmwinstaller.find_initial_cmw_clusters')
    def test_create_tasks_for_two_nodes_creates_required_tasks(self, find_fn,
                                                               config_task):
        cluster = mock.Mock()
        node1 = mock.Mock(is_for_removal=mock.Mock(return_value=False))
        node2 = mock.Mock(is_for_removal=mock.Mock(return_value=False))
        cluster.nodes = [node1, node2]
        ms = mock.Mock()

        find_fn.return_value = [cluster]
        self.context_api.query.return_value = [ms]

        result = create_ssh_config_tasks(self.context_api)
        self.assertEquals(3, len(result))
        self.context_api.query.assert_called_once_with('ms')
        self.assertEquals(config_task.mock_calls, [
            mock.call(ms, ms,
                      "Configure SSH keymaster on MS",
                      "ssh::rootconfig",
                      "ssh-rootconfig",
                      master="true",
                      server="false",
                      client="false"),
            mock.call(cluster.nodes[0], cluster.nodes[0],
                      "Configure SSH keys on nodes",
                      "ssh::rootconfig",
                      "ssh-rootconfig",
                      server="true",
                      client="true"),
            mock.call(cluster.nodes[1], cluster.nodes[1],
                      "Configure SSH keys on nodes",
                      "ssh::rootconfig",
                      "ssh-rootconfig",
                      server="true",
                      client="true")])


class TestCreateAMFCGSInstallTasks(unittest.TestCase):
    """Tests creation of AMF-CGS install configuration tasks"""
    def setUp(self):
        self.context_api = mock.Mock(
            'litp.core.plugin_context_api.PluginApiContext', autospec=True)()

    @mock.patch('cmwplugin.cmwinstaller.ConfigTask')
    @mock.patch('cmwplugin.cmwinstaller.find_initial_cmw_clusters')
    def test_no_initial_cmw_clusters_create_no_tasks(self, find_fn,
                                                     config_task):
        find_fn.return_value = False
        result = create_ssh_config_tasks(self.context_api)
        self.assertEquals(0, len(result))
        self.assertEquals(0, self.context_api.query.call_count)
        self.assertEquals(0, config_task.query.call_count)

    @mock.patch('cmwplugin.cmwinstaller.ConfigTask')
    @mock.patch('cmwplugin.cmwinstaller.find_initial_cmw_clusters')
    def test_create_tasks_for_two_nodes_creates_single_task(self, find_fn,
                                                            config_task):
        ms = mock.Mock()
        find_fn.return_value = True
        self.context_api.query.return_value = [ms]

        result = create_amf_cgs_install_tasks(self.context_api)
        self.assertEquals(1, len(result))
        self.context_api.query.assert_called_once_with('ms')
        config_task.assert_called_once_with(ms, ms,
                                            "Install AMF-CGS on MS",
                                            "cba::cgs_install",
                                            "cgs-install")

    @mock.patch('cmwplugin.cmwinstaller.find_initial_cmw_clusters')
    def test_empty_create_amf_cgs_install_tasks(self, mock_finder):
        mock_finder.return_value = False
        self.assertEquals([], create_amf_cgs_install_tasks(mock.Mock()))


