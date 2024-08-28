##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################
'''
Provides decorators for Plugin classes and their helper classes so the helper
classes may use CallbackTasks directly.
CallbackTasks in the helper classes must be created through the
create_callback_task factory method and not instantiated directly.
'''

import sys
import hashlib
from litp.core.execution_manager import CallbackTask


def create_md5(filepath):
    file_data = open(filepath)
    md5 = hashlib.md5()
    while True:
        # 8192 bytes at a time (allegedly the most efficient)
        line = file_data.read(8192)
        if not line:
            break
        md5.update(line)
    return md5


def patch_plugin_callback(clazz):
    '''
    Adds __callback__ utility function to plugin to allow callbacks
    from helper classes to be called directly
    '''
    def __callback__(self, callback_api, *args,
                     **kwargs):  # pylint: disable=W0613
        module_name = kwargs["__module_name__"]
        class_name = kwargs["__class_name__"]
        function_name = kwargs["__function_name__"]
        del kwargs["__function_name__"]
        del kwargs["__module_name__"]
        del kwargs["__class_name__"]
        current_module = sys.modules[module_name]
        clazz = getattr(current_module, class_name)
        getattr(clazz, function_name)(callback_api, *args, **kwargs)
    clazz.__callback__ = __callback__
    return clazz


def patch_helper_callback(clazz):
    '''
    Adds _create_callback_task method that produces a CallbackTask that uses
    the __callback__ method as a proxy to the passed helper function
    '''
    def _create_callback_task(self, plugin, model_item, description, function,
                              *cargs, **kwargs):
        kwargs["__module_name__"] = self.__module__
        kwargs["__class_name__"] = self.__class__.__name__
        kwargs["__function_name__"] = function.__name__
        cargs = (model_item,
                 description,
                 plugin.__callback__) + cargs
        return CallbackTask(*cargs, **kwargs)
    clazz.create_callback_task = _create_callback_task
    return clazz


def valid_cluster_nodes(cluster):
    nodes = [node for node in cluster.nodes if not node.is_for_removal()]
    return nodes
