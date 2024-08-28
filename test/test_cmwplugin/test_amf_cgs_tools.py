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

import mock

from cmwplugin.campaign import amf_cgs_tools


class TestTempDirContextManager(unittest.TestCase):

    @mock.patch('cmwplugin.campaign.amf_cgs_tools.tempfile.mkdtemp')
    @mock.patch('cmwplugin.campaign.amf_cgs_tools.shutil.rmtree')
    def test_tempdir(self, rmtree, mkdtemp):
        with amf_cgs_tools.tempdir() as tmpdir:
            pass
        mkdtemp.assert_called_with(prefix='tmp')
        rmtree.assert_called_with(tmpdir)

        with amf_cgs_tools.tempdir(prefix='lalala') as tmpdir:
            pass
        mkdtemp.assert_called_with(prefix='lalala')
        rmtree.assert_called_with(tmpdir)


class TestAmfCgsTools(unittest.TestCase):

    def setUp(self):
        self.amf_cgs = amf_cgs_tools.AmfCgsTools("/tmp")

    def test_check_rdn_size(self):
        try:
            self.amf_cgs._check_rdn_size('1' * 100, '')
            # Fail if no exception thrown.
            assert False
        except AssertionError:
            pass
        self.assertEqual(None, self.amf_cgs._check_rdn_size('1' * 63, ''))
        self.assertEqual(None, self.amf_cgs._check_rdn_size('', '1' * 63))
        self.assertEqual(None, self.amf_cgs._check_rdn_size('', '1'))
        self.assertEqual(None, self.amf_cgs._check_rdn_size('1', '1'))
