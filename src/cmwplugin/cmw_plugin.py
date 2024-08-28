##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.plugin import Plugin
from litp.core.litp_logging import LitpLogger
from litp.core.task import OrderedTaskList
from cmwplugin.ldeinstaller import LdeInstaller
from cmwplugin.cmwinstaller import (CmwInstaller,
                                    create_ssh_config_tasks,
                                    create_amf_cgs_install_tasks,
                                    find_initial_cmw_clusters,
                                    validate_model_for_amf_cgs_install_tasks,
                                    create_ocf_resource_agents_install_tasks)
from cmwplugin.campaign_helper import cmwCampaignHelper
from cmwplugin.utils import patch_plugin_callback
log = LitpLogger()


@patch_plugin_callback
class CMWPlugin(Plugin):
    """
    LITP CMW plugin for CMW installation and configuration.
    """
    def __init__(self):
        super(CMWPlugin, self).__init__()
        self.lde_installer = LdeInstaller()

    def validate_model(self, plugin_api_context):
        """
        Validate that:

        - there are at least two nodes in the cluster
        - which nodes have missing, bad or duplicated node_ids
        - each node in the cluster has an IP address on the management network
        - cluster nodes have a file-system  mounted to /cluster
        - all nodes in the clusters have configured interfaces on all
          heartbeat networks
        - only one CMW cluster should be defined
        - there is no circular dependency in clustered services
        - all clustered service names should be unique within the cluster
        - clustered services using CMW must contain a runtime
        - only one runtime should be defined per CMW clustered service
        - only 2N reduncancy is supported for lsb-runtime
        - service names in the lsb-runtime should be unique
        - only N-way Active redundancy is supported for JEE container
        """
        errors = []
        for cluster in find_initial_cmw_clusters(plugin_api_context):
            errors += self.lde_installer.validate_model(cluster)

        errors += cmwCampaignHelper().validate_model(plugin_api_context)
        errors += validate_model_for_amf_cgs_install_tasks(plugin_api_context)
        return errors

    def create_configuration(self, plugin_api_context):
        """
        Provides support for the addition, update and removal
        of cmw-manager model items.
        Creating a deployment model with a cmw-manager in the cluster
        creates tasks to install and cofigure LDE and CMW.

        *Example CLI for this plugin :**

        .. code-block:: bash

            litp create -p /deployments/test -t deployment
            litp create -t cmw-cluster    -p /deployments/test/clusters/ \
            cmw_cluster -o cluster_id=2 tipc_networks="hb1,hb2" \
            internal_network="mgmt"

        .. code-block:: bash

        """
        tasks = []
        clusters = find_initial_cmw_clusters(plugin_api_context)
        if clusters:
            tasks += create_ssh_config_tasks(plugin_api_context)
            tasks += create_amf_cgs_install_tasks(plugin_api_context)
            tasks += create_ocf_resource_agents_install_tasks(
                plugin_api_context)
            for cluster in clusters:
                cluster_tasks = []
                conf_tasks, cb_tasks = self.lde_installer.create_configuration(
                    self, cluster, plugin_api_context)
                tasks += conf_tasks
                tasks += cb_tasks
                cluster_tasks += CmwInstaller().create_configuration(
                    plugin_api_context, self, cluster)
                if cluster_tasks and cb_tasks:
                    for t in cb_tasks:
                        cluster_tasks[0].requires.add(t)
                tasks.append(OrderedTaskList(cluster.software, cluster_tasks))
        tasks.extend(cmwCampaignHelper().create_configuration(self,
                                                          plugin_api_context))
        return tasks
