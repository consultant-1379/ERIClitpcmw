##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from cmwplugin.cmw_mco_api import CmwMcoApi
from cmwplugin.cmw_mco_api import CmwMcoApiException
import unittest
import mock
from mock import *
import os
import tempfile


class TestCmwCmdApi(unittest.TestCase):

    def setUp(self):
        self.csh = CmwMcoApi()
        self.csh.set_node("mn1")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_give_x_permission_fail(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "err": "Expected Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.give_x_permission,
                          "/tmp", "file,txt")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_give_x_permission_success(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.give_x_permission("/tmp", "file.txt")
        _call_mco.assert_called_once_with('cmw_utils',
                                          'give_file_execute_permission',
                                          {'path': '/tmp',
                                           'filename': 'file.txt'})

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_execute_script_fail(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "err": "Expected Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.execute_script,
                          "/tmp", "file,txt")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_execute_script_success(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.execute_script("/tmp", "file.txt")
        _call_mco.assert_called_once_with('cmw_utils',
                                          'execute_script',
                                          {'path': '/tmp',
                                           'script_name': 'file.txt'},
                                          timeout=600)

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_check_file_doesnt_exist(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "err": "Expected Error"}
        file_exists = self.csh.check_file_exists("/tmp", "file.txt")
        self.assertEquals(file_exists, False)

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_check_file_does_exist(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        file_exists = self.csh.check_file_exists("/tmp", "file.txt")
        self.assertEqual(file_exists, True)

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_create_directory_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.create_directory("/tmp")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_create_directory_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "out": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.create_directory,
                          "/tmp")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_delete_file_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.delete_file("/tmp", "file.txt")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_delete_file_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "out": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.delete_file,
                          "/tmp", "file.txt")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_unpack_tarfile_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.unpack_tarfile("/home", "/tmp", "file.txt")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_unpack_tarfile_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "out": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.unpack_tarfile,
                          "/home", "/tmp", "file.txt")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_transfer_sdp_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success", "md5sum": 44}
        with patch('tempfile.mkdtemp', return_value="/tmp"):
            with patch('os.chmod', return_value=True):
                with patch('shutil.copy2', return_value=True):
                    result = self.csh.transfer_sdp("mn1", "/tmp", "/tmp", "file.txt", "10.10.10.100")
        self.assertEqual(result, 44)

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_transfer_sdp_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "err": "Error"}
        with patch('tempfile.mkdtemp', return_value="/tmp"):
            with patch('os.chmod', return_value=True):
                with patch('shutil.copy2', return_value=True):
                    self.assertRaises(CmwMcoApiException,
                          self.csh.transfer_sdp,
                          "mn1", "/tmp", "/tmp", "file.txt", "10.10.10.100")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_import_sdp_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.import_sdp("file.txt", "/tmp")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_import_sdp_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "out": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.import_sdp,
                          "file.txt", "/tmp")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_start_campaign_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.start_campaign("campaign_name")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_start_campaign_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "out": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.start_campaign,
                          "campaign_name")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_commit_campaign_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.commit_campaign("campaign_name")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_commit_campaign_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "out": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.commit_campaign,
                          "campaign_name")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_spersist_configuration_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.persist_configuration()

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_persist_configuration_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "out": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.persist_configuration)

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_remove_campaign_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "Success"}
        self.csh.remove_campaign("campaign_name")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_remove_campaign_unsuccessfully(self, _call_mco):
        _call_mco.return_value = {"retcode": -1, "out": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.remove_campaign,
                          "campaign_name")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_get_campaign_status_fail1(self, _call_mco):
    # The mco call will fail
        _call_mco.return_value = {"retcode": -1, "Err": "Error"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.get_campaign_status,
                          "campaign_name")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_get_campaign_status_fail2(self, _call_mco):
    # The campaign prefix is incorrect ie campaign#####
        _call_mco.return_value = {"retcode": 0, "out": "campaign#####"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.get_campaign_status,
                          "campaign_name")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_get_campaign_status_fail3(self, _call_mco):
    # The campaign status is not one of 'INITIAL', 'EXECUTING', 
    #'COMPLETED', 'COMMITTED'
        _call_mco.return_value = {"retcode": 0, "out": "campaign=invalid"}
        self.assertRaises(CmwMcoApiException,
                          self.csh.get_campaign_status,
                          "campaign")

    @mock.patch('cmwplugin.cmw_mco_api.CmwMcoApi._call_mco')
    def test_get_campaign_status_successfully(self, _call_mco):
        _call_mco.return_value = {"retcode": 0, "out": "campaign=COMMITTED"}
        status = self.csh.get_campaign_status("campaign")
        self.assertEqual(status, "COMMITTED")

    @mock.patch('cmwplugin.cmw_mco_api.run_rpc_command')
    def test_call_mco_not_enough_results(self, run_rpc):
        run_rpc.return_value = {}
        mco_action = "execute_script"
        args = {"arg1": "val1"}
        self.assertRaises(CmwMcoApiException,
                          self.csh._call_mco,
                          "cmw_utils",
                          mco_action,
                          args)

    @mock.patch('cmwplugin.cmw_mco_api.run_rpc_command')
    def test_call_mco_reply_from_wrong_node(self, run_rpc):
        run_rpc.return_value = {"mn3": {"data": {"retcode": 0,
                                                 "out": "",
                                                 "err": ""},
                                        "errors": ""
                                        }
                                }
        mco_action = "execute_script"
        args = {"arg1": "val1"}
        self.assertRaises(CmwMcoApiException,
                          self.csh._call_mco,
                          "cmw_utils",
                          mco_action,
                          args)

    @mock.patch('cmwplugin.cmw_mco_api.run_rpc_command')
    def test_call_mco_reply_failure_from_one_node(self, run_rpc):
        run_rpc.return_value = {"mn1": {"data": {"retcode": 0,
                                                 "out": "",
                                                 "err": ""},
                                        "errors": ""
                                        },
                                "mn2": {"data": {"retcode": 0,
                                                 "out": "",
                                                 "err": ""},
                                        "errors": "Problem"
                                        }
                                }
        mco_action = "execute_script"
        args = {"arg1": "val1"}
        self.assertRaises(CmwMcoApiException,
                          self.csh._call_mco,
                          "cmw_utils",
                          mco_action,
                          args,
                          n=["mn1", "mn2"])
