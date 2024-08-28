#  Puppet Manifest file for lde
# EXAMPLE
#               $nodes=[{ nodenumber  => '1',
#                         hostname    => 'SC-1',
#                         nodetype    => 'control',
#                         interface   => 'eth0',
#                         macaddress  => 'XX:XX:XX:XX:XX:XX',
#                         tipcaddress => '1.1.1'
#                       },{
#                         nodenumber  => '2',
#                         hostname    => 'SC-2',
#                         nodetype    => 'control',
#                         interface   => 'eth0',
#                         macaddress  => 'XX:XX:XX:XX:XX:XX',
#                         tipcaddress => '1.1.2'
#                       },{
#                         nodenumber  => '3',
#                         hostname    => 'PL-3',
#                         nodetype    => 'payload',
#                         interface   => 'eth0',
#                         macaddress  => 'XX:XX:XX:XX:XX:XX',
#                         tipcaddress => '1.1.3'
#                       },{
#                         nodenumber  => '4',
#                         hostname    => 'PL-4',
#                         nodetype    => 'payload',
#                         interface   => 'eth0',
#                         macaddress  => 'XX:XX:XX:XX:XX:XX',
#                         tipcaddress => '1.1.4'
#                       }],
#               $cluster= { internalNetwork  => '10.46.80.0/21',
#                           defaultNetwork   => '0.0.0.0/0',
#                           controlInterface => 'eth0',
#                           msHostname       => 'ms1',
#                           bootIP           => '10.46.86.1',
#                           netID            => '4711',
#                           timezone         => 'Europe/Dublin'
#                         },
define cmw::lde($nodes, $cluster,
                #update the below hash if upgrade of lde occurs,
                #change via lde plugin
                $package_versions = { lde-cmwea            => 'installed',
                                      lde-monitored-dhcpd  => 'installed',
                                      lde-global-users     => 'installed',
                                      tipc-km              => 'installed'
                      },


                #tipc-km is used with the kernel version,
                #so needs to be defined here.
                #If kernel changes this will need to change also.
                $tipckm_label='tipc-km-2.6.32_220.el6.x86_64-R*'
                ) {

  $msHostname = $cluster['msHostname']

  yumrepo { 'lde.repo':
    name => 'LDE',
    baseurl  => "http://$msHostname/cba/rpms",
    enabled  => 1,
    gpgcheck => 0,
    before   => [Package['lde-cmwea'], Package['tipc-km'], Package['lde-global-users'], Package['lde-monitored-dhcpd']],
  }

  package {'parted':
          name => 'parted'
  }

  package {'lde-monitored-dhcpd':
          ensure  => $package_versions[lde-monitored-dhcpd],
          require => Package['parted']
  }

  package {'lde-global-users':
          ensure  => $package_versions[lde-global-users],
  }

  package {'lde-cmwea':
          ensure  => $package_versions[lde-cmwea],
          require => Package['tipc-km']
  }

  package { 'tipc-km':
          ensure  => $package_versions[tipc-km],
          name    => $tipckm_label,
  }

  file { 'cluster.group':
    ensure => 'present',
    path   => '/cluster/etc/group',
    noop   => true,
  }

  #tune2fs is something we can test to replace e2label
  exec { 'lde_boot':
    path     => '/usr/bin:/usr/sbin:/bin:/sbin',
    command  => 'tune2fs -L lde_boot  $(mount | grep /boot |
      awk \'{print $1}\')',
    unless   => 'tune2fs -l  $(mount | grep /boot |
                  awk \'{print $1}\') | grep lde_boot',
  }

  service { 'lde-dhcpd':
    enable => false
  }

  service { 'lde-ckcfg':
    enable => false
  }

  file {'lde_disk_boot':
      ensure  => present,
      path    => '/etc/udev/rules.d/99-lde-disk_boot.rules',
      mode    => '0644',
      content => 'ID_FS_LABEL=="lde_boot", SYMLINK+="disk_boot"'
    }

}
