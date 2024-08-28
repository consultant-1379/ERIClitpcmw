import unittest

import mock

from cmwplugin.campaign import cmw_exec_manager


class TestCMWExecutionManager(unittest.TestCase):
    """
    Tests for `CMWExecutionManager`.
    """

    def setUp(self):
        self.primary_node = mock.Mock()
        self.manager = cmw_exec_manager.cmwExecutionManager(self.primary_node)
        self.manager.cmw_mco_cmd = mock.Mock()

    def test_import_sdps(self):
        try:
            self.manager.import_sdps(self.primary_node)
            assert False
        except Exception as err:
            self.assertEquals(
                'No files to import',
                err.message)

        self.manager.import_sdps(self.primary_node, 'file1', 'file2')
        self.manager.cmw_mco_cmd.import_sdp.assert_any_call(
            'file1', destpath='/tmp')
        self.manager.cmw_mco_cmd.import_sdp.assert_any_call(
            'file2', destpath='/tmp')
        self.manager.cmw_mco_cmd.delete_file.assert_any_call('/tmp', 'file1')
        self.manager.cmw_mco_cmd.delete_file.assert_any_call('/tmp', 'file2')

    def test_transfer_files(self):
        try:
            self.manager.transfer_files(
                '10.10.10.1',
                '10.10.10.2',
                '/foo',
                '/bar')
            assert False
        except Exception as err:
            self.assertEquals(
                'No files to transfer',
                err.message)
        # TODO test positive case, requires file IO mock.
