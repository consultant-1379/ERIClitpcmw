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
Module contains LdeInstaller class which is used by CMWPlugin to validate
model for LDE installation on cluster nodes and create configuration for it
"""

from litp.core.litp_logging import LitpLogger
from litp.core.validators import ValidationError
from litp.core.execution_manager import ConfigTask
from cmwplugin.cmw_mco_api import CmwMcoApi
from cmwplugin.execution import patch_callback
from cmwplugin.utils import (patch_helper_callback,
                             valid_cluster_nodes)

# pylint doesn't like it to be called 'log'
log = LitpLogger()  # pylint: disable=invalid-name


@patch_helper_callback
class LdeInstaller(object):
    """
    Class validates and creates configuration for any CMW cluster in initial
    state. The configuration generated creates lde cluster
    """
    cluster_min_nodes = 2
    cluster_max_nodes = 2047  # max number of tipc numbers (1.1.X)
    not_enough_nodes_msg = ("CMW cluster has too few nodes: {0}; minimum "
                            "number: {1}")
    unset_node_id_msg = "Node '{0}' on CMW cluster '{1}' has no node_id"
    missing_node_ids_msg = ("Impossible to designate control nodes on CMW "
                            "cluster '{0}'; node_ids: {1} missing")
    duplicate_node_ids_msg = "Duplicate node ids: {0}"
    invalid_node_id_msg = ("Invalid node id: {0} in node '{1}' on cluster "
                           "'{2}'; only integers in range 1-{3} are supported")
    one_node_only_msg = "CMW cluster has only one node"
    mgmt_missing_iface_msg = ("Node doesn't expose any interfaces to "
                              "management network")
    heartbeat_missing_iface_msg = ("Node doesn't expose any interfaces to "
                                   "heartbeat network '{0}'")
    #==========================================================================
    # false_heartbeat_redundancy_msg = ("More than one TIPC heartbeat network "
    #                                   "links to the same interface")
    #==========================================================================
    prepare_lde_msg = 'Load LDE packages on "{0}"'
    configuring_lde_msg = 'Configure LDE on "{0}"'
    create_cluster_conf_msg = 'Creating cluster.conf on node "{0}"'
    no_clusters_found_msg = 'No CMW clusters found'
    no_mgmt_network_msg = ("No management network specified for CMW cluster "
                           "'{0}'")
    mgmt_net_not_in_net_profile_msg = ("CMW management network not found in "
                                       "network_profile of node {0} "
                                       "in cluster {1}")
    hb_net_not_in_net_profile_msg = ("CMW heartbeat network '{0}' not found "
                                     "in network_interfaces of node '{1}' "
                                     "in cluster '{2}'")
    no_ip_on_mgmt_network_msg = "No ip assigned on mgmt network"
    #separate_network_profiles_msg = 'Nodes have separate network profiles'
    dummy_lde_ip = '10.46.86.1'
    cluster_state_msg = "CMW cluster '{0}' in '{1}' state"
    no_lde_software_item_msg = "CMW cluster doesn't have 'lde' software item"
    no_cluster_mounted = "Node does not have a mount for /cluster"
    not_all_mounts_using_same_provider = ("Nodes should use the same storage "
                                          "provider for all /cluster mounts")
    not_supported_iface_type = "Interface type '{0}' is not supported"
    tipc_unique_mac_required = ("Unique MAC address required for "
                                "tipc_networks in cluster '{0}'")

#    no_nfs_server = "Management server acting as NFS server has unknown ip"

    def __init__(self):
        super(LdeInstaller, self).__init__()
        self.tipc_addr_gen = None

    def _detect_not_enough_nodes(self, cluster):
        """
        Creates list of ValidationErrors for each cluster that has less nodes
        than required
        """
        errors = []
        cluster_nodes = valid_cluster_nodes(cluster)
        node_count = len(cluster_nodes)
        if node_count < self.cluster_min_nodes:
            errors.append(ValidationError(
                item_path=cluster.nodes.get_vpath(),
                error_message=self.not_enough_nodes_msg.format(
                    node_count, self.cluster_min_nodes)))
        return errors

    def _detect_incorrect_node_ids(self, cluster):
        """
        Creates list of ValidationErrors for each cluster which nodes have
        missing, bad or duplicated node_ids.
        """
        errors = []

        cluster_nodes = valid_cluster_nodes(cluster)

        if self._has_enough_nodes(cluster):
            unset_nodes = self._get_nodes_with_unset_node_ids(
                cluster_nodes)
            errors += [ValidationError(
                item_path=node.get_vpath(),
                error_message=self.unset_node_id_msg.format(
                    node.item_id, cluster.item_id))
                for node in unset_nodes]

            invalid_nodes = self._get_nodes_with_invalid_ids(
                cluster_nodes)
            errors += [ValidationError(
                item_path=node.get_vpath(),
                error_message=self.invalid_node_id_msg.format(
                    "'" + node.node_id + "'",
                    node.item_id, cluster.item_id,
                    self.cluster_max_nodes))
                for node in invalid_nodes]

            missing = self._get_missing_node_ids(cluster_nodes)
            if missing:
                errors.append(ValidationError(
                    item_path=cluster.get_vpath(),
                    error_message=self.missing_node_ids_msg.format(
                        cluster.item_id, ", ".join(missing))))

            duplicates = self._get_duplicate_node_ids(cluster_nodes)
            if duplicates:
                errors.append(ValidationError(
                    item_path=cluster.get_vpath(),
                    error_message=self.duplicate_node_ids_msg.format(
                        ",".join(duplicates))))

        return errors

    def _detect_mgmt_network_problems(self, cluster):
        """
        Creates list of ValidationErrors each node in cluster that doesn't have
        an ip on mgmt network
        """
        errors = []
        cluster_nodes = valid_cluster_nodes(cluster)

        mgmt_network = cluster.internal_network
        if not mgmt_network:
            errors.append(ValidationError(
                item_path=cluster.get_vpath(),
                error_message=self.no_mgmt_network_msg.format(
                    cluster.item_id)))
        else:
            for node in cluster_nodes:
                if not self._get_ip_for_network(mgmt_network, node):
                    errors.append(ValidationError(
                        item_path=node.get_vpath(),
                        error_message=self.no_ip_on_mgmt_network_msg))

        return errors

    def _detect_missing_cluster_mount(self, cluster):
        """
        Returns a list with ValidationError if cluster nodes do not have
        a file_system  mounted to /cluster
        """
        errors = []
        cluster_nodes = valid_cluster_nodes(cluster)

        mount_to_provider = dict()
        for node in cluster_nodes:
            found = False
            for fs in node.file_systems:
                if fs.mount_point == "/cluster":
                    found = True
                    mount_to_provider[fs.item_id] = fs.provider
            if found is False:
                errors.append(ValidationError(
                        item_path=node.get_vpath(),
                        error_message=self.no_cluster_mounted))
        providers = set(mount_to_provider.values())
        if len(providers) > 1:
            errors.append(ValidationError(
                    item_path=cluster.get_vpath(),
                    error_message=self.not_all_mounts_using_same_provider))

        return errors

    #==========================================================================
    # def _detect_multiple_netprofiles(self, cluster):
    #     """
    #     Detects if nodes are disconnected due to have different network
    #     profiles linked to them
    #     Returns a list with a ValidationError
    #     """
    #     if self._check_nodes_on_one_netprofile(cluster.nodes):
    #         return [ValidationError(
    #             item_path=cluster.get_vpath(),
    #             error_message=self.separate_network_profiles_msg)]
    #     return []
    #==========================================================================

    def _detect_heartbeat_problems(self, cluster):
        """
        Detects if all nodes in clusters have configured interfaces on all
        heartbeat networks.
        Returns a list of ValidationErrors
        """
        errors = []
        cluster_nodes = valid_cluster_nodes(cluster)
        hb_ifaces = {}
        for node in cluster_nodes:
            for heartbeat in cluster.tipc_networks.split(","):
                nic_mac = self._get_iface_and_mac(heartbeat, node)
                if not nic_mac:
                    msg = self.hb_net_not_in_net_profile_msg.format(
                        heartbeat, node.item_id,
                        cluster.item_id)
                    errors.append(ValidationError(
                        item_path=node.get_vpath(),
                        error_message=msg))
                else:
                    hb_ifaces[nic_mac[0]] = nic_mac[1]
            if len(hb_ifaces.values()) != len(set(hb_ifaces.values())):
                msg = self.tipc_unique_mac_required.format(
                    cluster.item_id)
                errors.append(ValidationError(
                    item_path=cluster.get_vpath(),
                    error_message=msg))
        return errors

    # Already validate on the item_type
    #==========================================================================
    # def _detect_false_hbeat_redundancy(self, cluster):
    #     """
    #     Detects if all heartbeat networks in clusters are really separate
    #     networks.
    #     Returns a list of ValidationErrors
    #     """
    #     errors = []
    #     # assume if network name and interface are the same then we deal
    #     # with a single network
    #     net_props = [(hbeat.network_name, hbeat.interface)
    #                  for hbeat in cluster.heartbeat_networks]
    #     if len(set(net_props)) < len(net_props):
    #         errors.append(ValidationError(
    #             item_path=cluster.get_vpath(),
    #             error_message=self.false_heartbeat_redundancy_msg))
    #     return errors
    #==========================================================================

    def validate_model(self, cluster):
        """
        Validates any cmw cluster that is in initial status
        Returns a list of ValidationErrors
        """
        errors = []

        # TODO move this log to CMWPlugin
        log.trace.debug(LdeInstaller.cluster_state_msg.format(
            cluster.item_id, cluster.get_state()))
        if cluster.item_type_id == 'cmw-cluster' and cluster.is_initial():
            errors += self._detect_not_enough_nodes(cluster)
            errors += self._detect_incorrect_node_ids(cluster)
            errors += self._detect_mgmt_network_problems(cluster)
            errors += self._detect_missing_cluster_mount(cluster)
            #TODO, should we check on validate ?
            #errors += self._detect_multiple_netprofiles(cluster)
            # Already validated in item_type
            #errors += self._detect_false_hbeat_redundancy(cluster)
            errors += self._detect_heartbeat_problems(cluster)

        return errors

    def _handle_model_errors(self, cluster):
        """
        Checks if any problem with required model data has slipped through
        other checks and raises RuntimeError if so
        """
        # not caught by cluster model extension validation
        cluster_nodes = valid_cluster_nodes(cluster)
        node_count = len(cluster_nodes)
        if node_count < self.cluster_min_nodes:
            raise RuntimeError(self.not_enough_nodes_msg.format(
                node_count, self.cluster_min_nodes))

        # not caught by CmwPlugin.validate() method

        self._handle_node_id_errors(cluster)

        #======================================================================
        # if self._check_nodes_on_one_netprofile(cluster.nodes):
        #     raise RuntimeError(self.separate_network_profiles_msg)
        #======================================================================

        for node in cluster_nodes:
            ip_address = self._get_ip_for_network(
                cluster.internal_network, node)
            if not ip_address:
                raise RuntimeError(self.no_ip_on_mgmt_network_msg)

    def _handle_node_id_errors(self, cluster):
        """
        Checks if any problem related to node ids in model data has slipped
        through other checks and raises RuntimeError if yes
        """
        cluster_nodes = valid_cluster_nodes(cluster)

        unset = self._get_nodes_with_unset_node_ids(cluster_nodes)
        if unset:
            item_ids = [node.item_id for node in unset]
            raise RuntimeError(self.unset_node_id_msg.format(
                cluster.item_id, ", ".join(item_ids)))

        invalid = self._get_nodes_with_invalid_ids(cluster_nodes)
        if invalid:
            inv_node_ids = ["'" + node.node_id + "'" for node in invalid]
            item_ids = [node.item_id for node in invalid]
            raise RuntimeError(self.invalid_node_id_msg.format(
                ", ".join(inv_node_ids),
                ", ".join(item_ids),
                cluster.item_id,
                self.cluster_max_nodes))

        missing = self._get_missing_node_ids(cluster_nodes)
        if missing:
            raise RuntimeError(self.missing_node_ids_msg.format(
                cluster.item_id, ", ".join(missing)))

    def create_configuration(self, plugin, cluster, plugin_api):
        """
        Creates configuration in form of ConfigTask for all nodes in any
        CMW cluster that is in initial state
        Returns a list of ConfigTasks
        Will do same checks as validate_model and throw RuntimeErrors for all
        failures (example situation: validate_model hasn't been called at all)
        """
        self._handle_model_errors(cluster)

        cluster_nodes = valid_cluster_nodes(cluster)

        # placed here to ensure that multiple calls to create_configuration
        # will always result the generator to start at it's correct start
        # position
        self.tipc_addr_gen = self._get_tipc_addr_gen()
        conf_tasks = []
        callback_tasks = []

        if cluster.is_initial():
            mgmt_net_subnet = self._get_mgmt_subnet(plugin_api, cluster)

            ms_server = plugin_api.query('ms')[0]
            ms_hostname = ms_server.hostname

            ms_subnet_ip = self._get_ms_subnet_ip(mgmt_net_subnet)

            ctrl_iface = self._retrieve_control_iface(cluster.internal_network,
                                                      cluster_nodes)
            cluster_cfg = {
                'internalNetwork': mgmt_net_subnet,
                'msHostname': ms_hostname,
                'msSubnetIP': ms_subnet_ip,
                'bootIP': self.dummy_lde_ip,
                'netID': cluster.cluster_id,
                'quick-reboot': cluster.quick_reboot,
                'controlInterface': ctrl_iface,
            }

            nodes_cfg = self._configure_nodes(cluster)

            return self._generate_tasks(plugin, cluster, nodes_cfg,
                                        cluster_cfg)
        return conf_tasks, callback_tasks

    def create_callback_task(self, *args, **kwargs):
        '''
        Function is overridden by  @patch_helper_callback to
        provide implementation
        '''
        pass

    def _generate_tasks(self, plugin, cluster, nodes_cfg, cluster_cfg):
        """Creates list of tasks"""
        cluster_nodes = valid_cluster_nodes(cluster)
        nodes = self._sort_nodes(cluster_nodes)

        conf_tasks = []
        callback_tasks = []

        clust_conf_task = ConfigTask(nodes[0],
                                     cluster.software,
                                     self.create_cluster_conf_msg.format(
                                                        nodes[0].hostname),
                                     'cmw::cluster_conf',
                                     "cluster-config",
                                     nodes=nodes_cfg,
                                     cluster=cluster_cfg)
        for fs in nodes[0].file_systems:
            if fs.mount_point == "/cluster":
                clust_conf_task.requires.add(fs)
        conf_tasks.append(clust_conf_task)

        for node in nodes:
            task = ConfigTask(node, cluster.software,
                              self.prepare_lde_msg.format(node.hostname),
                              'cmw::lde', "lde-config",
                              nodes=nodes_cfg, cluster=cluster_cfg)
            for fs in node.file_systems:
                if fs.mount_point == "/cluster":
                    task.requires.add(fs)
            conf_tasks.append(task)

            callback_tasks.append(
                self.create_callback_task(
                    plugin,
                    cluster.software,
                    self.configuring_lde_msg.format(node.hostname),
                    self._config_LDE,
                    node=node.hostname,
                )
            )
        return conf_tasks, callback_tasks

    def _configure_nodes(self, cluster):
        """
        Generates nodes section of configuration
        Returns list of dicts
        """
        cluster_nodes = valid_cluster_nodes(cluster)
        nodes = self._sort_nodes(cluster_nodes)
        nodes_cfg = list()
        for node in nodes:

            ip_address = self._get_ip_for_network(
                cluster.internal_network, node)
            node_cfg = {
                'nodenumber': node.node_id,
                'nodetype': self._get_nodetype(node),
                'primarynode': self._is_primary_node(node),
                'hostname': node.hostname,
                'tipcaddress': self.tipc_addr_gen.next(),
                'ip': ip_address,
            }

            hb_ifaces = self._get_hb_iface_list(cluster, node)
            node_cfg['hb_interface_list'] = hb_ifaces

            ifaces = self._get_full_iface_list(cluster, node)
            node_cfg['interface_list'] = ifaces
            nodes_cfg.append(node_cfg)
        return nodes_cfg

    def _get_full_iface_list(self, cluster, node):
        """
        Returns a list of tuple(iface_name, macaddress) interfaces that each
        node exposes on mgmt and all heartbeat networks
        Assumes there is only one interface on each node per each network
        """
        ifaces = self._get_hb_iface_list(cluster, node)
        nic_mac = self._get_iface_and_mac(cluster.internal_network, node)
        # may overwrite a key with same value if one of networks acts as both
        # mgmt and heartbeat
        ifaces[nic_mac[0]] = nic_mac[1]

        return ifaces

    def _get_hb_iface_list(self, cluster, node):
        """
        Returns a list of tuple(iface_name, macaddress) interfaces that each
        node exposes on all heartbeat networks
        Assumes there is only one interface on each node per each network
        """
        hb_ifaces = {}
        for heartbeat in cluster.tipc_networks.split(","):
            iface_mac = self._get_iface_and_mac(heartbeat, node)
            if not iface_mac:
                raise RuntimeError(
                    self.heartbeat_missing_iface_msg.format(
                        heartbeat))
            hb_ifaces[iface_mac[0]] = iface_mac[1]
        return hb_ifaces

    def _retrieve_control_iface(self, mgmt_network, nodes):
        """
        Return name of the control interface
        """
        eths = []
        for node in nodes:
            iface, _ = self._get_iface_and_mac(mgmt_network, node)
            if not iface:
                raise RuntimeError(self.mgmt_missing_iface_msg)
            eths.append(iface)

        return eths[0]

    @staticmethod
    def _get_missing_node_ids(nodes):
        """
        Checks if primary and secondary control nodes can be established
        based on node_id
        Convention: node_id = 1 means primary control node
        node_id = 2 means secondary control node
        """
        missing = []
        node_ids = [node.node_id for node in nodes]
        # always check
        if "1" not in node_ids:
            missing.append("1")
        # only check if more than 1 node
        if len(nodes) > 1 and "2" not in node_ids:
            missing.append("2")

        return missing

    @staticmethod
    def _get_nodes_with_unset_node_ids(nodes):
        """
        Get nodes that don't have node_id properties set
        """
        return [node for node in nodes if not node.node_id]

    def _get_nodes_with_invalid_ids(self, nodes):
        """
        Get nodes that don't have node_id properties set
        """
        invalid_nodes = []
        for node in nodes:
            if node.node_id:
                try:
                    node_id = int(node.node_id)
                except ValueError:
                    invalid_nodes.append(node)
                else:
                    if node_id < 1 or node_id > self.cluster_max_nodes:
                        invalid_nodes.append(node)
        return invalid_nodes

    @staticmethod
    def _sort_nodes(nodes):
        """
        Sorts list of nodes by node_id
        """
        nodes = sorted(nodes, key=lambda node: node.node_id)
        return nodes

    @staticmethod
    def _get_duplicate_node_ids(nodes):
        """
        Retrieves duplicated node_ids
        """
        node_ids = [node.node_id for node in nodes if node.node_id is not None]
        return list(set([nid for nid in node_ids if node_ids.count(nid) > 1]))

    def _get_mgmt_subnet(self, plugin_api, cluster):
        """
        Retrieves the subnet from management network found in network_profile
        on any node
        """
        networks = plugin_api.query("network", name=cluster.internal_network)
        if not networks:
            return None
        else:
            return networks[0].subnet

    def _get_iface_and_mac(self, network, node):
        """
        Retrieves interface-macaddress tuple of interface exposed by a node
        to a network.
        Assumes single interface per network (as does views framework)
        """
        try:
            iface = self._get_network_if_in_network_interfaces(network,
                                                      node.network_interfaces)
            device_name = getattr(iface, 'device_name')
            mac = ''
            if iface.item_type_id == "eth":
                mac = getattr(iface, 'macaddress', '')
            elif iface.item_type_id == "vlan":
                tagged_dev, _ = device_name.rsplit(".", 1)
                eth_iface = self._get_device_name_in_network_interfaces(
                    tagged_dev,
                    node.network_interfaces)
                if eth_iface:
                    mac = getattr(eth_iface, 'macaddress', '')
            elif iface.item_type_id == "bond":
                bond_slaves = self._get_bond_interface_slaves(iface,
                                                    node.network_interfaces)
                if bond_slaves:
                    mac = getattr(bond_slaves[0], 'macaddress', '')
            else:
                raise RuntimeError(self.not_supported_iface_type.format(
                        iface.item_type_id))
            if device_name and mac:
                return [device_name, mac]
        except AttributeError:
            pass  # return None

    def _get_bond_interface_slaves(self, bond_interface, network_interfaces):
        """
        Returns a list of interfaces which are eth slaves for a given bond.
        The list is ordered by device_name ascending.
        """
        if bond_interface.item_type_id != 'bond':
            raise RuntimeError("The interface %s must be of type bond "
                               "to get its slaves." % bond_interface)
        interfaces = self._get_network_interfaces_by_type('eth',
                                                          network_interfaces)
        name = bond_interface.device_name
        slaves = [e for e in interfaces if hasattr(e, 'master') and
                  e.master == name]
        slaves.sort(lambda a, b: cmp(a.device_name, b.device_name))
        return slaves

    @staticmethod
    def _get_ms_subnet_ip(mgmt_net_subnet):
        """
        Generates an IP address in the same subnet as the mgmt network
        """
        sub_ip = mgmt_net_subnet.split("/")[0].split(".")
        sub_ip[3] = "1"
        ms_subnet_ip = ".".join(sub_ip)
        return ms_subnet_ip

    @staticmethod
    def _get_device_name_in_network_interfaces(dev_name, network_interfaces):
        """
        Gets interface from the network_interfaces of a node
        """
        for iface in network_interfaces:
            if dev_name == iface.device_name:
                return iface

    @staticmethod
    def _get_network_if_in_network_interfaces(network, network_interfaces):
        """
        Gets interface from the network_interfaces of a node
        """
        for iface in network_interfaces:
            if network == iface.network_name:
                return iface

    @staticmethod
    def _get_network_interfaces_by_type(net_type, network_interfaces):
        """
        Gets network_interfaces in a node with a specific type
        """
        return [n for n in network_interfaces
                if not n.is_removed() and not n.is_for_removal() and
                    n.item_type_id == net_type]

    def _get_ip_for_network(self, network, node):
        """
        Retrieves ip address of a node on a particular network
        """
        ips = self._get_for_network(network, node, 'ipaddress')
        if ips:
            return ips[0]

    def _get_for_network(self, network, node, *property_names):
        try:
            iface = self._get_network_if_in_network_interfaces(network,
                                                      node.network_interfaces)
            return ([getattr(iface, "%s" % prop)
                          for prop in property_names])
        except AttributeError:
            pass  # return None

    @staticmethod
    def _check_nodes_on_one_netprofile(nodes):
        """
        Tests if all nodes in cluster share one network_profile
        """
        return len(set([node.network_profile.name for node in nodes])) > 1

    @staticmethod
    def _get_tipc_addr_gen(start=1):
        """
        Creates a generator for tipc addresses
        Generation starts with 1.1.1 and increases the last fragment by one
        """
        while True:
            yield '1.1.' + str(start)
            start += 1

    @staticmethod
    def _get_nodetype(node):
        """
        Retrieves node type based on node_id
        Convention is: node_ids 1-2 are control nodes;
        node_ids above that mean the nodes are payload nodes
        """
        if int(node.node_id) > 2:
            return 'payload'
        else:
            return 'control'

    @staticmethod
    def _is_primary_node(node):
        """
        Checks if a node is a primary one (first control node)
        based on node_id
        Convention is: node_id = 1 means it's a primary node
        """
        return node.node_id == "1"

    def _has_enough_nodes(self, cluster):
        """
        Check if cluster has any nodes
        """
        cluster_nodes = valid_cluster_nodes(cluster)
        return len(cluster_nodes) >= self.cluster_min_nodes

    @staticmethod
    @patch_callback
    def _config_LDE(callback_api, node):  # pylint: disable=W0613
        '''
        Executes the lde-config command using mcollective on managed node
        '''
        cmw_mco_cmd = CmwMcoApi()
        cmw_mco_cmd.set_node(node)
        cmw_mco_cmd.lde_config()
