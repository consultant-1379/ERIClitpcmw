##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.validators import ValidationError
from base_cmw_integration import CmwIntegrationBase


class TestCMWPluginIntegration(CmwIntegrationBase):

    def setUp(self):
        super(TestCMWPluginIntegration, self).setUp()

    def test_bond_interfaces(self):
        cluster_str = "/deployments/test/clusters/cluster1"
        self.setup_model(add_eth_if=False)
        for i in range(1,3):
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/b1" % i)
            self._add_bond_interface_to_model(path, 1, "heartbeat2")
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/if0" % i)
            self._add_eth_interface_to_model(path, i, 0,
                                             net_name="mgmt", ip=True)
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/if1" % i)
            self._add_eth_interface_to_model(path, i, 1, "heartbeat1")

        errors = self.plugin.validate_model(self.context_api)
        emsg = ("CMW heartbeat network 'heartbeat2' not found in "
                "network_interfaces of node 'node{0}' in cluster 'cluster1'")
        expected = [ValidationError(cluster_str + "/nodes/node1",
                                    error_message=emsg.format(1)),
                    ValidationError(cluster_str + "/nodes/node2",
                                    error_message=emsg.format(2))]

        self.assertEqual(errors, expected)
        self.assertEqual(len(errors), 2)

        for i in range(1,3):
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/if2" % i)
            self._add_eth_interface_to_model(path, i, 2, master="bond1")
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/if3" % i)
            self._add_eth_interface_to_model(path, i, 3, master="bond1")

        errors = self.plugin.validate_model(self.context_api)
        print errors
        self.assertEqual(len(errors), 0)

    def test_vlan_interface(self):
        cluster_str = "/deployments/test/clusters/cluster1"
        self.setup_model(add_eth_if=False)
        for i in range(1,3):
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/vlan1" % i)
            self._add_vlan_interface_to_model(path, 2, 100,
                                              net_name="heartbeat2")
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/if0" % i)
            self._add_eth_interface_to_model(path, i, 0,
                                             net_name="mgmt", ip=True)
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/if1" % i)
            self._add_eth_interface_to_model(path, i, 1,
                                             "heartbeat1")

        errors = self.plugin.validate_model(self.context_api)
        print errors
        emsg=("CMW heartbeat network 'heartbeat2' not found in "
              "network_interfaces of node 'node{0}' in cluster 'cluster1'")
        expected = [ValidationError(cluster_str + "/nodes/node1",
                                    error_message=emsg.format(1)),
                    ValidationError(cluster_str + "/nodes/node2",
                                    error_message=emsg.format(2))]

        self.assertEqual(errors, expected)
        self.assertEqual(len(errors), 2)

        for i in range(1,3):
            path = (cluster_str +
                    "/nodes/node%d/network_interfaces/if2" % i)
            self._add_eth_interface_to_model(path, i, 2,
                                             "network1")

        errors = self.plugin.validate_model(self.context_api)
        print errors
        self.assertEqual(len(errors), 0)
