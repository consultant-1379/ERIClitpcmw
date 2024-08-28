##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import os
from hashlib import md5

from litp.core.litp_logging import LitpLogger
from cmwplugin.cmw_mco_api import CmwMcoApi

log = LitpLogger()


class cmwExecutionManager(object):
    '''
    Manages the collection of information from the model
    '''
    def __init__(self, primary_node):
        self.primary_node = primary_node
        self.cmw_mco_cmd = CmwMcoApi()

    def check_if_file_on_node(self, abs_file_name, nodes):
        """
        :summary: Validate that the supplied file is present on the
                clustered-service nodes
        :param abs_file_name: absolute file Name
        :type abs_file_name: string

        :param cs: cs dict
        """
        result = True

        path, filename = os.path.split(abs_file_name)
        for node in nodes:
            self.cmw_mco_cmd.set_node(node)
            rc = self.cmw_mco_cmd.check_file_exists(path, filename)
            if not rc:
                log.trace.debug("Failed to find %s on %s" % (abs_file_name,
                                                             node))
                result = False
                break
        return result

    def import_sdps(self, node, *filenames):
        '''
        triggers a cmw import of the campaign sdp file
        :param filenames: list of files to be imported
        :type  filenames: list
        '''
        self.cmw_mco_cmd.set_node(node)
        if len(filenames) == 0:
            error_msg = "No files to import"
            log.trace.error(error_msg)
            raise Exception(error_msg)

        for filename in filenames:
            log.trace.info("Importing %s" % filename)
            self.cmw_mco_cmd.import_sdp(filename, destpath="/tmp")
            self.cmw_mco_cmd.delete_file("/tmp", filename)

    def transfer_files(self, dest_host, ms_ip, dest_path, filepath, *files):
        '''
        Copies files to a node and verify their integrity
        :param filenames: list of files to be imported
        :type  filenames: list
        '''

        self.cmw_mco_cmd.set_node(dest_host)
        if len(files) == 0:
            log.trace.error("No files to transfer")
            raise Exception("No files to transfer")

        for filename in files:
            log.trace.info("Copying file %s" % filename)

#            result = self.copy(dest_host, filename, dest_path)
            dest_md5 = self.cmw_mco_cmd.transfer_sdp(dest_host,
                                                     dest_path,
                                                     filepath,
                                                     filename,
                                                     ms_ip)

#           if not result[0] == 0:
#               error_msg = ("Unable to copy %s to %s" % (filename, dest_host))
#               log.trace.error(error_msg)
#               raise Exception(error_msg)

            with open(filepath + "/" + filename) as loc_file:
                file_data = loc_file.read()
                loc_md5 = md5(file_data).hexdigest()

                if not loc_md5 == dest_md5:
                    error_msg = " Copy failed, md5sum does not match"
                    log.trace.error(error_msg)
                    raise Exception(error_msg)
