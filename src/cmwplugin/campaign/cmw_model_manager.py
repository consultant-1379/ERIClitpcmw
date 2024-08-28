##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.litp_logging import LitpLogger
from litp.core.model_item import RefCollectionItem, CollectionItem
from cmwplugin.utils import valid_cluster_nodes
log = LitpLogger()
#from nose.tools import set_trace


class cmwModelManager(object):

    def __init__(self, context_api):
        self.context_api = context_api
        self.__services__ = {}
        self.__node_tags__ = {}

    def fromApi(self, cs_name=None):
        deployments = self.context_api.query("cmw-cluster")
        #print deployments[0].query("node", node_id=1)
        #set_trace()
        cluster = deployments[0]
        valid_nodes = valid_cluster_nodes(cluster)
        nodes = sorted(valid_nodes, key=lambda node: node.node_id)
        i = 1
        for node in nodes:
            if i < 3:
                self.__node_tags__[node.node_id] = "SC-%d" % i
            else:
                self.__node_tags__[node.node_id] = "PL-%d" % i
            i += 1
        #print nodes
        if cs_name:
            for service in deployments[0].services:
                if cs_name == service.item_id:
                    #self.__services__[service.name] = self._parse(service)
                    return {service.item_id: self._parse(service)}
        else:
            for service in deployments[0].services:
                self.__services__[service.item_id] = self._parse(service)
            return self.__services__

    def _query(self, item_type_id, **properties):
        return self.context_api.query(item_type_id, **properties)

    def find_primary_node(self, cluster):
        for node in cluster.query("node"):
            if node.node_id == "1":
                return node
        return None

    def initial_clustered_services(self):
        ret = []
        cs_list = self._query("cmw-clustered-service")
        for cs in cs_list:
            if cs.is_initial():
                ret.append(cs)
        return ret

    def nodes_for_clustered_service(self, cs_name):
        services = self._query("cmw-clustered-service", item_id=cs_name)
        if not services:
            return None
        return services[0].nodes

    def packages_for_clustered_service(self, cs_name):
        services = self._query("cmw-clustered-service", item_id=cs_name)
        if not services:
            return None
        apps = services[0].applications
        for app in apps:
            return app.packages
        return None
    #==========================================================================
    # def _query(self, _item, item_type, **kwargs):
    #     result = []
    #     for item in _item:
    #         if item.item_type == item_type:
    #             result.append(item)
    #         children = [x for x in item.values() if type(x) is ModelItem]
    #         result.extend(self._query(children, item_type, **kwargs))
    #     return result
    #==========================================================================

    def _parse(self, item):
        item_dict = {}
        if not type(item._model_item) in [RefCollectionItem, CollectionItem]:
            item_dict["type"] = item.item_type_id
            #print item
            for key in item.properties.keys():
                if hasattr(item, key):
                    value = getattr(item, key)
                    if callable(item.properties[key]):
                        if type(value) == list:
                            tmp_dict = {}
                            for x in value:
                                tmp_dict[x.item_id] = self._parse(x)
                            value = tmp_dict
                    item_dict[key] = value

#            item_dict["status"] = item.status
#            item_dict["is_ref"] = not item._ref is None
        if item.is_node():
            item_dict["amf-name"] = self.__node_tags__[item.node_id]
        if type(item._children) is dict:
            children = item._children.keys()
        else:
            children = item._children().keys()
        #print item.item_id, children
        for child in children:
            child_item = getattr(item, child)
            item_dict[child] = self._parse(child_item)
        return item_dict

    def _get_ms_ip_for_internal_network(self, cluster):
        ms = self.context_api.query('ms')[0]
        for iface in ms.network_interfaces:
            if iface.network_name == cluster.internal_network:
                return iface.ipaddress
