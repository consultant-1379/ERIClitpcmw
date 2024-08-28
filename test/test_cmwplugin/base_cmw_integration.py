##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from cmwplugin.cmw_plugin import CMWPlugin
from cba_extension.cba_extension import CBAExtension
#from vcs_extension.vc import VcsExtension
from package_extension.package_extension import PackageExtension
from volmgr_extension.volmgr_extension import VolMgrExtension
from nas_extension.nas_extension import NasExtension

from litp.extensions.core_extension import CoreExtension
from network_extension.network_extension import NetworkExtension
from volmgr_extension.volmgr_extension import VolMgrExtension
from litp.core.model_manager import ModelManager
from litp.core.execution_manager import ExecutionManager

from litp.core.plugin_manager import PluginManager
from litp.core.validators import ValidationError
from litp.core.plugin_context_api import PluginApiContext
from litp.core.callback_api import CallbackApi

import unittest
import mock


def _get_jee_install_source():
    return "/tmp/jee.tgz"


class CmwIntegrationBase(unittest.TestCase):

    def _print_task_descriptions(self, tasks):
        for task in tasks:
            if hasattr(task, "description"):
                print task.description
            if hasattr(task, "task_list"):
                self._print_task_descriptions(task.task_list)

    @mock.patch('litp.core.callback_api._SecurityApi')
    def setUp(self, _SecurityApi_mock):
        self.node1 = self.node2 = None
        self.model = ModelManager()
        self.plugin_manager = PluginManager(self.model)

        core_ext = CoreExtension()
        network_ext = NetworkExtension()
        cba_ext = CBAExtension()
#        vcs_ext = VcsExtension()
        vol_ext = VolMgrExtension()
        pkg_ext = PackageExtension()
        vol_ext = VolMgrExtension()
        nas_ext = NasExtension()

        for ext in [core_ext, network_ext, cba_ext, pkg_ext, vol_ext, nas_ext]:
            self.plugin_manager.add_property_types(ext.define_property_types())
            self.plugin_manager.add_item_types(ext.define_item_types())
            if ext == core_ext:
                self.plugin_manager.add_default_model()

        self.plugin = CMWPlugin()
        for plugin in [CMWPlugin]:
            self.plugin_manager.add_plugin(plugin.__name__,
                                           "{0}.{1}".format(plugin.__module__,
                                                            plugin.__name__),
                                           "1.0.0", plugin())
        self.context_api = PluginApiContext(self.model)
        self.callback_api = mock.Mock()

        def side_effect(*args, **kwargs):
            return self.model.query(*args, **kwargs)

        self.callback_api.query.side_effect = side_effect
        self.callback_api.execution_manager.model_manager = self.model

        self.execution_manager = ExecutionManager(self.model, mock.Mock(), mock.Mock())
        self.callback_api = CallbackApi(self.execution_manager)

    def _add_item_to_model(self, *args, **kwargs):
        result = self.model.create_item(*args, **kwargs)
        self._assess_result(result)
        return result

    def _remove_item_from_model(self, *args, **kwargs):
        result = self.model.remove_item(*args, **kwargs)
        self._assess_result(result)
        return result

    def _update_item_in_model(self, *args, **kwargs):
        result = self.model.update_item(*args, **kwargs)
        self._assess_result(result)
        return result

    def _add_inherited_item_to_model(self, source_vpath, target_vpath):
        result = self.model.create_inherited(source_vpath, target_vpath)
        self._assess_result(result)
        return result

    def _assess_result(self, result):
        try:
            checks = [type(result) is list,
                      len(result),
                      type(result[0]) is ValidationError]
        except TypeError:  # result is not list
            pass
        except IndexError:  # result is empty list
            pass
        else:
            if all(checks):
                raise RuntimeError(repr(result[0]))

    def _string_and_sort(self, errors):
        return sorted([str(error) for error in errors])

    #==========================================================================
    # def _add_jboss_container_to_model(self, number, servicename=None,
    #                                   csname=None, active="2", standby="0"):
    #     if not servicename:
    #         servicename = number
    #     if not csname:
    #         csname = 'cs%s' % number
    #     node_list = "node1,node2"
    #     self._add_item_to_model(
    #         'clustered-service',
    #         '/deployments/test/clusters/cluster1/services/service%s' % number,
    #         name=csname,
    #         active=active,
    #         standby=standby,
    #         node_list=node_list
    #     )
    #     self._add_item_to_model(
    #         'jee-container',
    #         "/deployments/test/clusters/cluster1/services/service{0}"
    #         "/runtimes/jee-container{0}".format(number),
    #         install_source=_get_jee_install_source(),
    #         name="jee-container{0}".format(number)
    #     )
    #==========================================================================

    def _add_software_item_and_link(self, item, item_name):
        self._add_item_to_model(
            'package', '/software/items/%s' % item, name=item_name)
        self._add_inherit_to_model(
            '/software/items/%s' % item,
            '/deployments/test/clusters/cluster1/nodes/node1/items/%s' % item
       )
        self._add_inherit_to_model(
            '/software/items/%s' % item,
            '/deployments/test/clusters/cluster1/nodes/node2/items/%s' % item
        )

    def _add_eth_interface_to_model(self, path, idx, if_idx, net_name=None,
                                    ip=False, master=None):
        a = ("eth", path)
        kw = dict()
        kw["macaddress"] = "08:00:27:5B:C%d:3%d" % (idx, if_idx)
        kw["device_name"] = "eth%d" % if_idx
        if net_name:
            kw["network_name"] = net_name
        if ip:
            kw["ipaddress"] = "10.10.10.%d" % idx
        if master:
            kw["master"] = master

        print "adding eth"
        print a, kw
        self._add_item_to_model(*a, **kw)

    def _add_vlan_interface_to_model(self, path, idx, vlan_tag, net_name=None):
        a = ("vlan", path)
        kw = dict()
        kw["device_name"] = "eth%d.%d" % (idx, vlan_tag)
        if net_name:
            kw["network_name"] = net_name
        kw["ipaddress"] = "20.20.20.%d" % idx

        print "adding vlan"
        print a, kw
        self._add_item_to_model(*a, **kw)

    def _add_bond_interface_to_model(self, path, idx, net_name):
        a = ("bond", path)
        kw = dict()
        kw["network_name"] = net_name
        kw["device_name"] = "bond%d" % idx
        kw["mode"] = "1"
        kw["miimon"] = "100"

        print "adding bond"
        print a, kw
        self._add_item_to_model(*a, **kw)

    def add_cluster(self, num_of_nodes=2, cluster_type="cmw-cluster",
                    cluster_id='1234', fencing_num=0, vcs_cluster_type="sfha",
                    cluster_name="cluster1", add_eth_if=True):
        cluster_str = "/deployments/test/clusters/%s" % cluster_name
        nfs_mount_str = "/infrastructure/storage/nfs_mounts/nm1"
        if cluster_type == "vcs-cluster":
            self._add_item_to_model("vcs-cluster",
                                    cluster_str,
                                    cluster_type=vcs_cluster_type,
                                    cluster_id=cluster_id,
                                    llt_nets="heartbeat1,heartbeat2",
                                    low_prio_net="mgmt")
            for i in range(0, fencing_num):
                self._add_item_to_model("disk",
                                cluster_str + "/fencing_disks/fd%d" % i,
                                name='fencing_disk_{0}'.format(i),
                                uuid='10%d' % i,
                                size='1G')
        elif cluster_type == "cmw-cluster":
            self._add_item_to_model(
                "cmw-cluster",
                cluster_str,
                cluster_id="1234",
                internal_network="mgmt",
                tipc_networks="heartbeat1,heartbeat2")
        else:
            self._add_item_to_model(
                "cluster",
                cluster_str)

        # if non vcs or cmw, no heartbeats
        if cluster_type in ["vcs-cluster", "cmw-cluster"]:
            # create nodes
            for i in range(1, num_of_nodes + 1):
                self._add_item_to_model(
                    "node",
                    cluster_str + "/nodes/node%d" % i,
                    hostname="mn%d" % i,
                    node_id="%d" % i)
                self._add_inherited_item_to_model(
                    self.model.query(
                        'system', system_name='MN%d' % i)[0].get_vpath(),
                    cluster_str + "/nodes/node%d/system" % i)
                self._add_inherited_item_to_model(
                    self.model.query('route')[0].get_vpath(),
                    cluster_str + "/nodes/node%d/routes/r_0" % i)
                if add_eth_if:
                    path = (cluster_str +
                            "/nodes/node%d/network_interfaces/if0" % i)
                    self._add_eth_interface_to_model(path, i, 0,
                                                     net_name="mgmt", ip=True)
                    path = (cluster_str +
                            "/nodes/node%d/network_interfaces/if1" % i)
                    self._add_eth_interface_to_model(path, i, 1,
                                                     net_name="heartbeat1")
                    path = (cluster_str +
                            "/nodes/node%d/network_interfaces/if2" % i)
                    self._add_eth_interface_to_model(path, i, 2,
                                                     net_name="heartbeat2")
                self._add_inherited_item_to_model(
                    nfs_mount_str,
                    cluster_str + "/nodes/node%d/file_systems/nm1" % i)

    def setup_model(self, num_of_nodes=2, cluster_type="cmw-cluster",
                    cluster_id='1234', fencing_num=0, vcs_cluster_type="sfha",
                    num_of_clusters=1, add_eth_if=True):
        nfs_mount_str = "/infrastructure/storage/nfs_mounts/nm1"
        self._add_item_to_model(
            'network',
            '/infrastructure/networking/networks/mgmt',
            name='mgmt',
            subnet='10.10.10.0/24',
            litp_management='true')
        self._add_item_to_model(
            'route',
            '/infrastructure/networking/routes/def_route',
            subnet='0.0.0.0/0', gateway='10.10.10.254')
        # Create node systems
        for i in range(1, num_of_nodes + 1):
            self._add_item_to_model(
                'system',
                '/infrastructure/systems/system_%d' % i,
                system_name='MN%d' % i)
        # Create deployment
        self._add_item_to_model(
            "deployment",
            "/deployments/test")
        self._add_item_to_model(
            "nfs-mount",
            nfs_mount_str,
            export_path="/exports/cluster",
            provider="nfs1",
            mount_point="/cluster",
            mount_options="soft",
            network_name="mgmt")
        for i in range(1, num_of_clusters + 1):
            self.add_cluster(num_of_nodes, cluster_type, cluster_id,
                             fencing_num, vcs_cluster_type,
                             add_eth_if=add_eth_if)

        self._add_item_to_model(
            'eth',
            '/ms/network_interfaces/if0',
            macaddress='08:00:27:5B:C2:AA',
            device_name='eth0',
            ipaddress='10.10.10.253',
            network_name='mgmt')
        self._add_item_to_model(
            'package',
            '/software/items/java',
            name='jre',
            )
        self._add_inherited_item_to_model(
            '/software/items/java',
            "/ms/items/java")

    def _add_clustered_service_to_model(self, number, csname=None, active="2", standby="0"):
        if not csname:
            csname = 'cs%s' % number

        node_list = ','.join(["node{0}".format(x+1) for x in range(int(active)+int(standby))])
        self._add_item_to_model(
            'cmw-clustered-service',
            '/deployments/test/clusters/cluster1/services/service%s' % number,
            name=csname,
            active=active,
            standby=standby,
            node_list=node_list
        )

    def _add_jboss_container_to_model(self, number, servicename=None, csname=None,
                              active="2", standby="0"):
        self._add_clustered_service_to_model(number, csname, active, standby)
        self._add_item_to_model(
            'jee-container',
            "/deployments/test/clusters/cluster1/services/service{0}"
            "/applications/jee-container{0}".format(number),
            install_source=_get_jee_install_source(),
            name="jee-container{0}".format(number)
        )

    def _add_service_to_model(self, number, servicename=None, csname=None,
                              active="2", standby="0", no_of_ips=1):

        if not servicename:
            servicename = number
        self._add_clustered_service_to_model(number, csname=csname,
                                                active=active, standby=standby)
        service_path = "/software/services/lsb{0}".format(number)
        self._add_item_to_model(
            'service',
            service_path,
            service_name=servicename,
        )
        self._add_inherited_item_to_model(
            service_path,
            "/deployments/test/clusters/cluster1/services/service{0}"
            "/applications/lsb{0}".format(number)
        )
        #name="runtime{0}".format(number),
            #restart_limit=3,
            #startup_retry_limit=3,
            #status_interval=30,
            #status_timeout=60
        #======================================================================
        # ips = []
        # for ip in range(no_of_ips):
        #     ips.append(self._add_item_to_model(
        #         'vip',
        #         "/deployments/test/clusters/cluster1/services/service{0}"
        #         "/runtimes/runtime{0}/ipaddresses/ip{1}".format(number, ip),
        #         network_name='mgmt',
        #         ipaddress='10.10.10.%d' % (ip + 51)
        #     ).ipaddress)
        # return ips
        #======================================================================
