define cmw::configure($tarball){
    file { 'tarball':
        ensure  => file,
        path    => '/root/CMW/.tar',
        mode    => '0644',
        owner   => root,
        group   => root,
        source  => 'puppet:///modules/cmw/$tarball',
        require => File['CMWdir'],
    }

    file { 'CMWdir':
        ensure  => directory,
        path    => '/root/CMW',
        mode    => '0755',
        owner   => root,
        group   => root,
    }

    exec { 'untar':
        command => 'tar -xvf $tarball',
        path    => '/bin/',
        require => File['tarball', 'CMWdir'],
        cwd     => '/root/CMW',
    }

}

