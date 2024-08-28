import unittest

import os
import tempfile
import filecmp
import re
import mock

from cmwplugin.campaign.cmw_software import RpmToSdp
from cmwplugin.campaign.cmw_software import RpmInfo
from cmwplugin.campaign.cmw_software import cmwRepo


def _mock__run_cmd(cmd):
    return


class TestCmwSoftware(unittest.TestCase):

    def setUp(self):
        pass

    #==========================================================================
    # def test_create_md5(self):
    #     temp = tempfile.mkdtemp() + "/test"
    #     with open(temp, "w") as f:
    #         f.write('TEST' + '\n')
    #     md5 = create_md5(temp)
    #     # Assert(os.path.exists(tmp_file))
    #     # os.remove(tmp_file)
    #==========================================================================

    def test_rpm_info_1(self):
        self.assertRaises(Exception, RpmInfo.get_rpm_tag, ('test'))

    @mock.patch('cmwplugin.campaign.cmw_software._run_cmd',
                mock.Mock(side_effect=lambda x: (0, "foobar,1.7.0_17,el6", "")))
    def test_rpm_info_get_rpm_tags(self):
        name = 'foobar-1.7.0-17-el6.rpm'
        attrs = ['name', 'version', 'release']
        expected = ["foobar", "1.7.0_17", "el6"]
        self.assertEqual(expected, RpmInfo.get_rpm_tags(attrs, "/tmp/test.rpm"))

    @mock.patch('cmwplugin.campaign.cmw_software._run_cmd',
                mock.Mock(side_effect=lambda x: (0, "foobar", "")))
    def test_rpm_info_get_rpm_tag(self):
        expected = "foobar"
        self.assertEqual(expected, RpmInfo.get_rpm_tag("name", "/tmp/test.rpm"))

    @mock.patch('cmwplugin.campaign.cmw_software.RpmInfo.get_rpm_tag',
                mock.Mock(side_effect=lambda x, y: 'Ericsson AB'))
    def test_rpm_info_get_provider_1(self):
        self.assertEquals('ERIC', RpmInfo.get_provider("/tmp/test.rpm"))

    @mock.patch('cmwplugin.campaign.cmw_software.RpmInfo.get_rpm_tag',
                mock.Mock(side_effect=lambda x, y: 'ABCD'))
    def test_rpm_info_get_provider_2(self):
        self.assertEquals('3PP', RpmInfo.get_provider("/tmp/test.rpm"))

    @mock.patch('cmwplugin.campaign.cmw_software.RpmInfo.get_rpm_tag',
                mock.Mock(side_effect=lambda x, y: x))
    def test_rpm_info_get_cmw_name(self):
        #re.get_rpm_tag = lambda x: x
        self.assertEquals('3PP-name-version-release', RpmInfo.get_cmw_name("/tmp/test.rpm"))
  
    def test_rpm_info_invalid_rpm(self):
        import tempfile

        file_desc, name = tempfile.mkstemp()
        self.assertRaises(Exception, RpmInfo.get_rpm_tag, 'NAME')
        self.assertRaises(Exception, RpmInfo.get_rpm_tags, 'NAME')

    @mock.patch('cmwplugin.campaign.cmw_software._run_cmd',
                mock.Mock(side_effect=lambda x: (0, "/opt/ericsson/jboss-eap-6.0.2.tgz", "")))
    @mock.patch('cmwplugin.campaign.cmw_software.RpmInfo.get_rpm_install_dirs',
                mock.Mock(side_effect=lambda path: ["/opt/", "/opt/ericsson/"]))
    def test_rpm_info_get_rpm_install_files(self):
        rpm_path = '/some/foobar-1.2.3-el6.rpm'
        expected = ['/opt/ericsson/jboss-eap-6.0.2.tgz']
        self.assertEqual(expected, RpmInfo.get_rpm_install_files(rpm_path))

    @mock.patch('cmwplugin.campaign.cmw_software._run_cmd',
                mock.Mock(side_effect=lambda x: (0, "/opt/\n/opt/ericsson/", "")))
    def test_rpm_info_get_rpm_install_dirs(self):
        rpm_path = '/some/foobar-1.2.3-el6.rpm'
        expected = ["/opt/", "/opt/ericsson/"]
        self.assertEqual(expected, RpmInfo.get_rpm_install_dirs(rpm_path))

    def file_fwrite(self, path, name, content=''):
        ff = open(os.path.join(path, name), 'w')
        ff.write(content)
        ff.close()

    #---------------------------------------------- def test_replace_etf(self):
        #----------------- mock_etf = tempfile.NamedTemporaryFile(delete=False)
        #---------------------------------- mock_etf.write('$provider \n$name')
        #----------------------------------------------------- mock_etf.close()
        #----------- CmwUtils()._replace_etf_content(mock_etf.name, 'cmw_name')
        #-------------------------------------- xd = open(mock_etf.name).read()
        #----------------------------------------- self.assertTrue('3PP' in xd)
        #------------------------------------ self.assertTrue('cmw_name' in xd)

    @mock.patch('cmwplugin.campaign.cmw_software.RpmInfo.get_rpm_tag',
                mock.Mock(side_effect=lambda x, y: x))
    def test_rpm2sdp1(self):
        temp = tempfile.mkdtemp()

        r2s = RpmToSdp(rpm_path=temp, output_path="/tmp")
        r2s._setup()

        self.assertEqual(r2s.provider, "3PP")
        self.assertEqual(r2s.cmw_name, "3PP-name-VERSION-RRELEASE")
        self.assertEqual(r2s.sdp_path, '/tmp/3PP-name-VERSION-RRELEASE.sdp')

        # paths to tmp
        r2s._templates = os.path.join(r2s._workspace, 'templates')
        r2s.output_path = os.path.join(r2s._workspace, 'output')
        os.mkdir(r2s._templates)
        os.mkdir(r2s.output_path)
        print r2s._workspace
        print r2s._templates

        self.file_fwrite(r2s._workspace, 'ETF.xml', r2s.provider + '\n' + r2s.cmw_name)
        self.file_fwrite(r2s._templates, 'ETF_bundle.xml', '$provider\n$name')
        self.file_fwrite(r2s._templates, 'offline-remove.sh', 'true')
        self.file_fwrite(r2s._templates, 'offline-install.sh', 'true')
        try:
            # mock generate_sdp, as we don't want to test that here
            cmw_name = '3PP-name-VERSION-RRELEASE'
            sdp_path = '/tmp/3PP-name-VERSION-RRELEASE.sdp'

            packed = r2s.pack()
            self.assertEqual(packed, (sdp_path, cmw_name))

            # assert that we copied required files.
            wanted = set(('offline-remove.sh', 'offline-install.sh',
                          'ETF.xml', 'output/3PP-name-VERSION-RRELEASE.sdp'))

            def _get_files(path, wanted):
                found = set()
                for each in wanted:
                    file = os.path.join(path, each)
                    if os.path.isfile(file):
                        found.add(each)
                return found

            self.assertEqual(wanted, _get_files(r2s._workspace, wanted))

            # assert that ETF content is updated
            etf_path = os.path.join(r2s._workspace, "ETF.xml")
            expect1 = os.path.join(r2s._workspace, "expected_ETF.xml")

            with open(expect1, 'w') as ff:
                ff.write("3PP\n3PP-name-VERSION-RRELEASE")

            self.assertTrue(filecmp.cmp(expect1, etf_path))
        except OSError:
            print "Permission denied in certain circumstances."

    def assertRaisesWithMessage(self, e_class, e, func, *args, **kwargs):
        """Same as assertRaises, but also compares the exception message."""
        if hasattr(e_class, '__name__'):
            exc_name = e_class.__name__
        else:
            exc_name = str(e_class)

        try:
            func(*args, **kwargs)
        except e_class as expr:
            if str(expr) != e:
                msg = '%s raised, but with wrong message: "%s" != "%s"'
                raise self.failureException(msg % (exc_name,
                                            str(expr),
                                               str(e)))
#                  str(expr).encode('string_escape'),
#                 str(e).encode('string_escape')))
            return
        else:
            raise self.failureException('%s not raised' % exc_name)

    def test_cmw_repo_get_rpm(self):

        package = {}
        package['name'] = "foo"
        package['version'] = "1.0.0"
        package['release'] = "15.el6"
        #package['arch'] = "x86_64"
        package['repository'] = "OS"

        def _mock_build_repo_rpm_dict():
            repos_dict ={
                        'foo': {
                               '1.0.0': {
                                         '15.el6':{
                                                   'x86_64':'/var/www/html/rhel/foo.rpm'
                                                    }
                                         }
                                },
                       'foo2': {
                                '1.0.1': {
                                          'r1':{
                                                'x86_64':'/var/www/html/litp/foo2.rpm'
                                                }
                                          }
                                ,
                                '1.0.2': {
                                          'r1':{
                                                'x86_64':'/var/www/html/litp/foo2.rpm'
                                                }
                                          }
                                },
                       'foo3': {
                                '1.0.1': {
                                          'r1':{
                                                'x86_64':'/var/www/html/litp/foo3_r1.rpm',
                                                'i686':'/var/www/html/litp/foo3_r1_i686.rpm'
                                                },
                                          'r2':{
                                                'x86_64':'/var/www/html/litp/foo3_r2.rpm'
                                                }
                                          }
                                          ,
                                },
                            }

            return repos_dict

        repo = cmwRepo("OS","/tmp")
        repo.repo_dict = _mock_build_repo_rpm_dict()
        # name, version, release
        rpm_to_install = '/var/www/html/rhel/foo.rpm'
        ret = repo.get_rpm(package)
        self.assertEqual(rpm_to_install, ret)

        # name, _, _, _
        package['version'] = None
        package['release'] = None
        # find 1 package
        rpm_to_install = '/var/www/html/rhel/foo.rpm'
        ret = repo.get_rpm(package)
        self.assertEqual(rpm_to_install, ret)

        # # name, _, _, _ -- find 1+ package
        # - more than one version
        package['name'] = 'foo2'
        message = "Package 'foo2' has errors on the definition. Defined properties '[]'. Multiple versions for this package. Found: '1.0.1' '1.0.2' "
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)
        #self.assertEqual(message, repo.get_rpm(package))

        # - more than one release
        package['name'] = 'foo3'
        message = "Package 'foo3' has errors on the definition. Defined properties '[]'. Multiple releases for this package. Found: 'r1' 'r2' "
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)

        # name, version, _, _
        package['name'] = 'foo'
        package['version'] = '1.0.0'
        # find 1 package
        rpm_to_install = '/var/www/html/rhel/foo.rpm'
        ret = repo.get_rpm(package)
        self.assertEqual(rpm_to_install, ret)
        # find 1+ package
        # - more than 1 version not valid as we have set the version

        # - more than 1 release
        package['name'] = 'foo3'
        package['version'] = '1.0.1'
        message = "Package 'foo3' has errors on the definition. Defined properties '['Version: 1.0.1']'. Multiple releases for this package. Found: 'r1' 'r2' "
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)

        # name, version, release, _.
        package['name'] = "foo"
        package['version'] = "1.0.0"
        package['release'] = "15.el6"

        # find 1 package
        rpm_to_install = '/var/www/html/rhel/foo.rpm'
        ret = repo.get_rpm(package)
        self.assertEqual(rpm_to_install, ret)
        # find 1 package even with multiple releases
        package['name'] = "foo3"
        package['version'] = "1.0.1"
        package['release'] = "r2"
        rpm_to_install = '/var/www/html/litp/foo3_r2.rpm'
        ret = repo.get_rpm(package)
        self.assertEqual(rpm_to_install, ret)

        # find 1+ packages
        # multi arches
        package['name'] = "foo3"
        package['version'] = "1.0.1"
        package['release'] = "r1"
        message = "Package 'foo3' has errors on the definition. Defined properties '['Release: r1', 'Version: 1.0.1']'. Multiple architectures for this package. Found: 'x86_64' 'i686' "
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)

        # name, _, release, _ invalid as we validate before if version is set

        # name, _, _, arch
        package['name'] = "foo"
        package['version'] = None
        package['release'] = None
        package['arch'] = "x86_64"
        # find 1 package
        rpm_to_install = '/var/www/html/rhel/foo.rpm'
        ret = repo.get_rpm(package)
        self.assertEqual(rpm_to_install, ret)
        # find 1+ package
        package['name'] = "foo3"
        message = "Package 'foo3' has errors on the definition. Defined properties '['Arch: x86_64']'. Multiple releases for this package. Found: 'r1' 'r2' "
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)

        package['name'] = "foo2"
        message = "Package 'foo2' has errors on the definition. Defined properties '['Arch: x86_64']'. Multiple versions for this package. Found: '1.0.1' '1.0.2' "
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)

        # name, verion, _, arch
        package['name'] = "foo"
        package['version'] = '1.0.0'
        package['release'] = None
        package['arch'] = "x86_64"
        # find 1 package
        rpm_to_install = '/var/www/html/rhel/foo.rpm'
        ret = repo.get_rpm(package)
        self.assertEqual(rpm_to_install, ret)
        # find 1+ package
        package['name'] = "foo3"
        package['version'] = '1.0.1'
        message = "Package 'foo3' has errors on the definition. Defined properties '['Version: 1.0.1', 'Arch: x86_64']'. Multiple releases for this package. Found: 'r1' 'r2' "
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)

        package['arch'] = "i686"
        message = "Package 'foo3' has errors on the definition. Defined properties '['Version: 1.0.1', 'Arch: i686']'. Multiple releases for this package. Found: 'r1' 'r2' "
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)

        package['name'] = "foo3"
        package['version'] = u'1.0.1.1.1'
        message = "RPM 'foo3' with properties '['Version: 1.0.1.1.1', 'Arch: i686']' not valid. No package with '['Version: 1.0.1.1.1']' available on repository 'OS'"
        self.assertRaisesWithMessage(Exception, message, repo.get_rpm,package)