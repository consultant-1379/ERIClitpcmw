import unittest
import mock
from cmwplugin.utils import patch_plugin_callback, patch_helper_callback


class B(object):
    @staticmethod
    def callback(arg1, kwarg1=None):
        pass


class TestUtils(unittest.TestCase):

    @mock.patch('cmwplugin.utils.CallbackTask')
    @mock.patch('litp.core.plugin.Plugin')
    def test_create_callback_task(self, MockPlugin, MockTask):
        @patch_helper_callback
        class A(object):
            @staticmethod
            def callback(arg1, kwarg1=None):
                pass
        plugin = MockPlugin()
        plugin.__callback__ = mock.Mock()
        model_item = mock.Mock()
        A().create_callback_task(plugin, model_item, "hello",
                                 A.callback, "hello",
                                 kwarg1="hello")
        MockTask.assert_called_with(model_item, "hello", plugin.__callback__,
                                    "hello", __class_name__='A',
                                    __function_name__='callback',
                                    __module_name__=self.__module__,
                                    kwarg1='hello')

    @mock.patch('litp.core.plugin.Plugin')
    @mock.patch('test_cmwplugin.test_utils.B')
    def test_callback_task(self, MockPlugin, MockB):
        return

        @patch_plugin_callback
        class A(object):
            pass

        plugin = MockPlugin()
        plugin.__callback__ = mock.Mock()
        api = mock.Mock()
        args = ('hello',)
        kwargs = {"kwargs1": "hello",
                  "__module_name__": B.__module__,
                  "__class_name__": B.__class__.__name__,
                  "__function_name__": B.callback._mock_name}

        A().__callback__(api, *args, **kwargs)
