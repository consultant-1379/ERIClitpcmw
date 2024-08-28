#  Puppet Manifest file for cluster_conf
define cmw::cluster_conf($nodes, $cluster,
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
                ) {

  file { '/cluster/etc/':
    ensure  => directory,
  }

  # replace=>true will only cause puppet to update the cluster.conf
  # on a node if there is an update to the the file. Otherwise
  # it wont add a new cluster.conf on each node after the first one
  file { 'cluster.conf':
    ensure  => file,
    require => File['/cluster/etc/'],
    content => template('cmw/cluster.conf.erb'),
    path    => '/cluster/etc/cluster.conf',
    owner   => nobody,
    group   => nobody,
    replace => true,
  }

}

