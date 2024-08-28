require 'open3'

def get_system_path
    res = %x[source /etc/profile;  facter | grep path]
    path =  res.split("=>").last
    return path
end

module MCollective
  module Agent
    class Cmw_campaign<RPC::Agent
      #Ensure cmw is install on the node
      action "check_cmw_ready" do
        campaign = request[:campaign_name]
        cmd = %{cmw-status node}
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      # Import the sdp files
      action "transfer_sdp_files" do
        path = request[:relative_path]
        destpath = request[:dest_path]
        file = request[:filename_list]
        ms_ip = request[:ms_ip_addr]

        cmd = %{mkdir } + destpath
        retcode= run("#{cmd}",
                     :environment => {"PATH" => get_system_path})
        cmd = %{curl http://} + ms_ip + %{/} + path + "/" + file +
          " -o " + destpath + "/" + file
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
        cmd = %{md5sum } + destpath + "/" + file
        sout = ""
        serr = ""
        status = run(cmd, :stdout => sout,
                          :stderr => serr,
                          :chomp => true,
                          :environment => {"PATH" => get_system_path})
        reply[:md5sum] = sout.split(/ /)[0]
      end

      # Import the sdp files 
      action "import_sdp_files" do
        destpath = request[:dest_path]
        campaign = request[:sdp_list]
        cmd = %{cmw-sdp-import } + destpath + %{/} + campaign
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      #Start an installation of a campaign using cmw
      action "start_campaign" do
        campaign = request[:campaign_name]
        cmd = %{cmw-campaign-start --disable-backup } + campaign
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end
   
      # get the status of a campaign
      action "get_status" do
        campaign = request[:campaign_name]
        cmd = %{cmw-campaign-status } + campaign
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      #Check if component is already installed, using cmw-repository-list
      action "check_component_installed" do
        component = request[:component_name]
        cmd = %{cmw-repository-list | grep } + component + %{ | awk '{print $2}'}
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      #Commit a campaign using cmw-campaign-commit
      action "commit_campaign" do
        campaign = request[:campaign_name]
        cmd = %{cmw-campaign-commit } + campaign
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      #Persist a campaign using cmw-configuration-persist
      action "persist_configuration" do
        cmd = %{cmw-configuration-persist}
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end

      #Remove a campaign with cmw-campaign-remove
      action "remove_campaign" do  
        campaign = request[:campaign_name]
        cmd = %{cmw-sdp-remove } + campaign
        reply[:retcode] = run("#{cmd}",
                             :stdout => :out,
                             :stderr => :err,
                             :chomp => true,
                             :environment => {"PATH" => get_system_path})
      end
    end

  end
end
