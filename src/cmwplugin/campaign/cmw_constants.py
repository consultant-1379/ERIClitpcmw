##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

VALID_CAMPAIGN_STATUS = ["INITIAL", "EXECUTING", "COMPLETED", "COMMITTED"]

SUCCESS = 0
CAMPAIGN_SLEEP_SECONDS = 20

LITP_ROOT = "/opt/ericsson/nms/litp"
LITP_SDP_REPO = "/var/www/html/sdp_repo"
LITP_DATA_DIR = "/var/lib/litp/plugins/cmwplugin/data"

REDUNDANCY_MODEL = {
"nway-active":  "SA_AMF_N_WAY_ACTIVE_REDUNDANCY_MODEL",
"nway":         "SA_AMF_N-WAY_REDUNDANCY_MODEL",
"2n":           "SA_AMF_2N_REDUNDANCY_MODEL",
"nored":        "SA_AMF_NO_REDUNDANCY_MODEL",
"n+m":          "SA_AMF_NPM_REDUNDANCY_MODEL",
}

COMPTYPE_ETF_TEMPLATE = """<AmfEntityType>
<CompType name="safCompType=$comp_type_name" \
version="safVersion=$comp_type_version">
<providesCSType name="safCSType=$comp_type_provides_cs" \
version="safVersion=1.0.0">
        <oneactive/>
      </providesCSType>
      <unproxiedNonSaAware>
        <instantiateCmd>
          <command>$start_cmd</command>
          <args></args>
        </instantiateCmd>
        <terminateCmd>
          <command>$stop_cmd</command>
          <args></args>
        </terminateCmd>
        <cleanupCmd>
          <command>$cleanup_cmd</command>
          <args></args>
        </cleanupCmd>
      </unproxiedNonSaAware>
      <osafHcCmd>
        <command>$status_cmd</command>
        <args></args>
      </osafHcCmd>
      <bundleReference name="$bundle_reference"/>
    </CompType>
  </AmfEntityType>"""

SW_BUNDLE_ETF_TEMPLATE = """
        <swBundle>
            <removal>
                <offline>
                    <command>offline-remove.sh</command>
                    <args />
                    <serviceUnit />
                </offline>
                <online>
                    <command />
                    <args />
                </online>
            </removal>
            <installation>
                <offline>
                    <command>offline-install.sh</command>
                    <args />
                    <serviceUnit />
                </offline>
                <online>
                    <command />
                    <args />
                </online>
            </installation>
        </swBundle>
        """
