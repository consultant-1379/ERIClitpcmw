
class task_ms1__cba_3a_3acgs__install__cgs_2dinstall(){
    cba::cgs_install { "cgs-install":

    }
}

class task_ms1__ssh_3a_3arootconfig__ssh_2drootconfig(){
    ssh::rootconfig { "ssh-rootconfig":
        client => "false",
        master => "true",
        server => "false"
    }
}


node "ms1" {

    class {'litp::ms_node':}


    class {'task_ms1__cba_3a_3acgs__install__cgs_2dinstall':
    }


    class {'task_ms1__ssh_3a_3arootconfig__ssh_2drootconfig':
    }


}