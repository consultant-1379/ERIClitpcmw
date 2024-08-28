##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import os
import tarfile
import yum
import tempfile
import shutil

from cmwplugin.campaign.cmw_software import cmwRepo
from cmwplugin.campaign.cmw_software import cmwBundle
from cmwplugin.campaign.cmw_software import RpmToSdp
from cmwplugin.campaign import cmw_constants
from cmwplugin.campaign.cmw_etf import cmwETFGenerator
from cmwplugin.campaign.cmw_constants import LITP_DATA_DIR
from litp.core.litp_logging import LitpLogger
log = LitpLogger()
REPOS = {"3PP": "/var/www/html/3pp"}
        #"OS": "/profiles/node-iso/Packages/"}


class cmwSoftwareManager(object):
    '''
    Manage repos and other software related information
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.repos = []
        for repo_name, repo_path in REPOS.items():
            repo = cmwRepo(repo_name, repo_path)
            repo.refresh()
            self.repos.append(repo)

    def get_dummy_sdp(self):
        """ """
        return cmwBundle("3PP-dummy-0-R0",
                                    os.path.join(cmw_constants.LITP_SDP_REPO,
                                                        "3PP-dummy-0-R0.sdp"))

    def _generate_jboss_env(self, active, app, service_name,
            jee_container_name):
        jboss_env_file_names = []

        for index in range(active):
            default = {"LITP_JEE_CONTAINER_name": "jboss",
                "LITP_JEE_CONTAINER_instance_name":
                    service_name + "_su_" + str(index) + "_" + \
                    jee_container_name + "_instance",
                "LITP_JEE_CONTAINER_install_source":
                    "/opt/ericsson/nms/jboss/jboss-eap-6.1.1.tgz",
                "LITP_JEE_CONTAINER_home_dir":
                    "/home/jboss/" + service_name + "_su_" + str(index) + \
                    "_" + jee_container_name + "_instance",
                "LITP_JEE_CONTAINER_version": "1.0.0",
                "LITP_JEE_CONTAINER_process_user": "litp-admin",
                "LITP_JEE_CONTAINER_process_group": "litp-admin",
                "LITP_JEE_CONTAINER_public_listener": "0.0.0.0",
                "LITP_JEE_CONTAINER_public_port_base": "8080",
                "LITP_JEE_CONTAINER_management_listener": "0.0.0.0",
                "LITP_JEE_CONTAINER_management_port_base": "9990",
                "LITP_JEE_CONTAINER_management_port_native": "9999",
                "LITP_JEE_CONTAINER_internal_listener": "0.0.0.0",
                "LITP_JEE_CONTAINER_management_user": "admin",
                "LITP_JEE_CONTAINER_management_password": "passs.w0rd",
                "LITP_JEE_CONTAINER_port_offset": "0",
                "LITP_JEE_CONTAINER_Xms": "4048M",
                "LITP_JEE_CONTAINER_Xmx": "4048M",
                "LITP_JEE_CONTAINER_MaxPermSize": "512M",
                "LITP_JEE_CONTAINER_command_line_options":
                    "--server-config=standalone.xml -Djava.net." \
                    "preferIPv4Stack=true",
                "LITP_JEE_CONTAINER_pre_deploy":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "pre_deploy.d",
                "LITP_JEE_CONTAINER_post_deploy":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "post_deploy.d",
                "LITP_JEE_CONTAINER_pre_undeploy":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "pre_undeploy.d",
                "LITP_JEE_CONTAINER_post_undeploy":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "post_undeploy.d",
                "LITP_JEE_CONTAINER_pre_start":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "pre_start.d",
                "LITP_JEE_CONTAINER_post_start":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "post_start.d",
                "LITP_JEE_CONTAINER_pre_shutdown":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "pre_shutdown.d",
                "LITP_JEE_CONTAINER_post_shutdown":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "post_shutdown.d",
                "LITP_JEE_CONTAINER_pre_upgrade":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "pre_upgrade.d",
                "LITP_JEE_CONTAINER_post_upgrade":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_instance/" \
                    "post_upgrade.d",
                "LITP_DE_COUNT": "1",
                "LITP_DE_0_JEE_DE_install_source":
                    "/opt/jboss-eap/standalone/deployments/" \
                    "jboss-as-helloworld-1.1.1.war",
                "LITP_DE_0_JEE_DE_name": "jboss-as-helloworld-1.1.1.war",
                "LITP_DE_0_JEE_DE_version": "1.1.1",
                "LITP_DE_0_JEE_DE_app_type": "war",
                "LITP_DE_0_JEE_DE_pre_deploy":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_deploy.d",
                "LITP_DE_0_JEE_DE_post_deploy":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/" \
                    "post_deploy.d",
                "LITP_DE_0_JEE_DE_pre_undeploy":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/" \
                    "pre_undeploy.d",
                "LITP_DE_0_JEE_DE_post_undeploy":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/" \
                    "post_undeploy.d",
                "LITP_DE_0_JEE_DE_pre_start":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_start.d",
                "LITP_DE_0_JEE_DE_post_start":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_start.d",
                "LITP_DE_0_JEE_DE_pre_shutdown":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/" \
                    "pre_shutdown.d",
                "LITP_DE_0_JEE_DE_post_shutdown":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/" \
                    "post_shutdown.d",
                "LITP_DE_0_JEE_DE_pre_upgrade":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_upgrade.d",
                "LITP_DE_0_JEE_DE_post_upgrade":
                    "/opt/ericsson/nms/litp/etc/jboss/jboss_app/" \
                    "post_upgrade.d",
                "LITP_SP_COUNT": "0",
            }
            jboss_defaults = os.path.join(LITP_DATA_DIR, "jboss_env_variables")
            if not os.path.exists(jboss_defaults):
                os.makedirs(jboss_defaults)

            unique_comp_id = service_name + '_' + jee_container_name
            su_type = app + '-' + 'SuType'
            sutype_inst = su_type + '-' + str(index)
            file_name = '.'.join((unique_comp_id, sutype_inst, service_name, \
                app, 'env'))
            jboss_default_file = os.path.join(jboss_defaults, file_name)
            f = open(jboss_default_file, 'a+')
            # Empty out the existing contents
            f.seek(0, 0)
            f.truncate()

            for k, v in default.items():
                f.write("%s=\"%s\"\n" % (k, v))
            f.close()

            #log.trace.debug("Written to file %s" % file_name)
            jboss_env_file_names.append(file_name)

        return jboss_env_file_names

    def get_jboss_default(self, active, app, service_name, jee_container_name):
        """ """
        output_path = cmw_constants.LITP_SDP_REPO
        cmw_name = '-'.join(("3PP", "jboss_defaults", "0", "R0"))

        workspace = tempfile.mkdtemp()
        path = os.path.dirname(cmw_constants.__file__)

        jboss_env_file_names = self._generate_jboss_env(active, app,
            service_name, jee_container_name)
        for file_name in jboss_env_file_names:
            jboss_defaults = os.path.join(LITP_DATA_DIR,
                "jboss_env_variables_file")
            jboss_default_file = os.path.join(jboss_defaults, file_name)
            shutil.copy2(jboss_default_file, workspace)
        templates = os.path.join(path, "templates")
        etf_template = os.path.join(templates, "ETF_bundle.xml")
        etf_path = os.path.join(workspace, "ETF.xml")
        shutil.copy2(etf_template, etf_path)
        cmwETFGenerator.update_etf_template(etf_path, cmw_name, "3PP")
        shutil.copy2(os.path.join(templates, "offline-remove.sh"),
                     workspace)
        shutil.copy2(os.path.join(templates, "offline-install.sh"),
                     workspace)

        return self.create_sdp(cmw_name, workspace, output_path)

    def sdp_exists(self, sdp_name):
        sdp_repo_path = os.path.join(cmw_constants.LITP_SDP_REPO,
                                     sdp_name + ".sdp")
        return os.path.isfile(sdp_repo_path)

    def get_sdp(self, rpm_info):
        rpm_path = self.get_rpm_path(rpm_info)
        sdp = RpmToSdp(rpm_path, cmw_constants.LITP_SDP_REPO)
        return cmwBundle(sdp.cmw_name, sdp.sdp_path, sdp_gen=sdp)

    def get_rpm_path(self, rpm_info):
        # TODO search ONLY default repo if no repo is defined?
        if "repository" in rpm_info:
            repo_name = rpm_info["repository"]
            repo = self._get_repo(repo_name)
            if not repo:
                raise Exception("Repository %s not found on the system" % \
                                                                    repo_name)
            return repo.get_rpm(rpm_info)

        for repo in self.repos:
            return repo.get_rpm(rpm_info)

    def _get_repo(self, repo_name):
        for repo in self.repos:
            if repo.repo_name == repo_name.upper():
                return repo
        return None

    @staticmethod
    def create_sdp(cmw_name, source_dir, output_dir, files=None):
        """
        Generate the SDP file
        """
        tarname = cmw_name + ".sdp"
        tarpath = os.sep.join((output_dir, tarname))

        log.trace.debug("Generating SDP {0}".format(tarname))

        tar = tarfile.open(name=tarpath, mode="w:gz", dereference=True)

        if not files:
            files = os.listdir(source_dir)

        for f in files:
            tar.add("{0}/{1}".format(source_dir, f),
                arcname=f)
        tar.close()
        return cmwBundle(cmw_name, tarpath)

    @staticmethod
    def is_os_package(pkg_name):
        yb = yum.YumBase()
        # Important to note that enabling just cached operation is the only
        # way to use a non-root user, for now we trust that the plugin will
        # always be ran with root, so cache only operation is disabled
        yb.conf.cache = 0
        for repo in yb.repos.listEnabled():
            yb.repos.disableRepo(repo.id)
        yb.repos.enableRepo("OS")
        pl = yb.doPackageLists(pkgnarrow="all", patterns=[pkg_name])
        if pl.available or pl.installed:
            return True
        return False

    def check_rpms(self, pkgs_dict, os_pkgs, node_names):
        pass
