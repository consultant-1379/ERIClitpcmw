require 'open3'

def get_system_path
    res = %x[source /etc/profile;  facter | grep path]
    path =  res.split("=>").last
    return path
end

module MCollective
  module Agent
    class Cmw_utils<RPC::Agent

      action "lde_config" do
        cmd = %{lde-config --create}

        reply[:retcode] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      action "execute_script" do
        path = request[:path]
        script_name = request[:script_name]

#        cmd = %{sh } + path + "/" + script_name
        cmd = %{sh } + script_name

        reply[:retcode] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true,
                              :cwd => path,
                             :environment => {"PATH" => get_system_path})
      end

      action "rpm_dry_run" do
        implemented_by("/tmp/cmw_helper.py")
      end

      action "create_directory" do
        path = request[:path]

        cmd = %{mkdir -p } + path

        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      action "unpack_tarfile" do
        path = request[:path]
        destpath = request[:destpath]
        filename = request[:filename]

        cmd = %{tar -xvf } + path + "/" + filename + " --dir " + destpath

        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      action "check_file_exists" do
        path = request[:path]
        filename = request[:filename]

        cmd = %{test -f } + path + "/" + filename

        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      action "delete_file" do
        path = request[:path]
        filename = request[:filename]

        cmd = %{rm -f } + path + "/" + filename

        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      action "give_file_execute_permission" do
        path = request[:path]
        filename = request[:filename]

        cmd = %{chmod +x } + path + "/" + filename

        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      action "reboot_machine" do
        cmd = %{shutdown -r now}
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end
    end

  end
end

