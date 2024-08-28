##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import copy
import itertools
import os

from cmwplugin.campaign.cmw_cluster_manager import cmwClusterManager
from cmwplugin.campaign.cmw_software_manager import cmwSoftwareManager
from cmwplugin.campaign.cmw_model_manager import cmwModelManager
from cmwplugin.execution import patch_callback
from cmwplugin.utils import (patch_helper_callback,
                             valid_cluster_nodes)
from litp.core.execution_manager import ConfigTask
from litp.core.litp_logging import LitpLogger
from litp.core.validators import ValidationError
from cmwplugin.campaign.cmw_software import RpmInfo


log = LitpLogger()


class CMWModel(object):
    """
    class for abstraction of CMW items in LITP model.
    """
    def __init__(self, plugin_api_context):
        self.api = plugin_api_context

    @property
    def nodes(self):
        """
        Return all nodes in deployment.
        """
        return self.api.query('node')

    @property
    def clusters(self):
        """
        Return all cmw-clusters.
        """
        return self.api.query('cmw-cluster')

    @property
    def _iter_services(self):
        """
        Generator method for services in a group of cmw clusters.
        """
        for cluster in self.clusters:
            for service in cluster.query('cmw-clustered-service'):
                yield service

    @property
    def _iter_applications(self):
        """
        Generator method for applications in a group of cmw clusters.
        """
        for service in self._iter_services:
            for application in service.applications:
                yield application


class CMWCampaignValidator(object):
    """
    Class containing all validation methods for a
    cmw-clustered-service.
    """

    def __init__(self, cmw_model):
        # Implement strategy design pattern to account for model changes.
        self.model = cmw_model

    def __getattr__(self, attr):
        """
        Delegate any attributes not defined on this class to `self.model`.
        """
        return getattr(self.model, attr)

    def validate_model(self):
        """
        Validation checks for CMW clusters.
        """
        # If we have no cmw-clusters we don't validate.
        if not self.clusters:
            return []

        return list(itertools.ifilter(bool, itertools.chain(
            self.validate_cluster_count(),
            self.validate_only_nway_active(),
            self.validate_node_count(),
            self.validate_service_has_applications(),
            self.validate_service_name_unique(),
            self.validate_no_os_packages(),
            self.validate_dependencies_only_in_failover(),
            self.validate_no_circular_dependencies(),
            self.validate_clustered_service_uniquely_named(),
            self.validate_nodes_exist()
        )))

    def validate_clustered_service_uniquely_named(self):
        seen_names = set()
        for service in self._iter_services:
            if service.name in seen_names:
                yield ValidationError(
                    service.get_vpath(),
                    error_message="Clustered service names should be unique "
                    "in a cluster")
            seen_names.add(service.name)

    def validate_nodes_exist(self):
        """
        Validate that nodes from `node_list` exist in model.
        """
        node_ids = [node.item_id for node in self.nodes]
        print self.nodes
        for service in self._iter_services:
            for node_id in service.node_list.split(','):
                if node_id not in node_ids:
                    yield ValidationError(
                        service.get_vpath(),
                        error_message='Node: %s is not in the deployment' %
                            node_id)

    def validate_cluster_count(self, n=1):
        """
        Validate that only `n` number of clusters are defined.
        """
        if len(self.clusters) > n:
            yield ValidationError(
                self.clusters[0].get_vpath(),
                error_message="Only %s cluster should be defined" % n)

    def validate_only_nway_active(self):
        """
        Validates there are no standby nodes for a service.
        """
        for service in self._iter_services:
            if int(service.standby) > 0:
                yield ValidationError(
                    service.get_vpath(),
                    error_message="Only NWAY-ACTIVE services supported")

    def validate_service_has_applications(self):
        """
        Validate a cmw-clustered-service has at least one application
        """
        for service in self._iter_services:
            # TODO: Look at why `len` needed.
            if not len(service.applications):
                yield ValidationError(
                    service.get_vpath(),
                    error_message="Clustered service using CMW must "
                                  "contain an application")

    def validate_node_count(self):
        """
        Check that each `cmw-clustered-service` contains enough nodes.
        """
        for service in self._iter_services:
            required_nodes = int(service.active) + int(service.standby)
            if len(service.node_list.split(',')) != required_nodes:
                yield ValidationError(
                    service.get_vpath(),
                    error_message="Active and standby count do not match "
                                  "node_list count.")

    def validate_no_os_packages(self):
        """
        Validate that no packages attached to an application or from the OS
        repo.
        """
        for application in self._iter_applications:
            for package in application.packages:
                if (package.repository == 'OS' or
                        cmwSoftwareManager.is_os_package(package.name)):
                    yield ValidationError(
                        application.get_vpath(),
                        error_message="OS packages not supported in "
                                      "cmw-clustered-service")

    def validate_service_name_unique(self):
        """
        Validate that each application in a `cmw-clustered-service` is
        uniquely named.
        """
        seen_names = set()
        for application in self._iter_applications:
            if application.service_name in seen_names:
                yield ValidationError(
                    application.get_vpath(),
                    error_message="Application 'service_name' should be unique"
                                  " within a cluster.")
            seen_names.add(application.service_name)

    def validate_dependencies_only_in_failover(self):
        """
        Validate that only failover services have dependencies.
        """
        for service in self._iter_services:
            if int(service.standby) == 0 and service.dependency_list:
                yield ValidationError(
                    service.get_vpath(),
                    error_message="Dependencies can only be set for 2N "
                                  "services")

    def validate_no_circular_dependencies(self):
        """
        Validate there are no circular dependencies on cmw services.
        """
        for cluster in self.clusters:
            for error in _validate_no_circular_dependencies(cluster):
                yield error


@patch_helper_callback
class cmwCampaignHelper(object):
    """
    Main class for interfacing with the plugin
    """

    def validate_model(self, plugin_api_context):
        validator = CMWCampaignValidator(CMWModel(plugin_api_context))
        return validator.validate_model()

    @staticmethod
    def _validate_lsb_service(services, cs_name, nodes, cmw_clus_mgr):
        """
        :summary: Validate scripts are present

        :param si_obj: ServiceUnit object to validate
        :type si_obj: LitpItem ? XXX
        """
        for service in services[cs_name]["applications"]:
            # XXX assuming 1 runtime
            lsb_dict = services[cs_name]["applications"][service]

            found = False
            cleanup_found = False
            cleanup_command = lsb_dict["cleanup_command"]
            cleanup_command = cleanup_command.split(" ")[0]

            pkgs_dict = lsb_dict["packages"].values()
            svc_name = lsb_dict["service_name"]
            svc_path_1 = os.path.join("/etc/rc.d/init.d/", svc_name)
            svc_path_2 = os.path.join("/etc/init.d/", svc_name)
            for pkg in pkgs_dict:

                pkg_path = cmw_clus_mgr.soft_mgr.get_rpm_path(pkg)

                file_list = RpmInfo.get_rpm_install_files(pkg_path)
                # FIXME: hardcoding the service path for rhel, check other
                # services for the right location
                if svc_path_1 in file_list or svc_path_2 in file_list:
                    found = True
                if cleanup_command in file_list:
                    cleanup_found = True

            if not found:
                found = cmw_clus_mgr.cmw_exec_mgr.check_if_file_on_node(
                                                                    svc_path_1,
                                                                    nodes)
            if not found:
                found = cmw_clus_mgr.cmw_exec_mgr.check_if_file_on_node(
                                                                    svc_path_2,
                                                                    nodes)
            if not cleanup_found:
                cleanup_found = \
                            cmw_clus_mgr.cmw_exec_mgr.check_if_file_on_node(
                                                            cleanup_command,
                                                                nodes)
            if not found:
                raise Exception("Service name '%s' not found in any pkg or "
                                 "node for %s" % (svc_name, service))
            if not cleanup_found:
                if not cleanup_found:
                    raise Exception("cleanup_command '%s' not found in any pkg"
                    " or Node for %s " % (cleanup_command, service))

    def _clean_services(self, services, cs, pkg_list):
        services_clean = copy.deepcopy(services)
        for app in services[cs]["applications"]:
            pkg_dict = services[cs]["applications"][app]["packages"]
            for pkg in pkg_dict:
                if pkg_dict[pkg]["name"] in pkg_list:
                    del \
                services_clean[cs]["applications"][app]["packages"][pkg]
        return services_clean

    def _sort_dependency_order(self, sgs_dict):
        """
        :summary: Sorts dependency order between service groups
        and detects circular dependencies.
        """
        final_list = list()
        deps_dict = dict()

        for sg_name in sgs_dict:
            if sgs_dict[sg_name]["dependencies"]:
                deps_dict[sg_name] = []
                for dep_id in sgs_dict[sg_name]["dependencies"].keys():
                    deps_dict[sg_name].append(dep_id)
                    log.trace.debug('SG %s has dependency on ' % dep_id)
            else:
                log.trace.debug('Adding SG %s to the final list' % sg_name)
                final_list.append(sg_name)

        max_iter = len(deps_dict.keys())
        count = 0
        while deps_dict:
            _tmp = copy.deepcopy(deps_dict)
            for sg_name in _tmp.keys():
                deps = set(_tmp[sg_name])
                if deps == deps.intersection(final_list):
                    final_list.append(sg_name)
                    del deps_dict[sg_name]
            if count >= max_iter:
                error_msg = ("Unable to resolve dependencies for [{0}]. "
                             "This might be caused by a circular dependency")
                error_msg = error_msg.format(', '.join(
                                        [x for x in deps_dict]))
                log.trace.error(error_msg)
                raise Exception(error_msg)
            count += 1
        log.trace.debug("Dependency order sorted: {0}".format(final_list))

        return final_list

    def create_configuration(self, plugin, plugin_api_context):
        """
        Creates configuration in form of ConfigTask for all nodes in any
        CMW cluster that is in initial state
        Returns a list of ConfigTasks/CallbackTasks
        Will do same checks as validate_model and throw RuntimeErrors for all
        failures
        """
        tasks = []

        cmw_mm = cmwModelManager(plugin_api_context)
        clusters = plugin_api_context.query("cmw-cluster")
        if not clusters:
            return tasks
        cluster = clusters[0]

        cluster_nodes = valid_cluster_nodes(cluster)
        for node in cluster_nodes:
            if node.is_initial():
                tasks.append(ConfigTask(
                            node,
                            node,
                            "Install LITP CMW helper script",
                            "cmw::agent_install",
                            "agent_install"
                        ))
        initial_cs = cmw_mm.initial_clustered_services()

        if not initial_cs:
            return tasks
        #raise Exception()
        initial_cs = [cs.item_id for cs in initial_cs]

        hostnames = [node.hostname for node in cluster_nodes]
        # TODO loop through clusters
        primary_node = cmw_mm.find_primary_node(cluster)
        if primary_node is None:
            raise RuntimeError("No node specified with id 1")

        services = cmw_mm.fromApi()
        order_list = self._sort_dependency_order(services)

        ms_ipaddr = cmw_mm._get_ms_ip_for_internal_network(cluster)

        initial_cs_ordered = []
        for cs_name in order_list:
            if cs_name in initial_cs:
                initial_cs_ordered.append(cs_name)
        for cs_name in initial_cs_ordered:
            svc_dict = cmw_mm.fromApi(cs_name)

            # FIXME, move this logic for package selection to model_manager
            packages = cmw_mm.packages_for_clustered_service(cs_name)
            pkg_list = []
            if packages:
                pkg_list = [pkg.name for pkg in packages \
                            if cmwSoftwareManager.is_os_package(pkg.name)]
            # NEED to clean first to avoid inconsistent data to arrive to
            # another clustered service callback
            svc_dict_clean = self._clean_services(svc_dict, cs_name, pkg_list)

            if pkg_list:
                for node in cluster_nodes:
                    tasks.append(ConfigTask(
                            node,
                            node,
                            ("Install packages: {0} , for clustered-"
                             "service {1}".format(str(", ".join(pkg_list)),
                                                  cs_name)),
                            "cmw::install_package",
                            "install_package_%s" % "_".join(pkg_list),
                            packages=pkg_list
                        ))

            svc = plugin_api_context.query("clustered-service",
                                           item_id=cs_name)[0]
            #pylint: disable=E1101
            tasks.append(
                self.create_callback_task(plugin,
                                  svc,
                                  ("Pre-check task for clustered service %s")
                                         % cs_name,
                                  self._pre_check,
                                  primary_node=primary_node.hostname,
                                  nodes=hostnames,
                                  services=svc_dict_clean,
                                  cs_name=cs_name,
                                  os_pkgs=pkg_list
                                  )
            )
            tasks.append(
                self.create_callback_task(plugin,
                                  svc,
                                  "Install clustered services %s" % cs_name,
                                  self._install,
                                  primary_node=primary_node.hostname,
                                  nodes=hostnames,
                                  services=svc_dict_clean,
                                  ms_ip=ms_ipaddr
                                  )
            )
            #pylint: enable=E1101

        return tasks

    @staticmethod
    @patch_callback
    def _pre_check(dummy_callback_api, primary_node, nodes, services, \
                                                            cs_name, os_pkgs):
        # FIXME: Check what parameters are really needed
        pkgs_dict = dict()
        for app in services[cs_name]["applications"]:
            pkgs_dict = \
                services[cs_name]["applications"][app]["packages"].values()
        cmw_cluster_manager = cmwClusterManager(primary_node, nodes, services)
        cmw_cluster_manager.soft_mgr.check_rpms(pkgs_dict, os_pkgs, nodes)
        cmwCampaignHelper._validate_lsb_service(services, cs_name, nodes,
                                                        cmw_cluster_manager)

    @staticmethod
    @patch_callback
    def _install(dummy_callback_api, primary_node, nodes, services, ms_ip):
        '''
        Callback function for CMW installation. Calls a series of subtasks.
        '''
        # FIXME: Check what parameters are really needed
        log.event.info("Installing clustered service")

        log.event.info(primary_node)
        dummy_data = {
            "cs1": {
                "dependencies": {"cs2": {}},
                "nodes": {
                    "node1": {
                        "amf-name": "SC-1"
                    },
                    "node2": {
                        "amf-name": "SC-2"
                    }
                },
                "active": 1,
                "standby": 1,
                "applications": {
                    "lsb_service1": {
                        "service_name": "httpd",
                        "packages": {
                            "nano": {
                                "name": "nano",
                                "repository": "OS"
                            },
                          #-------------------------------------------------- {
                            #--------------------------- "name": "mod_cluster",
                            #------------------------- "repository": "Products"
                          #-------------------------------------------------- }
                        },
                        "type": "service",
                        "cleanup_command": "/bin/true"
                    }
                  }
                },
                "cs2": {
                    "dependencies": {},
                    "nodes": {
                        "node1": {
                            "amf-name": "SC-1"
                        },
                        "node2": {
                            "amf-name": "SC-2"
                        }
                    },
                    "active": 1,
                    "standby": 1,
                    "s": {
                      "lsb_runtime1": {
                        "service_name": "qpidd",
                          "packages": {
                              "zip":
                              {
                                "name": "zip",
                                "repository": "OS"
                              },
                          #-------------------------------------------------- {
                            #--------------------------- "name": "mod_cluster",
                            #------------------------- "repository": "Products"
                          #-------------------------------------------------- }
                          },
                        "type": "service",
                        "cleanup_command": "/bin/true"
                      }
                    }
                  }
                }

        cmw_cluster_manager = cmwClusterManager(primary_node, nodes, services)
        cmw_cluster_manager.generate_campaigns()
        cmw_cluster_manager.execute_campaigns(primary_node, ms_ip)


class CircularDependency(Exception):
    pass


def _circular_path(graph, start, path):
    if start in path:
        raise CircularDependency("")
    else:
        path.append(start)
    for dep in graph[start]:
        if dep in path:
            raise CircularDependency("")
        _circular_path(graph, dep, path)


def _validate_no_circular_dependencies(cluster):
    errors = []
    graph = {}
    for service in cluster.services:
        if not service.item_id in graph:
            graph[service.item_id] = []
        for dep in service.dependencies:
            graph[service.item_id].append(dep.item_id)
    try:
        for service in graph:
            _circular_path(graph, service, [])
    except CircularDependency:
        errors.append(
            ValidationError(
                cluster.get_vpath(),
                error_message="Circular dependency in clustered services"))
    return errors
