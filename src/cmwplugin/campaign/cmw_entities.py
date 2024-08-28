##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################


class cmwApp(object):
    '''
    class representing an Application in the context of CMW
    '''
    def __init__(self, name):
        '''
        Constructor
        '''
        self.name = name
        self.service_groups = []


class cmwServiceGroup(object):
    '''
    class representing a Service Group in the context of CMW
    '''

    def __init__(self, name, version):
        '''
        Constructor
        '''
        self.name = name
        self.version = version
        # FIXME need to group SG's using AppType
        self.app_name = 'Litp_App'
        self.su_type = '-'.join([self.name, "SuType"])
        self.svc_type = '-'.join([self.name, "SvcType"])
        self.service_instances = []
        self.comps = []
        self.bundles = []
        self.dependency = []
        self.node_list = []
        self.availability_model = None
        self.active_count = None
        self.standby_count = None
        self.etf_file = None
        self.install_source = None


class cmw2NServiceGroup(cmwServiceGroup):

    def __init_(self, name, version):
        super(cmw2NServiceGroup, self).__init__(name, version)
        self.active_count = 1
        self.standby_count = 1


class cmwNWayActiveServiceGroup(cmwServiceGroup):

    def __init_(self, name, version, active_count):
        super(cmwNWayActiveServiceGroup, self).__init__(name, version)
        self.active_count = active_count
        self.standby_count = 0
        self.install_source = None


class cmwComponent(object):

    def __init__(self, comp_name, base_name, version):
        self.type = None
        #TODO: deal with version
        self.version = version
        self.name = base_name + "_" + comp_name
        self.cs_type = self.name + "-CsType"
        self.comp_type = self.name + "-CompType"
        self.start_command = None
        self.stop_command = None
        self.status_command = None
        self.cleanup_command = None


class cmwLSBComponent(cmwComponent):

    def __init__(self, comp_name, base_name, version, service_name,
                 cleanup_cmd):
        super(cmwLSBComponent, self).__init__(comp_name, base_name, version)
        self.start_command = "../sbin/service %s start" % service_name
        self.stop_command = "../sbin/service %s stop" % service_name
        self.status_command = "../sbin/service %s status" % service_name
        self.cleanup_command = ".." + cleanup_cmd
        self.service_name = service_name


class cmwJBossComponent(cmwComponent):

    def __init__(self, comp_name, base_name, version, cleanup_cmd):
        super(cmwJBossComponent, self).__init__(comp_name, base_name, version)
        litp_jboss_location = "../opt/ericsson/nms/litp/bin/litp-jboss "
        self.start_cmd = litp_jboss_location + "start"
        self.stop_cmd = litp_jboss_location + "stop"
        self.status_cmd = litp_jboss_location + "status"
        self.cleanup_cmd = ".." + cleanup_cmd


class cmwVipComponent(cmwComponent):

    def __init__(self):
        super(cmwVipComponent, self).__init__()


class cmwServiceUnit(object):

    def __init__(self, name):
        self.name = name


class cmwServiceInstance(object):

    def __init__(self, name):
        self.name = name
