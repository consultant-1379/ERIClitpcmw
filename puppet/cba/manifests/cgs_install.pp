define cba::cgs_install {
  yumrepo { 'cba.repo':
    name     => 'CBA',
    baseurl  => 'file:///var/www/html/cba/rpms',
    enabled  => 1,
    gpgcheck => 0,
    metadata_expire => 0,
  }

  package {'amf-cgs':
    ensure  => 'installed',
    require => Yumrepo['cba.repo']
  }
}
