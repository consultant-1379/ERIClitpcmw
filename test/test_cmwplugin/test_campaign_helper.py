##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from cmwplugin.campaign_helper import cmwCampaignHelper, CMWCampaignValidator
from cmwplugin.campaign.cmw_cluster_manager import cmwClusterManager
from cmwplugin.campaign.cmw_software import cmwBundle
from cmwplugin.campaign.cmw_etf import cmwETFGenerator
from cmwplugin.cmw_plugin import CMWPlugin
from cba_extension.cba_extension import CBAExtension
from package_extension.package_extension import PackageExtension

from litp.extensions.core_extension import CoreExtension
from network_extension.network_extension import NetworkExtension
from litp.core.model_manager import ModelManager
from litp.core.plugin_manager import PluginManager
from litp.core.validators import ValidationError
from litp.core.plugin_context_api import PluginApiContext

import unittest
import mock
from base_cmw_integration import CmwIntegrationBase
from cmwplugin.campaign.cmw_model_manager import cmwModelManager
from cmwplugin.campaign.cmw_etf import cmwETF


def _get_rpm_path_SE(rpm_info):
    return "/tmp/test.rpm"


def _get_sdp_SE(rpm_path):
    return cmwBundle("cmw-test-V1-R1", "/tmp/test.sdp")


def _get_rpm_install_files(rpm_path):
    return ["/etc/init.d/httpd", "/bin/true"]


def _execute_SE_n(node, command):
    if command.startswith("/bin/ls"):
        return 1, "", ""


def _execute_SE_p(node, command):
    if command.startswith("/bin/ls"):
        return 0, "", ""


class TestCMWCampaignIntegration(CmwIntegrationBase):

    def setUp(self):
        super(TestCMWCampaignIntegration, self).setUp()

    def _add_item_to_model(self, *args, **kwargs):
        result = self.model.create_item(*args, **kwargs)
        self._assess_result(result)
        return result

    def _assess_result(self, result):
        try:
            checks = [type(result) is list,
                      len(result),
                      type(result[0]) is ValidationError]
        except TypeError:  # result is not list
            pass
        else:
            if all(checks):
                raise RuntimeError(repr(result[0]))

    def test_validate_model(self):
        self.setup_model()
        errors = cmwCampaignHelper().validate_model(self.context_api)
        self.assertEqual(len(errors), 0)

    def _add_software_item_and_link(self, item, item_name):
        package_vpath = '/software/items/%s' % item
        self._add_item_to_model(
            'package', package_vpath, name=item_name)
        self._add_inherited_item_to_model(
            package_vpath,
            '/deployments/test/clusters/cluster1/nodes/node1/items/%s' % item
        )
        self._add_inherited_item_to_model(
            package_vpath,
            '/deployments/test/clusters/cluster1/nodes/node2/items/%s' % item
        )

#==============================================================================
#     def test_validate_jdk_model_error(self):
#         self.setup_model()
#         self._add_jboss_container_to_model(1, csname="a")
#         self._add_software_item_and_link(
#             'ERIClitpjboss',
#             'ERIClitpmnjboss_CXP9030959')
#         expected = sorted(["</deployments/test/clusters/cluster1/services/service1 - ValidationError - Node 'mn1' does not have 'jdk' package required for jee container>",
#                            "</deployments/test/clusters/cluster1/services/service1 - ValidationError - Node 'mn2' does not have 'jdk' package required for jee container>"])
# 
#         errors = cmwCampaignHelper().validate_model(self.context_api)
#         self.assertEqual(self._string_and_sort(errors), expected)
#==============================================================================

#==============================================================================
#     def test_validate_jdk_model_success(self):
#         self.setup_model()
#         self._add_jboss_container_to_model(1, csname="a")
#         self._add_software_item_and_link('jdk', 'jdk')
# 
#         errors = cmwCampaignHelper().validate_model(self.context_api)
#         for error in errors:
#             print errors
#         self.assertEqual(len(errors), 2)
#==============================================================================

    def test_validate_single_cluster(self):
        self.setup_model()
        self.add_cluster(cluster_name="cluster2")

        errors = cmwCampaignHelper().validate_model(self.context_api)
        self.assertEqual(len(errors), 1)

    def test_unique_service_name(self):
        self.setup_model()
        self._add_service_to_model(1, "a")
        self._add_service_to_model(2, "a")
        errors = cmwCampaignHelper().validate_model(self.context_api)
        print errors
        self.assertEqual(len(errors), 1)

    def test_unique_clustered_service_name(self):
        self.setup_model()
        self._add_service_to_model(1, csname="a")
        self._add_service_to_model(2, csname="a")
        errors = cmwCampaignHelper().validate_model(self.context_api)
        for error in errors:
            print error
        self.assertEqual(len(errors), 1)
# CANT create circular deps because of parsing error
#==============================================================================
#     def test_circular_dependencies_on_clustered_service(self):
#         self.setup_model()
#         self._add_service_to_model(1)
#         self._add_service_to_model(2)
#
#         self._update_item_in_model(
#                     '/deployments/test/clusters/cluster1/services/service1/',
#                     dependency_list='cs2')
#         self._update_item_in_model(
#                     '/deployments/test/clusters/cluster1/services/service2/',
#                     dependency_list='cs1')
#         errors = cmwCampaignHelper().validate_model(self.context_api)
#         self.assertEqual(len(errors), 1)
#==============================================================================

    @mock.patch('yum.YumBase')
    def test_packages_should_only_be_declared_in_runtime(self, yumbase):
        yumbase.doPackageLists = True

        self.setup_model()
        self._add_service_to_model(1)
        self._add_item_to_model(
            'package',
            '/software/items/httpd',
            name='httpd'
        )
        self._add_inherited_item_to_model(
            '/software/items/httpd',
            '/deployments/test/clusters/cluster1/nodes/node1/items/httpd'
        )
        self._add_inherited_item_to_model(
            '/software/items/httpd',
            '/software/services/lsb1/packages/httpd'
        )
        errors = cmwCampaignHelper().validate_model(self.context_api)
        self.assertEqual(len(errors), 1)

    def test_cmw_clustered_service_must_define_service(self):
        self.setup_model()
        node_list = "node1,node2"
        self._add_item_to_model(
            'cmw-clustered-service',
            '/deployments/test/clusters/cluster1/services/service1',
            name="cs1",
            active="2",
            standby="0",
            node_list=node_list
        )

        errors = cmwCampaignHelper().validate_model(self.context_api)
        expected = ("[</deployments/test/clusters/cluster1/services/service1 - ValidationError - Clustered service using CMW must contain an application>]")
        self.assertEqual(str(errors), expected)

    def test_active_standby_count_matches_node_count(self):
        self.setup_model()
        self._add_service_to_model(1, active=2, standby=1)
        errors = cmwCampaignHelper().validate_model(self.context_api)
        # Reports that standby != 1,
        # and active+standby (2+1) != num nodes (2)
        expected = "[</deployments/test/clusters/cluster1/services/service1 - ValidationError - Only NWAY-ACTIVE services supported>, </deployments/test/clusters/cluster1/services/service1 - ValidationError - Node: node3 is not in the deployment>]"
        self.assertEqual(str(errors), expected)

    @mock.patch('yum.YumBase')
    def test_os_packages_not_allowed(self, yumbase):
        yumbase.doPackageLists = True

        self.setup_model()
        self._add_service_to_model(1)
        self._add_item_to_model(
            'package',
            '/software/items/httpd',
            name='httpd',
            repository='OS',
            version='1-1'
        )
        self._add_inherited_item_to_model(
            '/software/items/httpd',
            ('/software/services/lsb1/packages/httpd'),
        )
        errors = cmwCampaignHelper().validate_model(self.context_api)
        expected = "[</deployments/test/clusters/cluster1/services/service1/applications/lsb1 - ValidationError - OS packages not supported in cmw-clustered-service>]"
        self.assertEqual(str(errors), expected)

    @mock.patch('cmwplugin.campaign.cmw_software_manager.cmwSoftwareManager.get_rpm_path',
                mock.Mock(side_effect=_get_rpm_path_SE))
    @mock.patch('cmwplugin.campaign.cmw_software_manager.cmwSoftwareManager.get_sdp',
                mock.Mock(side_effect=_get_sdp_SE))
    @mock.patch('cmwplugin.campaign.cmw_software.RpmInfo.get_rpm_install_files',
                mock.Mock(side_effect=_get_rpm_install_files))
    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi.check_file_exists',
                mock.Mock(side_effect=1))
    def test_validate_lsb_service(self):
        primary_node = "mn1"
        nodes = ["mn2", "mn1"]
        services = {
            "cs1": {
                "dependencies": {},
                "nodes": {
                    "node1": {
                        "amf-name": "SC-1"
                    },
                    "node2": {
                        "amf-name": "SC-2"
                    }
                },
                "active": "1",
                "standby": "1",
                "applications": {
                    "lsb1": {
                        "service_name": "httpd",
                        "packages": {
                            "nano": {
                                "name": "nano",
                                "repository": "products"
                            },
                        },
                        "type": "service-base",
                        "cleanup_command": "/bin/true"
                    }
                  }
                },
                "cs2": {
                "dependencies": {"cs2": {"name": "cs1"}},
                "nodes": {
                    "node1": {
                        "amf-name": "SC-1"
                    },
                    "node2": {
                        "amf-name": "SC-2"
                    }
                },
                "active": "1",
                "standby": "1",
                "applications": {
                    "lsb1": {
                        "service_name": "httpd_error",
                        "packages": {
                            "nano": {
                                "name": "nano",
                                "repository": "products"
                            },
                        },
                        "type": "service-base",
                        "cleanup_command": "/bin/true"
                    }
                  }
                }
            }
        cmw_cluster_manager = cmwClusterManager(primary_node, nodes, services)
        #cmw_cluster_manager.soft_mgr.check_rpms(pkgs_dict, os_pkgs, nodes)
        cmwCampaignHelper._validate_lsb_service(services, "cs1", nodes,
                                                        cmw_cluster_manager)
        self.assertRaises(Exception, cmwCampaignHelper._validate_lsb_service,
                          services, "cs2", nodes, cmw_cluster_manager)

    @mock.patch('cmwplugin.campaign.cmw_software_manager.cmwSoftwareManager.get_rpm_path',
                mock.Mock(side_effect=_get_rpm_path_SE))
    @mock.patch('cmwplugin.campaign.cmw_software_manager.cmwSoftwareManager.get_sdp',
                mock.Mock(side_effect=_get_sdp_SE))
    @mock.patch('cmwplugin.campaign.cmw_software.RpmInfo.get_rpm_install_files',
                mock.Mock(side_effect=_get_rpm_install_files))
#    @mock.patch('cmwplugin.execution.execute',
#                mock.Mock(side_effect=_execute_SE_n))
    def test_create_configuration(self):
        self.setup_model()
        self._add_service_to_model("1", "cs")
        self._add_service_to_model("2", "cs")
        tasks = cmwCampaignHelper().create_configuration(CMWPlugin(),
                                                         self.context_api)
        self.assertEqual(len(tasks), 6)
        #self.assert_(False, "buya")

    def test_sort_dependency_order_positive(self):
        # no negative equivalent for this because there's validation
        self.setup_model()
        self._add_service_to_model("1", "cs")
        self._add_service_to_model("2", "cs")
        self._update_item_in_model(
                       "/deployments/test/clusters/cluster1/services/service1",
                       dependency_list="service2"
                       )
        sgs_dict = cmwModelManager(self.context_api).fromApi()
        ord_list = cmwCampaignHelper()._sort_dependency_order(sgs_dict)
        self.assertEqual(ord_list, ['service2', 'service1'])

#    def test_create_config(self):
#        self.setup_model()
#        self._add_service_to_model(1, name="httpd")
#        tasks = cmwCampaignHelper().create_configuration(CMWPlugin(),
#                                                         self.context_api)
##        self.assertNotEqual(len(tasks), 0)


class MockModel(object):
    """
    Stub class for testing the campaign validator.
    """

    @property
    def clusters(self):
        return [mock.Mock(), mock.Mock()]

    @property
    def _iter_services(self):
        return [
            mock.Mock(standby=1, active=1, node_list='foo,bar',
                      applications=[]),
            mock.Mock(standby=0, active=2, node_list='foo',
                      dependency_list='foo,bar', applications=[1]),
            mock.Mock(standby=0, active=3, node_list='foo,bar,bill',
                      dependency_list='', applications=[1, 2, 3]),
        ]

    @property
    def _iter_applications(self):
        # GRRR we need this as name is reserved in mock.
        app1 = mock.Mock()
        app1.service_name = 'foo'
        app2 = mock.Mock()
        app2.service_name = 'foo'
        app3 = mock.Mock()
        app3.name = 'bar'
        return [
            app1,
            app2,
            app3,
        ]


class TestCMWCampaignValidator(unittest.TestCase):
    """
    TestCase for the CMWCampaignValidator.
    """
    def setUp(self):
        self.null_validator = CMWCampaignValidator(mock.Mock(clusters=[]))
        self.validator = CMWCampaignValidator(MockModel())

    def test_no_clusters_no_errors(self):
        self.assertEqual([], self.null_validator.validate_model())

    def test_validate_cluster_count(self):
        self.assertEqual(
            1, len(list(self.validator.validate_cluster_count())))
        self.assertEqual(
            0, len(list(self.validator.validate_cluster_count(n=2))))

    def test_validate_only_nway_active(self):
        self.assertEqual(
            1, len(list(self.validator.validate_only_nway_active())))

    #==========================================================================
    # def test_validate_node_count(self):
    #     self.assertEqual(
    #         1, len(list(self.validator.validate_node_count())))
    #==========================================================================

    def test_validate_service_name_unique(self):
        self.assertEqual(
            1, len(list(self.validator.validate_service_name_unique())))

    def test_dependencies_only_in_failover(self):
        self.assertEqual(
            1,
            len(list(self.validator.validate_dependencies_only_in_failover())))

    def test_service_has_applications(self):
        self.assertEqual(
            1,
            len(list(self.validator.validate_service_has_applications())))
