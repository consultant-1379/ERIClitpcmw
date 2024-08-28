##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import fnmatch
import os
import subprocess
import shutil
import re
import binascii
import tempfile
import tarfile
import sys

from cmwplugin.campaign import cmw_constants
from litp.core.litp_logging import LitpLogger
log = LitpLogger()


def _run_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    p.wait()
    stdout = p.stdout.read().strip()
    stderr = p.stderr.read().strip()
    return (p.returncode, stdout, stderr)


def generate_sdp(tarname, source_dir, output_dir, files=None):
    """
    Generate the SDP file
    """
    tarname += ".sdp"
    tarpath = os.sep.join((output_dir, tarname))

    log.trace.debug("Generating SDP {0}".format(tarname))
    try:
        tar = tarfile.open(name=tarpath, mode="w:gz", dereference=True)

        if not files:
            files = os.listdir(source_dir)

        for f in files:
            tar.add("{0}/{1}".format(source_dir, f),
                arcname=f)
        tar.close()
        return True
    except:  # pylint: disable=W0702
        log.event.error("Exception while packing SDP file %s: %s" % (tarname,
                                                             sys.exc_info()))
        return False


class RpmToSdp(object):
    """@summary: Builds and packages RPM informations and pack to SDP.
    Does not generate SDP, uses CMWUtil for that.
    """

    def __init__(self, rpm_path, output_path):
        """ """
        assert os.path.exists(rpm_path)
        self.rpm_path = rpm_path
        self.output_path = output_path
        path = os.path.dirname(cmw_constants.__file__)
        self._templates = os.path.join(path, "./templates")

        self._workspace = tempfile.mkdtemp()

        self.cmw_name = None
        self.sdp_path = None
        self.provider = None
        self._setup()

    def __del__(self):
        shutil.rmtree(self._workspace)

    def _condense_name(self, name, size=30):
        if len(name) > size - 1:
            name = name[:size - 10] + '_' + \
                hex(binascii.crc32(name) & 0xffffffff)\
                          .lstrip('0x').rstrip('L')
        return name

    def _remove_symbols(self, text, replace_with=""):
        pattern = re.compile(r"[\W_]+")
        return pattern.sub(replace_with, text)

    def _setup(self):
        """:summary: Uses _rpm_extractor to build CMW Name
        and path to SDP file.
        """
        rpm_version = RpmInfo.get_rpm_tag("version", self.rpm_path)
        rpm_version = rpm_version.upper()
        rpm_version = self._remove_symbols(rpm_version)

        rpm_release = RpmInfo.get_rpm_tag("release", self.rpm_path)
        rpm_release = self._remove_symbols(rpm_release)

        if not re.search("^[RP]", rpm_release):
            rpm_release = "R" + rpm_release

        rpm_release = rpm_release.upper()

        rpm_name = RpmInfo.get_rpm_tag("name", self.rpm_path)
        rpm_name = self._remove_symbols(rpm_name, '_')

        rpm_name = self._condense_name(rpm_name)

        self.provider = RpmInfo.get_provider(self.rpm_path)
        self.cmw_name = '-'.join((self.provider, rpm_name,
                             rpm_version, rpm_release))

        self.sdp_path = os.path.join(self.output_path, self.cmw_name)
        self.sdp_path += ".sdp"

    def pack(self):
        """:summary: This function does things:
        - Copies required RPMs and template XMLs into _workspace
        - Does a string replace on ETF xml
        - Calls generate_sdp

        :return: Tuple containing path to SDP and CMW compliant package name
        :type: tuple
        """
        rpms_dir = os.path.join(self._workspace, "rpms")
        if not os.path.exists(rpms_dir):
            try:
                os.mkdir(rpms_dir)
            except OSError as eo:
                log.event.error("Failed to create dir '{0}'. {1}".format(
                                                                    rpms_dir,
                                                                         eo))
                raise Exception("Error while creating SDP files")

        # symlink/copy files
        self._symlink_rpms(rpms_dir)

        etf_path = os.path.join(self._workspace, "ETF.xml")
        shutil.copy2(os.path.join(self._templates, "ETF_bundle.xml"),
                     etf_path)
        shutil.copy2(os.path.join(self._templates, "offline-remove.sh"),
                     self._workspace)
        shutil.copy2(os.path.join(self._templates, "offline-install.sh"),
                     self._workspace)

        self._update_etf(etf_path)
        if not generate_sdp(self.cmw_name, self._workspace, self.output_path):
            raise Exception("Error while creating SDP files")
        return (self.sdp_path, self.cmw_name)

    def _symlink_rpms(self, rpms_dir):
        symlink_path = os.path.join(rpms_dir,
                                        os.path.basename(self.rpm_path))
        os.symlink(self.rpm_path, symlink_path)

    def _update_etf(self, etf_path):
        _etf_content = []
        with open(etf_path, "r") as f:
            _etf_content = f.readlines()

        with open(etf_path, "w") as f:
            for line in _etf_content:
                line = line.replace('$provider', self.provider)
                line = line.replace('$name', self.cmw_name)
                f.write(line)


class RpmInfo(object):

#    TODO
# use this command to query all packages in a directory
# find $PWD -name "*.rpm" -exec rpm -qp --nosignature --qf
#  '%{Name} %{Version}' {} \; -exec echo " " {} \;
    @staticmethod
    def get_rpm_tag(tag, rpm_path):
        """
        Query package and retrieve info.

        :param info: Package info queried.
        :type info: string
        """
        cmd = "rpm -qp --nosignature --qf %{{{0}}} {1}".format(tag.upper(),
                                                               rpm_path)
        rc, stdout, stderr = _run_cmd(cmd)
        if rc != 0:
            raise Exception("Error getting RPM info: '%s'" % stderr)
        return stdout.strip()

    @staticmethod
    def get_provider(rpm_path):
        """ """
        vendor = RpmInfo.get_rpm_tag("vendor", rpm_path)
        if vendor:
            provider = "3PP"
            if vendor == "Ericsson AB":
                provider = "ERIC"
            return provider

    @staticmethod
    def get_cmw_name(rpm_path):
        """@summary: Builds CMW compliant name for given RPM package
        """
        provider = RpmInfo.get_provider(rpm_path)
        name = RpmInfo.get_rpm_tag("name", rpm_path)
        version = RpmInfo.get_rpm_tag("version", rpm_path)
        release = RpmInfo.get_rpm_tag("release", rpm_path)
        return '-'.join((provider, name, version, release))

    @staticmethod
    def get_rpm_tags(tag_list, rpm_path):
        """Reads tags for given RPM

        :param attr_list: List of RPM tags
        :type attr_list: tags
        """
        cmd = "rpm -qp --nosignature --qf "
        attr = ",".join(["%{" + x.strip().upper() + "}" for x in tag_list])
        cmd += attr + ' ' + rpm_path

        rc, stdout, stderr = _run_cmd(cmd)
        tags = stdout.split(',')

        if rc != 0:
            raise Exception('Error getting RPM tag for package {0}:'
                            ' {1} '.format(rpm_path, stderr))
        return tags

    @staticmethod
    def get_rpm_install_dirs(rpm_path):
        """Get dirs provided by RPM
        """
        cmd = "rpm -qp --qf '[%{DIRNAMES}\n]' " + rpm_path
        rc, stdout, stderr = _run_cmd(cmd)
        dir_list = [x.strip() for x in stdout.split('\n')]
        if rc != 0:
            raise Exception('error getting rpm info : %s ' % stderr)

        return  dir_list

    @staticmethod
    def get_rpm_install_files(rpm_path):
        """@summary: Return the install files of a RPM, without the dirs
        """
        cmd = "rpm -qlp " + rpm_path
        rc, stdout, stderr = _run_cmd(cmd)
        if rc != 0:
            raise Exception('Error getting rpm info : %s ' % stderr)

        file_list = [x.strip() for x in stdout.split('\n')]
        dir_list = RpmInfo.get_rpm_install_dirs(rpm_path)
        #  remove the ending slash
        dir_list = [x[:-1] for x in dir_list]

        # We just need the files not the dirs
        file_list = set(file_list) - set(dir_list)

        return  list(file_list)


class cmwBundle(object):
    '''
    Class representing a SDP bundle
    '''

    def __init__(self, cmw_name, path, rpm_list=None, sdp_gen=None):
        '''
        Constructor
        '''
        self.name = cmw_name
        self.rpm_list = rpm_list
        self.path = path
        self.file_name = os.path.basename(self.path)
        self.sdp_gen = sdp_gen

    def pack(self):
        self.sdp_gen.pack()


class cmwDummyBundle(cmwBundle):
    '''
    Class representing an empty SDP bundle
    '''

    def __init__(self):
        super(cmwDummyBundle, self).__init__()


class cmwRPM(object):
    '''
    Class representing an RPM file in a repo
    '''
    def __init__(self, path, repo_name, name, version, release, arch):
        self.path = path
        self.repo_name = repo_name
        self.name = name
        self.version = version
        self.release = release
        self.arch = arch


class cmwRepo(object):
    '''
    Class representing a repository of software packages
    '''
    def __init__(self, repo_name, repo_path):
        self.repo_name = repo_name.upper()
        self.repo_path = repo_path
        self.repo_dict = {}

    def get_rpm(self, rpm_info):
        pack_name = None
        pack_version = None
        pack_release = None
        pack_arch = None
        if "name" in rpm_info:
            pack_name = rpm_info["name"]
        if "version" in rpm_info:
            pack_version = rpm_info["version"]
        if "release" in rpm_info:
            pack_release = rpm_info["release"]
        if "arch" in rpm_info:
            pack_arch = rpm_info["arch"]

        pkg_map = {'pack_name': 'Name', 'pack_version': 'Version',
                   'pack_release': 'Release', 'pack_arch': 'Arch'}
        if not self.repo_dict:
            self.refresh()

        if pack_name in self.repo_dict:
            prop_list = dict()
            if pack_version:
                prop_list['pack_version'] = str(pack_version)
            if pack_release:
                prop_list['pack_release'] = str(pack_release)
            if pack_arch:
                prop_list['pack_arch'] = str(pack_arch)

            errors = list()
            versions = self.repo_dict[pack_name]
            try:
                if len(prop_list) == 3:
                    return versions[pack_version][pack_release][pack_arch]
                elif len(prop_list) == 2:
                    if pack_version and pack_release:
                        arches = versions[pack_version][pack_release]
                        if len(arches) != 1:
                            errors.append('multi_arch')
                        else:
                            return arches.values()[0]
                    elif pack_version and pack_arch:
                        releases = versions[pack_version]
                        if len(releases) != 1:
                            errors.append('multi_release')
                        else:
                            arches = releases.values()[0]
                            if len(arches) != 1:
                                errors.append('multi_arch')
                            else:
                                return arches.values()[0]
                elif len(prop_list) == 1:
                    if pack_version:
                        releases = versions[pack_version]
                        if len(releases) != 1:
                            errors.append('multi_release')
                        else:
                            arches = releases.values()[0]
                            if len(arches) == 1:
                                return arches.values()[0]
                            else:
                                errors.append('multi_arch')
                    elif pack_arch:
                        releases = versions.values()[0]
                        if len(versions) == 1 and len(releases) == 1:
                            return releases.values()[0][pack_arch]
                        else:
                            if len(versions) > 1:
                                errors.append('multi_version')
                            else:
                                errors.append('multi_release')
                elif len(prop_list) == 0:
                    releases = versions.values()[0]
                    arches = releases.values()[0]
                    if len(versions) == 1 and len(releases) == 1 \
                    and len(arches) == 1:
                        return arches.values()[0]
                    else:
                        if len(versions) > 1:
                            errors.append('multi_version')
                        elif len(releases) > 1:
                            errors.append('multi_release')
                        else:
                            errors.append('multi_arch')
            except KeyError as e:
                def_props = []
                failed_prop = []
                for prop, val in prop_list.iteritems():
                    prop_str = pkg_map[prop] + ": " + val
                    def_props.append(prop_str)
                    # FIXME BaseException.message is deprecated
                    if str(val) == str(e.args[0]):
                        failed_prop.append(prop_str)
                err_msg = ("RPM '{0}' with properties '{1}' not valid."
                             " No package with '{2}' available on "
                             "repository '{3}'").format(pack_name,
                                                        def_props,
                                                        failed_prop,
                                                        self.repo_name)
                log.trace.debug(err_msg)
                raise Exception(err_msg)
            if errors:
                err_msg = "Package '%s' has errors on the definition. " % \
                                                                pack_name
                def_props = [pkg_map[prop] + ": " + val for prop, val
                             in prop_list.items()]
                err_msg += "Defined properties '%s'. " % str(def_props)
                for err in errors:
                    if err == 'multi_arch':
                        err_msg += ("Multiple architectures for this "
                                    "package. Found: ")
                        for arch in arches:
                            err_msg += "'%s' " % arch
                    elif err == 'multi_release':
                        err_msg += ("Multiple releases for this "
                                    "package. Found: ")
                        for rel in releases:
                            err_msg += "'%s' " % rel
                    elif err == 'multi_version':
                        err_msg += ("Multiple versions for this "
                                    "package. Found: ")
                        for ver in versions:
                            err_msg += "'%s' " % ver
                log.trace.debug(err_msg)
                raise Exception(err_msg)
        else:
            err_msg = "RPM Package '{0}' not found in " \
                    "repository '{1}' ".format(pack_name,
                                                              self.repo_name)
            log.trace.debug(err_msg)
            raise Exception(err_msg)

    def refresh(self):
        for root, _, filenames in os.walk(self.repo_path):
            name_to_find = "*.rpm"
            # FIXME: change to glob probably
            for f in fnmatch.filter(filenames, name_to_find):
                rpm_path = os.path.join(root, f)
                rpm_path = \
                    rpm_path.replace(r'(', r'\(').replace(r')', r'\)')
                try:
                    attr_list = \
                    RpmInfo.get_rpm_tags(
                                        ['NAME', 'VERSION', 'RELEASE', 'ARCH'],
                                        rpm_path)
                except Exception, e:
                    log.event.error(str(e))
                    raise
                rpm_name = attr_list[0]
                version = attr_list[1]
                release = attr_list[2]
                arch = attr_list[3]

                # If found a new repositry add it.
                if rpm_name not in self.repo_dict:
                    self.repo_dict[rpm_name] = dict()

                # Append new versions/releases to the same package name
                if version not in self.repo_dict[rpm_name]:
                    self.repo_dict[rpm_name][version] = {}
                    self.repo_dict[rpm_name][version][release] = {}
                    self.repo_dict[rpm_name][version][release][arch] = \
                                                            rpm_path
#                            self.repo_dict[rpm_name][version][release].append(
#                                                             (rpm_path, arch))
                elif release not in self.repo_dict[rpm_name][version]:
                    self.repo_dict[rpm_name][version][release] = {}
                    self.repo_dict[rpm_name][version][release][arch] = \
                                                            rpm_path
                else:
                    # LITP-3791
                    # Changing error to debug, and not updating
                    # same package definition if one is already there.
                    if arch in \
                        self.repo_dict[rpm_name][version][release]:

                        wrn_msg = ("There are duplicated RPMs on"
                              " your repo: {0} and {1} have the same"
                              " name, version, release and arch in"
                              " RPM headers, found on repo {2}").format(
                                                    self.repo_dict[rpm_name]
                                                   [version]
                                                   [release]
                                                   [arch],
                                                   rpm_path,
                                                   self.repo_name)
                        log.event.warning(wrn_msg)

                    self.repo_dict[rpm_name][version][release][arch] = \
                            rpm_path
