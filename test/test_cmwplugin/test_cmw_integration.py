##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from base_cmw_integration import CmwIntegrationBase
from cmwplugin.campaign.cmw_model_manager import cmwModelManager
from cmwplugin.campaign.cmw_cluster_manager import cmwClusterManager
from cmwplugin.campaign.cmw_entities import cmwNWayActiveServiceGroup,\
    cmw2NServiceGroup


class TestCMWPluginIntegration(CmwIntegrationBase):

    def setUp(self):
        super(TestCMWPluginIntegration, self).setUp()

    def test_validate_model(self):
        self.setup_model()
        errors = self.plugin.validate_model(self.context_api)
        print errors
        self.assertEqual(len(errors), 0)

    def test_create_configuration(self):
        self.setup_model()
        tasks = self.plugin.create_configuration(self.context_api)
        self.assertEqual(len(tasks), 14)

    #==========================================================================
    # def test_cmw_cluster_manager_jboss(self):
    #     self.setup_model()
    #     self._add_jboss_container_to_model("1", "cs")
    #     primary_node = "mn1"
    #     nodes = ["mn2", "mn1"]
    #     sgs_dict = cmwModelManager(self.context_api).fromApi()
    #     print sgs_dict
    #     cmw_cluster_manager = cmwClusterManager(primary_node, nodes, sgs_dict)
    #     self.assertTrue(cmw_cluster_manager.apps, "no service groups defined")
    #     for app in cmw_cluster_manager.apps:
    #         for sg in app.service_groups:
    #             self.assertTrue(isinstance(sg, cmwNWayActiveServiceGroup))
    #==========================================================================

    def test_cmw_cluster_manager_lsb(self):
        self.setup_model()
        self._add_service_to_model("1", "cs")
        primary_node = "mn1"
        nodes = ["mn2", "mn1"]
        sgs_dict = cmwModelManager(self.context_api).fromApi()
        print sgs_dict
        cmw_cluster_manager = cmwClusterManager(primary_node, nodes, sgs_dict)
        self.assertTrue(cmw_cluster_manager.apps, "no service groups defined")
        for app in cmw_cluster_manager.apps:
            for sg in app.service_groups:
                self.assertTrue(isinstance(sg, cmwNWayActiveServiceGroup))

    def test_cmw_cluster_manager_service(self):
        self.setup_model()
        self._add_service_to_model("1", "cs")
        self._update_item_in_model("/deployments/test/clusters/cluster1/"
                                   "services/service1/applications/lsb1",
                                   start_command="/bin/test")
        primary_node = "mn1"
        nodes = ["mn2", "mn1"]
        sgs_dict = cmwModelManager(self.context_api).fromApi()
        print sgs_dict
        cmw_cluster_manager = cmwClusterManager(primary_node, nodes, sgs_dict)
        self.assertTrue(cmw_cluster_manager.apps, "no service groups defined")
        for app in cmw_cluster_manager.apps:
            for sg in app.service_groups:
                for comp in sg.comps:
                    self.assertEqual(comp.start_command, "../bin/test")
