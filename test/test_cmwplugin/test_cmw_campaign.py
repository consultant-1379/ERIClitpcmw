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

from cmwplugin.campaign.cmw_campaign import cmwCampaignGenerator, cmwCampaign
from cmwplugin.campaign.cmw_cluster_manager import cmwClusterManager
from cmwplugin.campaign.cmw_software import cmwBundle

from .base_cmw_integration import CmwIntegrationBase


def test_cmw_campaign():
    """Test `cmwCampaign` summary class attributes.
    """
    campaign = cmwCampaign('name', 'bundles')
    assert campaign.bundles == 'bundles'
    assert campaign.campaign_name == 'name'
    assert campaign.type is None
    assert campaign.sg is None
    campaign = cmwCampaign('name', 'bundles', sg='sg')
    assert campaign.bundles == 'bundles'
    assert campaign.campaign_name == 'name'
    assert campaign.type is None
    assert campaign.sg == 'sg'


class TestcmwCampaignGenerator(unittest.TestCase):
    """
    Test `cmwCampaignGenerator` class.
    """
    def setUp(self):
        self.generator = cmwCampaignGenerator()

    def test_get_nonamf_campaign_name(self):
        self.assertEquals(
            '3PP-FOO_SMFInstall',
            self.generator._get_nonamf_campaign_name('FOO'))

    def test_get_install_campaign_name(self):
        self.assertEquals(
            '3PP-FOO_Install',
            self.generator._get_install_campaign_name('FOO'))

    @mock.patch('cmwplugin.campaign.cmw_campaign.datetime')
    def test_get_upgrade_campaign_name(self, mock_dt):
        now = mock.Mock()
        now.strftime.return_value = 'foo'
        mock_dt.now.return_value = now
        self.assertEquals(
            'base_Upgrade_foo',
            self.generator._get_upgrade_campaign_name('base'))


def _get_rpm_path_SE(rpm_info):
    return "/tmp/test.rpm"


def _get_jee_install_source():
    return "/tmp/jee.tgz"


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

    #==========================================================================
    # @mock.patch('cmwplugin.campaign.cmw_software_manager.cmwSoftwareManager.get_rpm_path',
    #             mock.Mock(side_effect=_get_rpm_path_SE))
    # @mock.patch('cmwplugin.campaign.cmw_software_manager.cmwSoftwareManager.get_sdp',
    #             mock.Mock(side_effect=_get_sdp_SE))
    # @mock.patch('cmwplugin.campaign.cmw_software.RpmInfo.get_rpm_install_files',
    #             mock.Mock(side_effect=_get_rpm_install_files))
    # @mock.patch('cmwplugin.execution.execute',
    #             mock.Mock(side_effect=_execute_SE_n))
    # def test_generate_install(self):
    #     #--------------------------------------------------- self.setup_model()
    #     #---------------------------------------- self._add_service_to_model(1)
    #     primary_node = "mn1"
    #     nodes = ["mn2", "mn1"]
    #     services = {
    #         "cs1": {
    #             "dependencies": {},
    #             "nodes": {
    #                 "node1": {
    #                     "amf-name": "PL-3"
    #                 },
    #                 "node2": {
    #                     "amf-name": "PL-4"
    #                 }
    #             },
    #             "active": "1",
    #             "standby": "1",
    #             "runtimes": {
    #                 "lsb_runtime1": {
    #                     "service_name": "httpd",
    #                     "name": "lsb_runtime",
    #                     "packages": {
    #                         "nano": {
    #                             "name": "nano",
    #                             "repository": "products"
    #                         },
    #                     },
    #                     "type": "lsb-runtime",
    #                     "cleanup_command": "/bin/true"
    #                 }
    #               }
    #             },
    #             "cs2": {
    #             "dependencies": {"cs2": {"name": "cs1"}},
    #             "nodes": {
    #                 "node1": {
    #                     "amf-name": "SC-1"
    #                 },
    #                 "node2": {
    #                     "amf-name": "SC-2"
    #                 }
    #             },
    #             "active": "1",
    #             "standby": "1",
    #             "runtimes": {
    #                 "lsb_runtime1": {
    #                     "service_name": "httpd_error",
    #                     "name": "lsb_runtime",
    #                     "packages": {
    #                         "nano": {
    #                             "name": "nano",
    #                             "repository": "products"
    #                         },
    #                     },
    #                     "type": "lsb-runtime",
    #                     "cleanup_command": "/bin/true"
    #                 }
    #               }
    #             }
    #         }
    #     cmw_cluster_manager = cmwClusterManager(primary_node, nodes, services)
    #     #clus_mgr = cmw_cluster_manager.cmwClusterManager(primary_node, nodes, services)
    #     sg = cmw_cluster_manager.apps[0].service_groups[0]
    #     cmw_camp_gen = cmwCampaignGenerator()
    #     camp_name = cmw_camp_gen._get_install_campaign_name(sg.name)
    #     camp = cmw_camp_gen.generate_install(sg, camp_name)
    #==========================================================================
