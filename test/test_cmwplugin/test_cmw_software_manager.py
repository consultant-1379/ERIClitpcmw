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
from mock import Mock, patch

from cmwplugin.campaign.cmw_software_manager import cmwSoftwareManager

class TestcmwSoftwareManager(unittest.TestCase):

    def setUp(self):
        self.cmw_software_manager = cmwSoftwareManager()

    def test_generate_jboss_env(self):
        active = 2
        app = 'sg1_App'
        service_name = 'sg1'
        jee_container_name = 'jee_container1'
        f_mock = Mock(['seek', 'truncate', 'write', 'close'])

        expected_return = [
            'sg1_jee_container1.sg1_App-SuType-0.sg1.sg1_App.env', 
            'sg1_jee_container1.sg1_App-SuType-1.sg1.sg1_App.env']

        with patch ('litp.core.litp_logging.LitpLogger') as log_mock:
            with patch('__builtin__.open') as open_mock:
                with patch('cmwplugin.campaign.cmw_software_manager.os.path') \
                    as os_path_mock:
                    open_mock.return_value = f_mock
                    os_path_mock.exists.return_value = True
                    jboss_env_file_names = \
                        self.cmw_software_manager._generate_jboss_env(active, \
                        app, service_name, jee_container_name)

        # Check last line called by the write command
        expected_written = \
            "LITP_JEE_CONTAINER_post_start=\"" \
            "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/post_start.d\"\n"

        self.assertEquals(jboss_env_file_names, expected_return)
        f_mock.write.assert_called_with(expected_written)
        self.assertEquals(open_mock.call_count, 2)
        self.assertEquals(f_mock.seek.call_count, 2)
        self.assertEquals(f_mock.truncate.call_count, 2)
        self.assertEquals(f_mock.write.call_count, 92)
        self.assertEquals(f_mock.close.call_count, 2)
