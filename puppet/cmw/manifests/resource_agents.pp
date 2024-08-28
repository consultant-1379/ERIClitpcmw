define cmw::resource_agents($ensure='installed') {

  package { 'EXTRlitpresourceagents':
    ensure => $ensure,
  }
}

