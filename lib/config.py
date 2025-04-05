from pathlib import Path
import json
import os
from os.path import exists, isfile
from lib.logging import logger


class Config:
    """
    Class for parsing JSON config files
    """
    def __init__(self, config_file: str = ""):
        self.config_file = config_file
        self.data = self.Read()

        # Check if there is any data found
        if self.data is None:
            logger.critical("Configuration file could not be processed")
            logger.info("Exitting")
            exit(1)

        # General settings
        self.tmp_dir = self.GetOption('general', 'tmpDir')
        self.destination = self.GetOption('general', 'destination')
        self.wordpress = self.GetOption('general', 'wordpressBackup')
        self.database = self.GetOption('general', 'databaseBackup')

        # Worpress settings
        self.host = self.GetOption('wordpress', 'host')
        self.port = self.GetOption('wordpress', 'port')
        self.username = self.GetOption('wordpress', 'username')
        self.priv_key = self.GetOption('wordpress', 'privateKey')
        self.src = self.GetOption('wordpress', 'source')
        self.wp_dest = self.GetOption('wordpress', 'dest')

        # Database settings
        self.dbuser = self.GetOption('database', 'dbUser')
        self.dbname = self.GetOption('database', 'dbName')
        self.db_dest = self.GetOption('database', 'dbDest')

    def Read(self):
        """ Method for reading JSON config files"""
        path = Path('__main__')
        root_dir = path.parent.absolute()
        config_location = os.path.join(root_dir, self.config_file)
        data = None

        try:
            # Check extention
            if self.config_file.endswith('.json') is False:
                return None

            # Check if the file actually exists
            if exists(self.config_file) is True and isfile(self.config_file):

                # Read file and convert to DICT
                with open(config_location, 'r') as file:
                    data = json.load(file)
            return data
        except IOError as ioe:
            logger.error("Reading configuration file failed: %s", ioe)
            logger.info("Exitting")
            exit(1)

    def GetSection(self, section):
        """Get configuration section"""
        try:
            # Check of key exists
            if section in self.data:
                logger.debug("Found section %s", section)
                return self.data[section]
        except ValueError:
            logger.error("Cannot find section %s", section)

    def GetOption(self, section, option):
        """Get value from option in section"""
        try:
            var = []

            # Get section data and enumerate through it
            section = self.GetSection(section)
            if section is None:
                raise ValueError(
                        "Section {section} not found")
                logger.error("Section %s not found")

            for index, _ in enumerate(section):
                # Loop through data and search for option
                # the value of option will be saved when
                # search is successful
                for opt in section[index]:
                    if opt == option:
                        var = section[index].get(opt)
            logger.debug("option: %s, value: %s", option, var)
            return var
        except ValueError:
            logger.error("Parsing configuration file failed")
            exit(1)
