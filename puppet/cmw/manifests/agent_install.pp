define cmw::agent_install() {
  
  file { "/usr/share/litp/":
    ensure => "directory",
}

  file { 'cmw_helper':
    ensure => file,
    path   => '/usr/share/litp/cmw_helper.py',
    source => 'puppet:///modules/cmw/cmw_helper.py',
    owner  => root,
    group  => root,
    mode   => '0744',
  }
  }