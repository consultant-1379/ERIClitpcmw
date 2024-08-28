##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from time import sleep

from litp.core.litp_logging import LitpLogger
from cmwplugin.campaign.cmw_exceptions import CampaignRunnerException
#import cmwplugin.execution
from cmwplugin.campaign import cmw_constants
from cmwplugin.cmw_mco_api import CmwMcoApi

log = LitpLogger()


class CampaignRunner(object):
    '''
    CampaignRunner Class is responsible for transferring campaign .sdp
    files to the managed node and execute cmw commands to import and
    execute the campaign
    '''

    def __init__(self, desthost, destpath):
        self.destpath = destpath
        self.desthost = desthost
        self.cmw_mco_cmd = CmwMcoApi()
        self.cmw_mco_cmd.set_node(desthost)

    def get_campaign_status(self, campaign):
        '''
        retrieves the status of the campaign
        :param campaign: name of CMW campaign
        :type  campaign: string
        '''
        status = self.cmw_mco_cmd.get_campaign_status(campaign)
        return status

    def start_campaign(self, campaign):
        '''
        starts a campaign on remote node
        :param campaign: name of CMW campaign
        :type  campaign: string
        '''
        log.trace.info("start_campaign: starting %s" % campaign)
        self.cmw_mco_cmd.start_campaign(campaign)
        log.trace.info("Campaign %s started successfully" % campaign)

    def commit_campaign(self, campaign):
        '''
        commits a campaign on remote node
        :param campaign: name of CMW campaign
        :type  campaign: string
        '''
        log.trace.info("commit_campaign: committing %s" % campaign)
        self.cmw_mco_cmd.commit_campaign(campaign)
        log.trace.info("Campaign %s committed successfully" % campaign)

    def persist_campaign(self):
        '''
        triggers a cmw configuration persist on remote node
        '''
        log.trace.info("Persist_configuration for CMW")
        self.cmw_mco_cmd.persist_configuration()

    def remove_campaign(self, campaign):
        '''
        triggers a remove of campaign on remote node
        :param campaign: name of CMW campaign
        :type  campaign: string
        '''
        log.trace.info("remove_campaign: removing %s" % campaign)
        self.cmw_mco_cmd.remove_campaign(campaign)
        log.trace.info("Campaign %s removed successfully" % campaign)

    def execute_campaign(self, campaign):
        '''
        Verifies that a campaign goes from Initial to Committed
        state
        :param campaign: name of CMW campaign
        :type  campaign: string
        '''
        try:
            log.trace.info("execute_campaign: executing %s on node %s"
                           % (campaign, self.desthost))
            status = self.get_campaign_status(campaign)
            if status == "INITIAL":
                self.start_campaign(campaign)
                status = self.get_campaign_status(campaign)
                while status != "COMPLETED":
                    sleep(cmw_constants.CAMPAIGN_SLEEP_SECONDS)
                    status = self.get_campaign_status(campaign)
                self.commit_campaign(campaign)
                while status != "COMMITTED":
                    sleep(cmw_constants.CAMPAIGN_SLEEP_SECONDS)
                    status = self.get_campaign_status(campaign)
                self.persist_campaign()
                self.remove_campaign(campaign)
            else:
                log.trace.error("Campaign %s in incorrect state on node %s"
                                % (campaign, self.desthost))
                raise CampaignRunnerException("Campaign %s in incorrect "
                                              "state on node %s"
                                              % (campaign, self.desthost))
        except CampaignRunnerException as ex:
            log.trace.error("execute_campaign: got exception " + str(ex))
            raise ex
