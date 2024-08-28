##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import ConfigParser
import os

from litp.core.litp_logging import LitpLogger
from cmwplugin.campaign import cmw_constants
log = LitpLogger()


class cmwConfig(object):
    '''
    Read configuration file and offers wrapper functions for the
    cba components
    '''

    def __init__(self, config_file=None):
        '''
        Creates the config object

        :param config_file: Path to the configuration file
        :type config_file: string
        '''
        data_path = cmw_constants.LITP_DATA_DIR
        if config_file is None:
            config_file = "cmw_data.conf"
            self.config_file = os.path.join(data_path, config_file)
        else:
            self.config_file = config_file
        self.config = ConfigParser.SafeConfigParser()

    def read_plugin_config(self, section, option):
        """
        Read an option from the current config file.
        Raise an exception if it fails

        :param section: Section to read from the config file
        :type section: string
        :param option: Option to read from the config file
        :type option: string
        """
                # config.read doesn't raise an exception when it fails,
        # so need to check return type is not of len zero
        dataset = self.config.read(self.config_file)
        if len(dataset) == 0:
            log.trace.error("Failed to open %s" % self.config_file)
            raise Exception("cmwConfig failed to read")
        try:
            value = self.config.get(section, option)
        except ConfigParser.NoOptionError:
            return None
        except ConfigParser.Error as error:
            # log.trace.exception("%s : read_config exception: %s"
            #% (self.component, error))
            log.trace.error("Exception Error '{0}' happened while reading"
                            " option '{1}' from section '{2}' of CMW"
                            " plugin config file".format(
                                                  error,
                                                  option,
                                                  section)
                            )
            raise Exception("Failed to read plugin config")
        return value

    def write_plugin_config(self, section, option, value):
        """
        Write an option from the current config file.
        Raise an exception if it fails

        :param section: Section to write to the config file
        :type section: string
        :param option: Option to write to the config file
        :type option: string
        :param value: Value to write to the config file
        :type value: string
        """
        try:
            with open(self.config_file, 'rb') as configfile:
                self.config.readfp(configfile)
            self.config.set(section, option, value)
            with open(self.config_file, 'wb') as configfile:
                self.config.write(configfile)
        except ConfigParser.Error as error:
            log.trace.error("Exception Error '{0}' happened while writing"
                            " option '{1}' to section '{2}' of CMW"
                            " plugin config file".format(
                                                  error,
                                                  option,
                                                  section)
                            )
            raise Exception("Failed to write plugin config")
        return value
