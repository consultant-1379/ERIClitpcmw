metadata    :name        => "cmw_utils",
            :description => "Commands required while installing CMW ",
            :author      => "Ericsson AB",
            :license     => "Ericsson AB 2014",
            :version     => "1.0",
            :url         => "http://ericsson.com/",
            :timeout     => 600

action "lde_config", :description => "execute lde-config" do
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

action "execute_script", :description => "Execute shell script" do
    display :always

    input  :path,
           :prompt      => "Path",
           :description => "The location of the file",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :script_name,
           :prompt      => "The name of the script",
           :description => "The script to be executed",
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

action "rpm_dry_run", :description => "Create a directory" do
    display :always

    input  :path,
           :prompt      => "Path",
           :description => "The name of directory to be created",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :sdp_name,
           :prompt      => "The name of the script",
           :description => "The script to be executed",
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

action "create_directory", :description => "Create a directory" do
    display :always

    input  :path,
           :prompt      => "Path",
           :description => "The name of directory to be created",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
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

action "unpack_tarfile", :description => "Untar a file" do
    display :always

    input  :path,
           :prompt      => "Path",
           :description => "The location of the file",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :destpath,
           :prompt      => "Destination path",
           :description => "The location where the file should be unpacked",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :filename,
           :prompt      => "File",
           :description => "The file to be unpacked",
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

action "check_file_exists", :description => "Determine if a given file exists" do
    display :always

    input  :path,
           :prompt      => "Path",
           :description => "The location of the file",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :filename,
           :prompt      => "File",
           :description => "The file to be checked",
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

action "delete_file", :description => "Delete the specified file" do
    display :always

    input  :path,
           :prompt      => "Path",
           :description => "The location of the file",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :filename,
           :prompt      => "File",
           :description => "The file to be deleted",
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

action "give_file_execute_permission", :description => "Run chmod on a file" do
    display :always

    input  :path,
           :prompt      => "Path",
           :description => "The location of the file",
           :type        => :string,
           :validation  => '^((?:[a-zA-Z]\:){0,1}(?:[\\/][\w.-]+){1,})$',
           :optional    => false,
           :maxlength   => 60

    input  :filename,
           :prompt      => "File",
           :description => "The file to be checked",
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

action "reboot_machine", :description => "Reboot machine" do
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

