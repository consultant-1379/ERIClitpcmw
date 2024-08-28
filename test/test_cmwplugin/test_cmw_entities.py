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

from cmwplugin.campaign.cmw_entities import cmwJBossComponent


class TestcmwJBossComponent(unittest.TestCase):

    def test_constructor(self):
        base_name = 'base'
        comp_name = 'comp1'
        version = '1.0'
        cleanup_cmd = '/bin/true'
        self.cmw_jboss_component = cmwJBossComponent(comp_name, base_name,
                                                     version, cleanup_cmd)

        self.assertEquals(self.cmw_jboss_component.start_cmd,
            "../opt/ericsson/nms/litp/bin/litp-jboss start")
        self.assertEquals(self.cmw_jboss_component.stop_cmd,
            "../opt/ericsson/nms/litp/bin/litp-jboss stop")
        self.assertEquals(self.cmw_jboss_component.status_cmd,
            "../opt/ericsson/nms/litp/bin/litp-jboss status")
        self.assertEquals(self.cmw_jboss_component.cleanup_cmd,
            "../bin/true")
