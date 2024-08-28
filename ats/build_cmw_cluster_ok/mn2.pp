
class task_mn2__cmw_3a_3aagent__install__agent__install(){
    cmw::agent_install { "agent_install":

    }
}

class task_mn2__cmw_3a_3alde__lde_2dconfig(){
    cmw::lde { "lde-config":
cluster => {
        msSubnetIP => "10.10.10.1",
        internalNetwork => "10.10.10.0/24",
        bootIP => "10.46.86.1",
        netID => "1234",
        'quick-reboot' => "off",
        controlInterface => "eth0",
        msHostname => "ms1"
        },
nodes => [
{
        nodetype => "control",
        nodenumber => "1",
        ip => "10.10.10.101",
        hostname => "mn1",
        tipcaddress => "1.1.1",
hb_interface_list => {
        eth3 => "08:00:27:21:7D:BC",
        eth2 => "08:00:27:06:C0:61"
        },
interface_list => {
        eth3 => "08:00:27:21:7D:BC",
        eth2 => "08:00:27:06:C0:61",
        eth0 => "08:00:27:5B:C1:3F"
        },
        primarynode => "True"
        },
{
        nodetype => "control",
        nodenumber => "2",
        ip => "10.10.10.102",
        hostname => "mn2",
        tipcaddress => "1.1.2",
hb_interface_list => {
        eth3 => "08:00:27:21:7D:B3",
        eth2 => "08:00:27:06:C0:62"
        },
interface_list => {
        eth3 => "08:00:27:21:7D:B3",
        eth2 => "08:00:27:06:C0:62",
        eth0 => "08:00:27:5B:C1:31"
        },
        primarynode => "False"
        }
        ]

    }
}

class task_mn2__cmw_3a_3aresource__agents__resource_2dagents(){
    cmw::resource_agents { "resource-agents":

    }
}

class task_mn2__ssh_3a_3arootconfig__ssh_2drootconfig(){
    ssh::rootconfig { "ssh-rootconfig":
        client => "true",
        server => "true"
    }
}


node "mn2" {

    class {'litp::mn_node':
        ms_hostname => "ms1",
        cluster_type => "CMW"
        }


    class {'task_mn2__cmw_3a_3aagent__install__agent__install':
    }


    class {'task_mn2__cmw_3a_3alde__lde_2dconfig':
        require => [Class["task_mn2__cmw_3a_3aagent__install__agent__install"],Class["task_mn2__cmw_3a_3aresource__agents__resource_2dagents"],Class["task_mn2__ssh_3a_3arootconfig__ssh_2drootconfig"]]
    }


    class {'task_mn2__cmw_3a_3aresource__agents__resource_2dagents':
    }


    class {'task_mn2__ssh_3a_3arootconfig__ssh_2drootconfig':
    }


}