from base_cmw_integration import CmwIntegrationBase
from cmwplugin.campaign.cmw_model_manager import cmwModelManager
from cmwplugin.campaign.cmw_etf import cmwETFGenerator
from cmwplugin.campaign.cmw_cluster_manager import cmwClusterManager
from cmwplugin.campaign.cmw_software import cmwBundle
import mock

from lxml import etree


def _get_rpm_path_SE(rpm_info):
    return "/tmp/test.rpm"


def _get_sdp_SE(rpm_path):
    return cmwBundle("cmw-test-V1-R1", "/tmp/test.sdp")


def _get_rpm_install_files(rpm_path):
    return ["/etc/init.d/httpd", "/bin/true"]


class TestCMWCampaignIntegration(CmwIntegrationBase):

    def setUp(self):
        super(TestCMWCampaignIntegration, self).setUp()

    def test_etf_gen_1_sg(self):
        self.setup_model()
        self._add_service_to_model("1", "cs")
        primary_node = "mn1"
        nodes = ["mn2", "mn1"]
        sgs_dict = cmwModelManager(self.context_api).fromApi()
        print sgs_dict
        cmw_cluster_manager = cmwClusterManager(primary_node, nodes, sgs_dict)
        self.assertTrue(cmw_cluster_manager.apps, "no service groups defined")
        for app in cmw_cluster_manager.apps:
            for sg in app.service_groups:
                campaign_name = "3PP-service1_Install"
                etf = cmwETFGenerator().generate_sg_etf(sg, campaign_name)
                parser = etree.XMLParser(remove_blank_text=True)
                elem = etree.XML(etf.etf_xml, parser=parser)
                xml_str = etree.tostring(elem)
                expected_etf = \
"""<entityTypesFile xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="SAI-AIS-SMF-ETF-A.01.02_OpenSAF.xsd" name="3PP-service1_Install" provider="3PP">
  <AmfEntityType>
    <AppType name="safAppType=Litp_App" version="safVersion=1.0.0">
      <serviceGroupType name="safSgType=service1-SgType" version="safVersion=1.0.0"/>
    </AppType>
  </AmfEntityType>
  <AmfEntityType>
    <SGType name="safSgType=service1-SgType" version="safVersion=1.0.0">
      <suType name="safSuType=service1-SuType" version="safVersion=1.0.0"/>
      <redModel>SA_AMF_N_WAY_ACTIVE_REDUNDANCY_MODEL</redModel>
      <autoRepairOption>true</autoRepairOption>
    </SGType>
  </AmfEntityType>
  <AmfEntityType>
    <SUType name="safSuType=service1-SuType" version="safVersion=1.0.0">
      <componentType version="safVersion=1.0.0" name="safCompType=service1_lsb1-CompType"/>
      <providesServiceType name="safSvcType=service1-SvcType" version="safVersion=1.0.0"/>
    </SUType>
  </AmfEntityType>
  <AmfEntityType>
    <ServiceType name="safSvcType=service1-SvcType" version="safVersion=1.0.0">
      <csType version="safVersion=1.0.0" name="safCSType=service1_lsb1-CsType"/>
    </ServiceType>
  </AmfEntityType>
  <AmfEntityType>
    <CompType name="safCompType=service1_lsb1-CompType" version="safVersion=1.0.0">
      <providesCSType name="safCSType=service1_lsb1-CsType" version="safVersion=1.0.0">
        <oneactive/>
      </providesCSType>
      <unproxiedNonSaAware>
        <instantiateCmd>
          <command>../sbin/service cs start</command>
          <args/>
        </instantiateCmd>
        <terminateCmd>
          <command>../sbin/service cs stop</command>
          <args/>
        </terminateCmd>
        <cleanupCmd>
          <command>../bin/true</command>
          <args/>
        </cleanupCmd>
      </unproxiedNonSaAware>
      <osafHcCmd>
        <command>../sbin/service cs status</command>
        <args/>
      </osafHcCmd>
      <bundleReference name="safSmfBundle=3PP-dummy-0-R0"/>
    </CompType>
  </AmfEntityType>
  <AmfEntityType>
    <CSType name="safCSType=service1_lsb1-CsType" version="safVersion=1.0.0"/>
  </AmfEntityType>
  <swBundle name="safSmfBundle=3PP-dummy-0-R0">
            <removal>
                <offline>
                    <command>offline-remove.sh</command>
                    <args/>
                    <serviceUnit/>
                </offline>
                <online>
                    <command/>
                    <args/>
                </online>
            </removal>
            <installation>
                <offline>
                    <command>offline-install.sh</command>
                    <args/>
                    <serviceUnit/>
                </offline>
                <online>
                    <command/>
                    <args/>
                </online>
            </installation>
        </swBundle>
</entityTypesFile>"""
                elem = etree.XML(expected_etf, parser=parser)
                xml_str_expec = etree.tostring(elem)
                self.assertEqual(xml_str, xml_str_expec)
