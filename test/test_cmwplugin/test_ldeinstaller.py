##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

# pylint:disable=missing-docstring,invalid-name
# pylint:disable=too-many-instance-attributes,too-many-public-methods

import unittest
import mock

from cmwplugin.ldeinstaller import LdeInstaller
from litp.core.extension import ViewError


class TestLdeInstaller(unittest.TestCase):
    """
    Base class for actual model validation and configuration creation tests
    Provides test doubles for the dependencies of LdeInstaller class
    """
    def setUp(self):
        self.plugin = mock.Mock()
        self.plugin.__callback__ = mock.Mock()

        self.api_context = mock.Mock(
            'litp.core.plugin_context_api.PluginApiContext', autospec=True)()

        self.nfs_ipaddress = "193.120.208.1"
        self.ms_hostname = "ms1"

        self.cluster = mock.Mock()
        self.cluster.cluster_id = "12345"
        self.cluster.quick_reboot = 'off'
        self.cluster.item_id = 'cluster1'
        self.cluster.item_type_id = 'cmw-cluster'
        self.cluster.is_initial.return_value = True

        self.node1 = mock.Mock(node_id="1", hostname="sc1", item_id="node1")
        self.node2 = mock.Mock(node_id="2", hostname="sc2", item_id="node2")
        self.node3 = mock.Mock(node_id="3", hostname="pl1", item_id="node3")

        self.node1.network_interfaces = [mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth0",
                                                network_name="mgmt",
                                                ipaddress="193.120.208.222",
                                                macaddress='11:11:11:11:11:11'
                                                   ),
                                         mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth2",
                                                network_name="hb1",
                                                macaddress='AA:AA:AA:AA:AA:AA'
                                                   ),
                                         mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth3",
                                                network_name="hb2",
                                                macaddress='BB:BB:BB:BB:BB:BB'
                                                   ),
                                         ]
        self.node2.network_interfaces = [mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth0",
                                                network_name="mgmt",
                                                ipaddress="193.120.208.223",
                                                macaddress='22:22:22:22:22:22'
                                                   ),
                                         mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth2",
                                                network_name="hb1",
                                                macaddress='CC:CC:CC:CC:CC:CC'
                                                   ),
                                         mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth3",
                                                network_name="hb2",
                                                macaddress='DD:DD:DD:DD:DD:DD'
                                                   ),
                                         ]
        # only used in some cases
        self.node3.network_interfaces = [mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth0",
                                                network_name="mgmt",
                                                ipaddress="193.120.208.224",
                                                macaddress='33:33:33:33:33:33'
                                                   ),
                                         mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth2",
                                                network_name="hb1",
                                                macaddress='EE:EE:EE:EE:EE:EE'
                                                   ),
                                         mock.Mock(
                                                item_type_id='eth',
                                                device_name="eth3",
                                                network_name="hb2",
                                                macaddress='FF:FF:FF:FF:FF:FF'
                                                   ),
                                         ]
        self.node1.file_systems=[mock.Mock(
                mount_point="/cluster",
                provider="storage_provider1"
                )]
        self.node2.file_systems=[mock.Mock(
                mount_point="/cluster",
                provider="storage_provider1"
                )]
        self.node3.file_systems=[mock.Mock(
                mount_point="/cluster",
                provider="storage_provider1"
                )]
        self.node1.is_for_removal=mock.Mock(return_value=False)
        self.node2.is_for_removal=mock.Mock(return_value=False)
        self.node3.is_for_removal=mock.Mock(return_value=False)

#==============================================================================
#         self.node1.network_profile.name = 'net_profile'
#         self.node1.network_profile.management_network = 'mgmt'
#         self.node1.network_interfaces = [
#             mock.Mock(view_subnet='193.120.208.221/32',
#                       network_name="mgmt",
#                       ipaddress="193.120.208.222",
#                       device_name='eth0',
#                       macaddress='11:11:11:11:11:11'),
#             mock.Mock(network_name="hb1",
#                       device_name='eth2',
#                       macaddress='AA:AA:AA:AA:AA:AA'),
#             mock.Mock(network_name="hb2",
#                       device_name='eth3',
#                       macaddress='BB:BB:BB:BB:BB:BB')
#         ]
#         self.node2.network_profile.name = 'net_profile'
#         self.node2.network_interfaces = [
#             mock.Mock(view_subnet='193.120.208.221/32',
#                       network_name="mgmt",
#                       ipaddress="193.120.208.223",
#                       device_name='eth0',
#                       macaddress='22:22:22:22:22:22'),
#             mock.Mock(network_name="hb1",
#                       device_name='eth2',
#                       macaddress='CC:CC:CC:CC:CC:CC'),
#             mock.Mock(network_name="hb2",
#                       device_name='eth3',
#                       macaddress='DD:DD:DD:DD:DD:DD')
#         ]
#
#         # only used in some cases
#         self.node3.network_profile.name = 'net_profile'
#         self.node3.network_interfaces = [
#             mock.Mock(view_subnet='193.120.208.221/32',
#                       network_name="mgmt",
#                       ipaddress="193.120.208.224",
#                       device_name='eth0',
#                       macaddress='33:33:33:33:33:33'),
#             mock.Mock(network_name="hb1",
#                       device_name='eth2',
#                       macaddress='EE:EE:EE:EE:EE:EE'),
#             mock.Mock(network_name="hb2",
#                       device_name='eth3',
#                       macaddress='FF:FF:FF:FF:FF:FF')
#         ]
#==============================================================================

        def cluster_query(*args, **kwargs):
            if args[0] == "node":
                return [self.node1, self.node2]
        self.cluster.query.side_effect = cluster_query

        class CollectionMock(list):
            def __init__(self, *args, **kwargs):
                super(CollectionMock, self).__init__(*args, **kwargs)
                self.get_vpath = None

        self.cluster.nodes = CollectionMock([self.node1, self.node2])
        self.cluster.nodes.get_vpath = mock.Mock()
        self.cluster.internal_network = "mgmt"
        #======================================================================
        # mock.MagicMock(network_name="mgmt",
        #                                            interface="if0")
        #======================================================================
        self.cluster.tipc_networks = "hb1,hb2"
        #======================================================================
        # [
        #     mock.MagicMock(interface='if2', network_name='hb1'),
        #     mock.MagicMock(interface='if3', network_name='hb2'),
        # ]
        #======================================================================
        #======================================================================
        # self.cluster.mgmt_network.__eq__.side_effect = \
        #     lambda x: x.network_name == 'mgmt'
        # self.cluster.heartbeat_networks.split(",")[0].__eq__.side_effect = \
        #     lambda x: x.network_name == 'hb1'
        # self.cluster.heartbeat_networks[1].__eq__.side_effect = \
        #     lambda x: x.network_name == 'hb2'
        #======================================================================

        # pylint complains about **kwargs
        # pylint: disable=unused-argument
        def query(*args, **kwargs):
            if args[0] == "cmw-cluster":
                return [self.cluster]
            elif args[0] == "network":
                return [mock.Mock(subnet="192.120.208.0/24")]
            elif args[0] == "ms":
                return [mock.Mock(hostname="ms1")]
            elif args[0] == "nfs-service":
                if (kwargs["name"] is not None and
                    kwargs["name"] == "storage_provider1"):
                    return [mock.Mock(ipv4address=self.nfs_ipaddress)]
        self.api_context.query.side_effect = query
        self.helper = LdeInstaller()


class TestLdeInstallerValidateModel(TestLdeInstaller):
    """
    Class tests validation of the model with regards to lde installation
    method tested: LdeInstaller.validate_model
    """

    # negatives

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_two_nodes_with_no_sc_node_ids(
            self, validation_error):
        self.node1.node_id = "3"
        self.node2.node_id = "7"
        result = self.helper.validate_model(self.cluster)

        self.assertEqual(validation_error.mock_calls[0], mock.call(
            item_path=self.cluster.get_vpath(),
            error_message=LdeInstaller.missing_node_ids_msg.format(
                self.cluster.item_id, "1, 2")))
        self.assertEqual(len(validation_error.mock_calls), len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_nodes_without_node_id(self, validation_error):
        self.node1.node_id = "1"
        self.node2.node_id = None
        result = self.helper.validate_model(self.cluster)
        self.assertEqual(validation_error.mock_calls, [
            mock.call(item_path=self.node2.get_vpath(),
                      error_message=LdeInstaller.unset_node_id_msg.format(
                          self.node2.item_id, self.cluster.item_id)),
            mock.call(item_path=self.cluster.get_vpath(),
                      error_message=LdeInstaller.missing_node_ids_msg.format(
                          self.cluster.item_id, "2"))
        ])
        self.assertEqual(2, len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_dont_treat_undef_node_ids_as_duplicates(
            self, validation_error):
        self.node1.node_id = "1"
        self.node2.node_id = None
        self.node3.node_id = None
        self.cluster.nodes.append(self.node3)
        result = self.helper.validate_model(self.cluster)
        self.assertEqual(validation_error.mock_calls, [
            mock.call(item_path=self.node2.get_vpath(),
                      error_message=LdeInstaller.unset_node_id_msg.format(
                          self.node2.item_id, self.cluster.item_id)),
            mock.call(item_path=self.node3.get_vpath(),
                      error_message=LdeInstaller.unset_node_id_msg.format(
                          self.node3.item_id, self.cluster.item_id)),
            mock.call(item_path=self.cluster.get_vpath(),
                      error_message=LdeInstaller.missing_node_ids_msg.format(
                          self.cluster.item_id, "2"))
        ])
        self.assertEqual(validation_error.call_count, len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_treat_detects_invalid_node_ids(
            self, validation_error):

        # LITPCDS-2933
        self.cluster.nodes.append(self.node3)
        self.node1.node_id = "1"
        self.node2.node_id = "2"
        self.node3.node_id = "a"
        result = self.helper.validate_model(self.cluster)
        self.assertEqual(validation_error.call_count, len(result))

        self.node3.node_id = "3.1"
        self.helper.validate_model(self.cluster)
        self.node3.node_id = "3a"
        self.helper.validate_model(self.cluster)
        self.node3.node_id = "0"
        self.helper.validate_model(self.cluster)
        self.node3.node_id = "3 a"
        self.helper.validate_model(self.cluster)
        self.node3.node_id = "2048"
        self.helper.validate_model(self.cluster)
        self.assertEqual(validation_error.mock_calls, [
            mock.call(item_path=self.node3.get_vpath(),
                      error_message=LdeInstaller.invalid_node_id_msg.format(
                          "'a'", self.node3.item_id, self.cluster.item_id,
                          LdeInstaller.cluster_max_nodes)),
            mock.call(item_path=self.node3.get_vpath(),
                      error_message=LdeInstaller.invalid_node_id_msg.format(
                          "'3.1'", self.node3.item_id, self.cluster.item_id,
                          LdeInstaller.cluster_max_nodes)),
            mock.call(item_path=self.node3.get_vpath(),
                      error_message=LdeInstaller.invalid_node_id_msg.format(
                          "'3a'", self.node3.item_id, self.cluster.item_id,
                          LdeInstaller.cluster_max_nodes)),
            mock.call(item_path=self.node3.get_vpath(),
                      error_message=LdeInstaller.invalid_node_id_msg.format(
                          "'0'", self.node3.item_id, self.cluster.item_id,
                          LdeInstaller.cluster_max_nodes)),
            mock.call(item_path=self.node3.get_vpath(),
                      error_message=LdeInstaller.invalid_node_id_msg.format(
                          "'3 a'", self.node3.item_id, self.cluster.item_id,
                          LdeInstaller.cluster_max_nodes)),
            mock.call(item_path=self.node3.get_vpath(),
                      error_message=LdeInstaller.invalid_node_id_msg.format(
                          "'2048'", self.node3.item_id, self.cluster.item_id,
                          LdeInstaller.cluster_max_nodes)),
        ])

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_two_nodes_with_no_primary_sc_node_id(
            self, validation_error):
        self.node1.node_id = "2"
        self.node2.node_id = "7"
        result = self.helper.validate_model(self.cluster)

        self.assertEqual(validation_error.mock_calls[0], mock.call(
            item_path=self.cluster.get_vpath(),
            error_message=LdeInstaller.missing_node_ids_msg.format(
                self.cluster.item_id, "1")))
        self.assertEqual(len(validation_error.mock_calls), len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_nodes_with_duplicate_sc_node_id(
            self, validation_error):
        self.node3.node_id = "2"  # same as node2
        self.cluster.nodes.append(self.node3)
        result = self.helper.validate_model(self.cluster)
        validation_error.assert_called_once_with(
            item_path=self.cluster.get_vpath(),
            error_message=LdeInstaller.duplicate_node_ids_msg.format('2'))
        self.assertEqual(len(validation_error.mock_calls), len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_no_primary_sc_node_id_and_duplicate_node_id(
            self, validation_error):
        self.node1.node_id = "2"
        self.node2.node_id = "2"
        result = self.helper.validate_model(self.cluster)

        self.assertEqual(validation_error.mock_calls[0], mock.call(
            item_path=self.cluster.get_vpath(),
            error_message=LdeInstaller.missing_node_ids_msg.format(
                self.cluster.item_id, "1")))
        self.assertEqual(validation_error.mock_calls[1], mock.call(
            item_path=self.cluster.get_vpath(),
            error_message=LdeInstaller.duplicate_node_ids_msg.format('2')))
        self.assertEqual(len(validation_error.mock_calls), len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_two_nodes_with_no_secondary_sc_node_id(
            self, validation_error):
        self.node1.node_id = "1"
        self.node2.node_id = "7"
        result = self.helper.validate_model(self.cluster)

        self.assertEqual(validation_error.mock_calls[0], mock.call(
            item_path=self.cluster.get_vpath(),
            error_message=LdeInstaller.missing_node_ids_msg.format(
                self.cluster.item_id, "2")))
        self.assertEqual(len(validation_error.mock_calls), len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_cluster_too_few_nodes(self, validation_error):
        nodes_count = LdeInstaller.cluster_min_nodes - 1
        self.cluster.nodes.pop()
        result = self.helper.validate_model(self.cluster)
        validation_error.assert_called_once_with(
            item_path=self.cluster.nodes.get_vpath(),
            error_message=LdeInstaller.not_enough_nodes_msg.format(
                nodes_count, LdeInstaller.cluster_min_nodes))
        self.assertEqual(len(validation_error.mock_calls), len(result))

    # net profiles don't exist anymore
    #==========================================================================
    # @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    # def test_validation_detects_nodes_having_different_net_profiles(
    #         self, validation_error):
    #     self.node1.network_profile.name = 'different_net_profile'
    #     result = self.helper.validate_model(self.cluster)
    #     validation_error.assert_called_once_with(
    #         item_path=self.cluster.get_vpath(),
    #         error_message=LdeInstaller.separate_network_profiles_msg)
    #     self.assertEqual(1, len(result))
    #==========================================================================

    # this would be caught by the item validation
    #==========================================================================
    # @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    # def test_validation_detects_missing_mgmt_network(self, validation_error):
    #     self.cluster.mgmt_network = None
    #     result = self.helper.validate_model(self.cluster)
    #     msg = LdeInstaller.no_mgmt_network_msg.format(self.cluster.item_id)
    #     validation_error.assert_called_once_with(
    #         item_path=self.cluster.get_vpath(), error_message=msg)
    #     self.assertEqual(len(validation_error.mock_calls), len(result))
    #==========================================================================
    # net profiles don't exist anymore
    #==========================================================================
    # @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    # def test_validation_detects_disjoint_mgmt_network(self, validation_error):
    #     #self.cluster.mgmt_network.__eq__.side_effect = None
    #     #self.cluster.mgmt_network.__eq__.return_value = False
    #     result = self.helper.validate_model(self.cluster)
    #     msg1 = LdeInstaller.mgmt_net_not_in_net_profile_msg.format(
    #         self.node1.item_id, self.cluster.item_id)
    #     msg2 = LdeInstaller.mgmt_net_not_in_net_profile_msg.format(
    #         self.node2.item_id, self.cluster.item_id)
    #     self.assertEqual(validation_error.mock_calls,
    #                      [mock.call(item_path=self.node1.get_vpath(),
    #                                 error_message=msg1),
    #                       mock.call(item_path=self.node2.get_vpath(),
    #                                 error_message=msg2)])
    #     self.assertEqual(len(validation_error.mock_calls), len(result))
    #==========================================================================

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_incorrect_cluster_mount1(self,
                                                         validation_error):
        self.node1.file_systems[0].mount_point = '/wrong_mount'
        result = self.helper.validate_model(self.cluster)
        self.assertEqual(validation_error.mock_calls[0],
                         mock.call(item_path=self.node1.get_vpath(),
                                   error_message=\
                                       LdeInstaller.no_cluster_mounted))
        self.assertEqual(len(validation_error.mock_calls), len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_incorrect_cluster_mount2(self,
                                                         validation_error):
        self.node2.file_systems[0].provider = 'wrong_provider'
        result = self.helper.validate_model(self.cluster)
        self.assertEqual(validation_error.mock_calls[0],
                         mock.call(item_path=self.cluster.get_vpath(),
                                   error_message=\
                                       LdeInstaller.not_all_mounts_using_same_provider))
        self.assertEqual(len(validation_error.mock_calls), len(result))

# NO SUPPORT YET FOR CHECKING THIS
#==============================================================================
#     @mock.patch('cmwplugin.ldeinstaller.ValidationError')
#     def test_validation_detects_disjoint_hb_network(self, validation_error):
#         #self.cluster.heartbeat_networks.split(",")[0].__eq__.side_effect = None
#         #self.cluster.heartbeat_networks.split(",")[0].__eq__.return_value = False
#         #self.cluster.heartbeat_networks[1].__eq__.side_effect = None
#         #self.cluster.heartbeat_networks[1].__eq__.return_value = False
# 
#         self.node1.network_interfaces = \
#             self.node1.network_interfaces[0:1]
#         self.node2.network_interfaces = \
#             self.node2.network_interfaces[0:1]
#         result = self.helper.validate_model(self.cluster)
#         msg1 = LdeInstaller.hb_net_not_in_net_profile_msg.format(
#             self.cluster.heartbeat_networks.split(",")[0],
#             self.node1.item_id, self.cluster.item_id)
#         msg2 = LdeInstaller.hb_net_not_in_net_profile_msg.format(
#             self.cluster.heartbeat_networks[1],
#             self.node1.item_id, self.cluster.item_id)
#         msg3 = LdeInstaller.hb_net_not_in_net_profile_msg.format(
#             self.cluster.heartbeat_networks.split(",")[0],
#             self.node2.item_id, self.cluster.item_id)
#         msg4 = LdeInstaller.hb_net_not_in_net_profile_msg.format(
#             self.cluster.heartbeat_networks[1],
#             self.node2.item_id, self.cluster.item_id)
#         self.assertEqual(validation_error.mock_calls, [
#             mock.call(item_path=self.node1.get_vpath(),
#                       error_message=msg1),
#             mock.call(item_path=self.node1.get_vpath(),
#                       error_message=msg2),
#             mock.call(item_path=self.node2.get_vpath(),
#                       error_message=msg3),
#             mock.call(item_path=self.node2.get_vpath(),
#                       error_message=msg4)])
# 
#         self.assertEqual(len(validation_error.mock_calls), len(result))
#==============================================================================

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_missing_ip_in_mgmt_network(
            self, validation_error):
        self.node1.network_interfaces[0].ipaddress = None
        result = self.helper.validate_model(self.cluster)
        validation_error.assert_called_with(
            item_path=self.node1.get_vpath(),
            error_message=LdeInstaller.no_ip_on_mgmt_network_msg)
        self.assertEqual(len(validation_error.mock_calls), len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_heartbeat_prob_not_unique_mac(self,
                                                           validation_error):
        self.cluster.nodes[0].network_interfaces[1].macaddress = \
            self.cluster.nodes[0].network_interfaces[2].macaddress
        result = self.helper._detect_heartbeat_problems(self.cluster)
        print result
        validation_error.assert_called_once_with(
            item_path=self.cluster.get_vpath(),
            error_message=LdeInstaller.tipc_unique_mac_required.format(
                "cluster1"))
        self.assertEqual(len(validation_error.mock_calls), len(result))

    @mock.patch('cmwplugin.ldeinstaller.ValidationError')
    def test_validation_detects_heartbeat_prob_not_unique_mac(self,
                                                           validation_error):
        self.cluster.tipc_networks = "hb1,hb3"
        result = self.helper._detect_heartbeat_problems(self.cluster)
        print validation_error.mock_calls

        e1 = LdeInstaller.hb_net_not_in_net_profile_msg.format(
            "hb3", self.node1.item_id, self.cluster.item_id)
        e2 = LdeInstaller.hb_net_not_in_net_profile_msg.format(
            "hb3", self.node2.item_id, self.cluster.item_id)
        expected = [
            mock.call(item_path=self.node1.get_vpath(),
                      error_message=e1),
            mock.call(item_path=self.node2.get_vpath(),
                      error_message=e2)
            ]
        self.assertEqual(validation_error.mock_calls, expected)
        self.assertEqual(len(validation_error.mock_calls), len(result))

    # positives

    def test_validation_succeeds_for_cmw_cluster_in_non_initial_state(self):
        self.cluster.is_initial.return_value = False
        result = self.helper.validate_model(self.cluster)
        self.assertEqual(0, len(result))
        self.cluster.is_initial.assert_called_once_with()

    def test_validation_succeeds_for_non_cmw_ha_manager(self):
        cmw_mgr_search_result = []
        self.cluster.query.return_value = cmw_mgr_search_result
        result = self.helper.validate_model(self.cluster)
        self.assertEqual(0, len(result))

    def test_validation_succeeds_for_single_network_as_hbeat_and_mgmt(self):
        self.cluster.heartbeat_networks = self.cluster.mgmt_network
        self.assertEqual(0, len(self.helper.validate_model(self.cluster)))


class TestLdeInstallerCreateConfiguration(TestLdeInstaller):
    """
    Class tests creating config tasks with regards to lde installation
    method tested: LdeInstaller.create_configuration
    """

    # negative
    # exceptions: these should be detected by validation
    # and configuration never attempted to be created

    @mock.patch('cmwplugin.ldeinstaller.LdeInstaller._get_ms_subnet_ip')
    def test_create_conf_throws_view_error_for_nonexistent_view_property(self,
                                                        _get_ms_subnet_ip):
        _get_ms_subnet_ip.return_value = {"retcode": "10.10.10.100"}

        class NetworkMock(object):
            def __init__(self):
                self.network_name = "hb1"
                self.macaddress = 'AA:AA:AA:AA:AA:AA'
                super(NetworkMock, self).__init__()

            @property
            def device_name(self):
                raise ViewError('view error')

        self.node1.network_interfaces[1] = NetworkMock()
        self.assertRaises(ViewError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)

    @mock.patch('cmwplugin.ldeinstaller.LdeInstaller._get_ms_subnet_ip')
    def test_create_conf_throws_error_for_hbeat_with_missing_ifaces(self,
                                                    _get_ms_subnet_ip):
        #self.cluster.heartbeat_networks.split(",")[0].__eq__.side_effect = None
        #self.cluster.heartbeat_networks.split(",")[0].__eq__.return_value = False
        _get_ms_subnet_ip.return_value = {"retcode": "10.10.10.100"}
        self.node1.network_interfaces = \
            self.node1.network_interfaces[0:1]
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)

    def test_create_conf_throws_error_with_two_nodes_with_bad_node_ids(self):
        # no 1 nor 2
        self.cluster.nodes[0].node_id = "3"
        self.cluster.nodes[1].node_id = "7"
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        # no 1
        self.cluster.nodes[0].node_id = "2"
        self.cluster.nodes[1].node_id = "7"
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        # no 2
        self.cluster.nodes[0].node_id = "1"
        self.cluster.nodes[1].node_id = "7"
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        # undefined node_id
        self.cluster.nodes[0].node_id = "1"
        self.cluster.nodes[1].node_id = None
        self.cluster.nodes[1].item_id = 'node3'
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        # wrong type node_id
        self.cluster.nodes[0].node_id = "1"
        self.cluster.nodes[1].node_id = "2"

        self.cluster.nodes.append(self.node3)
        self.cluster.nodes[2].item_id = 'node3'

        self.cluster.nodes[2].node_id = 'a'
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        self.cluster.nodes[2].node_id = '3.1'
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        self.cluster.nodes[2].node_id = '3a'
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        self.cluster.nodes[2].node_id = '3 a'
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        # node_id out of range
        self.cluster.nodes[2].node_id = '2048'
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)
        self.cluster.nodes[2].node_id = '0'
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)

    def test_create_conf_throws_error_for_cluster_without_nodes(self):
        self.cluster.nodes = []
        self.assertRaises(RuntimeError, self.helper.create_configuration,
                          self.plugin, self.cluster, self.api_context)

    #==========================================================================
    # def test_create_conf_throws_error_with_nodes_having_different_net_profiles(
    #         self):
    #     self.node1.network_profile.name = 'different_net_profile'
    #     self.assertRaises(RuntimeError, self.helper.create_configuration,
    #                       self.cluster, self.api_context)
    #==========================================================================

    # positive

    @mock.patch('cmwplugin.ldeinstaller.LdeInstaller._get_ms_subnet_ip')
    def test_create_conf_creates_task_for_cluster_with_minimum_node_number(
            self, _get_ms_subnet_ip):
        _get_ms_subnet_ip.return_value = {"retcode": "10.10.10.100"}
        co, cb = self.helper.create_configuration(self.plugin,
                                                  self.cluster,
                                                  self.api_context)
        self.assertEqual(5, len(co) + len(cb))

    @mock.patch('cmwplugin.ldeinstaller.log')
    def test_create_conf_no_tasks_if_cluster_in_non_initial_state(self, log):
        self.cluster.is_initial.return_value = False
        self.cluster.get_state.return_value = 'Initial'
        co, cb = self.helper.create_configuration(self.plugin,
                                                  self.cluster,
                                                  self.api_context)
        self.assertEqual(0, len(co) + len(cb))
        self.cluster.is_initial.assert_called_with()

    @mock.patch('cmwplugin.ldeinstaller.LdeInstaller._get_ms_subnet_ip')
    def test_create_conf_creates_tasks_if_network_both_hbeat_and_mgmt(self,
                                            _get_ms_subnet_ip):
        _get_ms_subnet_ip.return_value = {"retcode": "10.10.10.100"}
        self.cluster.heartbeat_networks = self.cluster.mgmt_network
        co, cb = self.helper.create_configuration(self.plugin,
                                                  self.cluster,
                                                  self.api_context)
        self.assertEqual(5, len(co) + len(cb))

    @mock.patch('cmwplugin.ldeinstaller.ConfigTask', autospec=True)
    def tes_create_conf_creates_correct_config_tasks_for_three_nodes(
            self, config_task):
        # adding another node to get payload
        # and mix the order (should be another test)
        self.cluster.nodes = [self.node3, self.node2, self.node1]

        result = self.helper.create_configuration(self.plugin,
                                                  self.cluster,
                                                  self.api_context)

        self.assertEqual(len(config_task.mock_calls), len(result))
        node1_ifaces = [network.device_name
                        for network in self.node1.network_interfaces]
        node2_ifaces = [network.device_name
                        for network in self.node2.network_interfaces]
        node3_ifaces = [network.device_name
                        for network in self.node3.network_interfaces]
        node1_macs = [network.macaddress
                      for network in self.node1.network_interfaces]
        node2_macs = [network.macaddress
                      for network in self.node2.network_interfaces]
        node3_macs = [network.macaddress
                      for network in self.node3.network_interfaces]
        node1_ip = self.node1.network_interfaces[0].ipaddress
        node2_ip = self.node2.network_interfaces[0].ipaddress
        node3_ip = self.node3.network_interfaces[0].ipaddress
        subnet = "192.120.208.0/24"
        #self.node1.network_interfaces[0].view_subnet
        cluster_info_expected = {
            'internalNetwork': subnet,
            'controlInterface': node1_ifaces[0],
            'netID': self.cluster.cluster_id,
            'bootIP': LdeInstaller.dummy_lde_ip,
            'msHostname': self.ms_hostname,
            'msSubnetIp': self.nfs_ipaddress,
            'quick-reboot': self.cluster.quick_reboot
        }
        node_info_expected = [
            {
                'nodenumber': self.node1.node_id,
                'ip': node1_ip,
                'hostname': self.node1.hostname,
                'nodetype': 'control',
                'primarynode': True,
                'interface_list': dict(zip(
                    [
                        node1_ifaces[0],
                        node1_ifaces[1],
                        node1_ifaces[2],
                    ],
                    [
                        node1_macs[0],
                        node1_macs[1],
                        node1_macs[2],
                    ]
                )),
                'hb_interface_list': dict(zip(
                    [
                        node1_ifaces[1],
                        node1_ifaces[2],
                    ],
                    [
                        node1_macs[1],
                        node1_macs[2],
                    ]
                )),
                'tipcaddress': '1.1.1'
            },
            {
                'nodenumber': self.node2.node_id,
                'ip': node2_ip,
                'hostname': self.node2.hostname,
                'nodetype': 'control',
                'primarynode': False,
                'interface_list': dict(zip(
                    [
                        node2_ifaces[0],
                        node2_ifaces[1],
                        node2_ifaces[2],
                    ],
                    [
                        node2_macs[0],
                        node2_macs[1],
                        node2_macs[2],
                    ]
                )),
                'hb_interface_list': dict(zip(
                    [
                        node2_ifaces[1],
                        node2_ifaces[2],
                    ],
                    [
                        node2_macs[1],
                        node2_macs[2],
                    ]
                )),
                'tipcaddress': '1.1.2'
            },
            {
                'nodenumber': self.node3.node_id,
                'ip': node3_ip,
                'hostname': self.node3.hostname,
                'nodetype': 'payload',
                'primarynode': False,
                'interface_list': dict(zip(
                    [
                        node3_ifaces[0],
                        node3_ifaces[1],
                        node3_ifaces[2],
                    ],
                    [
                        node3_macs[0],
                        node3_macs[1],
                        node3_macs[2],
                    ]
                )),
                'hb_interface_list': dict(zip(
                    [
                        node3_ifaces[1],
                        node3_ifaces[2],
                    ],
                    [
                        node3_macs[1],
                        node3_macs[2],
                    ]
                )),
                'tipcaddress': '1.1.3'
            }
        ]
        config_task.assert_has_calls([
            mock.call(
                self.node1, self.cluster.software,
                LdeInstaller.configuring_lde_msg.format(self.node1.hostname),
                LdeInstaller.puppet_class_name,
                'cluster-config',
                nodes=node_info_expected,
                cluster=cluster_info_expected
            ),
            mock.call(
                self.node2, self.cluster.software,
                LdeInstaller.configuring_lde_msg.format(self.node2.hostname),
                LdeInstaller.puppet_class_name,
                'cluster-config',
                nodes=node_info_expected,
                cluster=cluster_info_expected
            ),
            mock.call(
                self.node3, self.cluster.software,
                LdeInstaller.configuring_lde_msg.format(self.node3.hostname),
                LdeInstaller.puppet_class_name,
                'cluster-config',
                nodes=node_info_expected,
                cluster=cluster_info_expected
            )
        ])

    @mock.patch('cmwplugin.ldeinstaller.ConfigTask', autospec=True)
    def tes_running_create_conf_multiple_times_starts_tipc_numbers_from_one(
            self, config_task):
        self.cluster.nodes = [self.node1, self.node2]

        node1_ifaces = [network.device_name
                        for network in self.node1.network_interfaces]
        node2_ifaces = [network.device_name
                        for network in self.node2.network_interfaces]
        node1_macs = [network.macaddress
                      for network in self.node1.network_interfaces]
        node2_macs = [network.macaddress
                      for network in self.node2.network_interfaces]
        node1_ip = self.node1.network_interfaces[0].ipaddress
        node2_ip = self.node2.network_interfaces[0].ipaddress
        subnet = "192.120.208.0/24"
        #self.node1.network_interfaces[0].view_subnet
        cluster_info_expected = {
            'internalNetwork': subnet,
            'controlInterface': node1_ifaces[0],
            'netID': self.cluster.cluster_id,
            'bootIP': LdeInstaller.dummy_lde_ip,
            'nfsIP': self.nfs_ipaddress,
            'quick-reboot': self.cluster.quick_reboot
        }
        node_info_expected = [
            {
                'nodenumber': self.node1.node_id,
                'ip': node1_ip,
                'hostname': self.node1.hostname,
                'nodetype': 'control',
                'primarynode': True,
                'interface_list': dict(zip(
                    [
                        node1_ifaces[0],
                        node1_ifaces[1],
                        node1_ifaces[2],
                    ],
                    [
                        node1_macs[0],
                        node1_macs[1],
                        node1_macs[2],
                    ]
                )),
                'hb_interface_list': dict(zip(
                    [
                        node1_ifaces[1],
                        node1_ifaces[2],
                    ],
                    [
                        node1_macs[1],
                        node1_macs[2],
                    ]
                )),
                'tipcaddress': '1.1.1'
            },
            {
                'nodenumber': self.node2.node_id,
                'ip': node2_ip,
                'hostname': self.node2.hostname,
                'nodetype': 'control',
                'primarynode': False,
                'interface_list': dict(zip(
                    [
                        node2_ifaces[0],
                        node2_ifaces[1],
                        node2_ifaces[2],
                    ],
                    [
                        node2_macs[0],
                        node2_macs[1],
                        node2_macs[2],
                    ]
                )),
                'hb_interface_list': dict(zip(
                    [
                        node2_ifaces[1],
                        node2_ifaces[2],
                    ],
                    [
                        node2_macs[1],
                        node2_macs[2],
                    ]
                )),
                'tipcaddress': '1.1.2'
            },
        ]

        # call twice to ensure that tipc numbering gets reset at each run
        self.helper.create_configuration(self.plugin,
                                         self.cluster,
                                         self.api_context)
        self.helper.create_configuration(self.plugin,
                                         self.cluster,
                                         self.api_context)

        self.assertEqual(config_task.mock_calls, [
            mock.call(
                self.node1, self.cluster.software,
                LdeInstaller.configuring_lde_msg.format(self.node1.hostname),
                LdeInstaller.puppet_class_name,
                'cluster-config',
                nodes=node_info_expected,
                cluster=cluster_info_expected
            ),
            mock.call(
                self.node2, self.cluster.software,
                LdeInstaller.configuring_lde_msg.format(self.node2.hostname),
                LdeInstaller.puppet_class_name,
                'cluster-config',
                nodes=node_info_expected,
                cluster=cluster_info_expected
            ),
            mock.call(
                self.node1, self.cluster.software,
                LdeInstaller.configuring_lde_msg.format(self.node1.hostname),
                LdeInstaller.puppet_class_name,
                'cluster-config',
                nodes=node_info_expected,
                cluster=cluster_info_expected
            ),
            mock.call(
                self.node2, self.cluster.software,
                LdeInstaller.configuring_lde_msg.format(self.node2.hostname),
                LdeInstaller.puppet_class_name,
                'cluster-config',
                nodes=node_info_expected,
                cluster=cluster_info_expected
            ),
        ])

    def test_get_iface_and_mac(self):
        node1 = mock.MagicMock()
        node1.hostname = "mn1"
        eth0= mock.MagicMock(device_name="eth0", item_type_id='eth')
        eth1= mock.MagicMock(device_name="eth1", item_type_id='eth')
        eth2= mock.MagicMock(device_name="eth0.100", item_type_id='vlan')
        eth3= mock.MagicMock(device_name="eth3", item_type_id='bond')
        eth4= mock.MagicMock(device_name="eth4",
                             item_type_id='eth',
                             master="eth3")
        eth5= mock.MagicMock(device_name="eth5",
                             item_type_id='eth',
                             master="eth3")
        eth0.macaddress = "08:00:27:5B:C1:31"
        eth1.macaddress = "08:00:27:5B:C1:32"
#        eth3.macaddress = "08:00:27:5B:C1:34"
        eth4.macaddress = "08:00:27:5B:C1:33"
        eth5.macaddress = "08:00:27:5B:C1:34"
        eth0.network_name = "mgmt"
        eth1.network_name = "traffic"
        eth2.network_name = "hb1"
        eth3.network_name = "hb2"
        for e in [eth0, eth1, eth2, eth3, eth4, eth5]:
            e.is_removed.return_value = False
            e.is_for_removal.return_value = False
        node1.network_interfaces = [eth0, eth1, eth2, eth3, eth4, eth5]
        network = "mgmt"
        dev, mac = self.helper._get_iface_and_mac(network, node1)
        self.assertEquals(dev, "eth0")
        self.assertEquals(mac, "08:00:27:5B:C1:31")

        network = "hb1"
        dev, mac = self.helper._get_iface_and_mac(network, node1)
        self.assertEquals(dev, "eth0.100")
        self.assertEquals(mac, "08:00:27:5B:C1:31")

        network = "hb2"
        dev, mac = self.helper._get_iface_and_mac(network, node1)
        self.assertEquals(dev, "eth3")
        self.assertEquals(mac, "08:00:27:5B:C1:33")
