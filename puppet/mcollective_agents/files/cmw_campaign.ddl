metadata    :name        => "cmw_campaign",
            :description => "Actions on a CMW campaign",
            :author      => "Ericsson AB",
            :license     => "Ericsson AB 2014",
            :version     => "1.0",
            :url         => "http://ericsson.com/",
            :timeout     => 10

action "get_status", :description => "Get the status of a CMW campaign" do
    display :always

    input  :campaign_name,
           :prompt      => "The name of the capaign",
           :description => "The campaign whose status is to be checked",
           :type        => :string,
           :validation  => '^[\w\-\.]+$',
           :optional    => false,
           :maxlength   => 60

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end

action "check_cmw_ready", :description => "Checks if CMW is running" do
    display :always

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end

action "check_component_installed", :description => "Checks if a component is installed" do
    display :always

    input  :component_name,
           :prompt      => "The name of the component",
           :description => "The component to be checked",
           :type        => :string,
           :validation  => '^[\w\-\.]+$',
           :optional    => false,
           :maxlength   => 60

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end

action "transfer_sdp_files", :description => "Transfer sdp files using curl" do
    display :always

    input  :relative_path,
           :prompt      => "File location",
           :description => "The location of the file",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :dest_path,
           :prompt      => "Dest Path",
           :description => "The location of the file",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :filename_list,
           :prompt      => "Filenames",
           :description => "List of files to be transferred",
           :type        => :string,
           :validation  => '^[\w\-\.]+(,[\w\-\.]+)*$',
           :optional    => false,
           :maxlength   => 200

    input  :md5_checksum_list,
           :prompt      => "md5 List",
           :description => "List of md5 values for files to be transferred",
           :type        => :string,
           :validation  => '^[\w\-\.]+(,[\w\-\.]+)*$',
           :optional    => false,
           :maxlength   => 200

    input  :ms_ip_addr,
           :prompt      => "MS IP Addr",
           :description => "IP addr for MS from where files are transferred",
           :type        => :string,
           :validation  => '',
           :optional    => false,
           :maxlength   => 200

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

    output :md5sum,
           :description => "The md5 value for the file",
           :display_as => "md5sum"

end

action "import_sdp_files", :description => "Import sdp files using cmw-sdp-import" do
    display :always

    input  :dest_path,
           :prompt      => "Dest Path",
           :description => "The location of the file",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :sdp_list,
           :prompt      => "SDPs",
           :description => "List of sdp files to be imported",
           :type        => :string,
           :validation  => '^[\w\-\.]+(,[\w\-\.]+)*$',
           :optional    => false,
           :maxlength   => 200

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end

action "start_campaign", :description => "Start a campaign using cmw-campaign-start" do
    display :always

    input  :campaign_name,
           :prompt      => "Campaign",
           :description => "Name of CMW campaign to be started",
           :type        => :string,
           :validation  => '^[\w\-\.]+$',
           :optional    => false,
           :maxlength   => 60

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end

action "commit_campaign", :description => "Commit a campaign using cmw-campaign-commit" do
    display :always

    input  :campaign_name,
           :prompt      => "Campaign",
           :description => "Name of CMW campaign to be committed",
           :type        => :string,
           :validation  => '^[\w\-\.]+$',
           :optional    => false,
           :maxlength   => 200

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end

action "remove_campaign", :description => "Remove a campaign using cmw-sdp-remove" do
    display :always

    input  :campaign_name,
           :prompt      => "Campaign",
           :description => "Name of CMW campaign to be removed",
           :type        => :string,
           :validation  => '^[\w\-\.]+$',
           :optional    => false,
           :maxlength   => 200

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end

action "persist_configuration", :description => "Persist the configuration using cmw-configuration-persist" do
    display :always

    output :retcode,
           :description => "The exit code from running the command",
           :display_as => "Result code"

    output :out,
           :description => "The stdout from running the command",
           :display_as => "out"

    output :err,
           :description => "The stderr from running the command",
           :display_as => "err"

end
