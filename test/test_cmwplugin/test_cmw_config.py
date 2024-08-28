##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################
import tempfile
import unittest
from cmwplugin.campaign.cmw_config import cmwConfig


class TestcmwConfig(unittest.TestCase):

    def setUp(self):
        rt, temp = tempfile.mkstemp()
        self.config = cmwConfig(config_file=temp)
        self.config.config.add_section("test_section")
        with open(self.config.config_file, 'wb') as configfile:
                self.config.config.write(configfile)

    def test_read_plugin_config(self):
        self.assertEqual(None, self.config.read_plugin_config("test_section", "test_item"))
        self.assertRaises(Exception, self.config.read_plugin_config, "test_", "test_item")

    def test_write_plugin_config(self):
        #print self.config.config_file
        self.config.write_plugin_config("test_section", "test_item", "test_value")
        self.assertEqual("test_value", self.config.read_plugin_config("test_section", "test_item"))

    def test_negative_config(self):
        import os
        try:
            os.remove("/tmp/bla94832943")
        except:
            pass
        self.config.config_file = "/tmp/bla94832943"
        self.assertRaises(Exception, self.config.read_plugin_config, "test_section", "test_item")
        conf = cmwConfig()
        self.assertRaises(Exception, conf.read_plugin_config, "test_section", "test_item")
        self.assertRaises(Exception, self.config.write_plugin_config, "test_s", "test_item", "test_value")