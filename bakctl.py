#!/usr/bin/env python3
"""
Dit script is voor het maken van backups van:
- Wordpress installatie
- MySQL database dmv dbdump
"""

__version__ = '0.1'
__author__ = 'Chris Dorsmam'

from sys import exit, argv
from datetime import datetime
import os
from os.path import exists, isfile
import tarfile
import subprocess
import hashlib
import logging
from shutil import which
import paramiko
import paramiko.auth_strategy
from scp import SCPClient
import itertools
import json
from pathlib import Path
from io import StringIO

logger = logging.getLogger(__name__)

date: str = datetime.today().strftime('%Y%m%d%H%M%S')
files: dict = {}
dbdump_opts = ""


def get_db_client():
    """
    Function is to find mysqldump or mariadb-dump
    When not found it will log error and exit
    """
    try:
        return which("mysqldump") or which("mariadb-dump")
    # If database cannot be found throw exception and exit
    except ValueError as ve:
        logger.error("Cannot find MariaDB or MySQL client: %s", ve)
        exit(1)


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
        path = Path(__file__)
        root_dir = path.parent.absolute()
        config_location = os.path.join(root_dir, self.config_file)
        data = None

        # Check extention
        if self.config_file.endswith('.json') is False:
            return None

        # Check if the file actually exists
        if exists(self.config_file) is True and\
                isfile(self.config_file):

            # Read file and convert to DICT
            with open(config_location, 'r') as file:
                data = json.load(file)
        return data

    def GetSection(self, section):
        """Get configuration section"""
        try:
            # Check of key exists
            if section in self.data:
                logger.info("Found section %s", section)
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

            for index, _ in enumerate(section):
                # Loop through data and search for option
                # the value of option will be saved when
                # search is successful
                for opt in section[index]:
                    if opt == option:
                        var = section[index].get(opt)
            logger.info("option: %s, value: %s", option, var)
            return var
        except ValueError:
            logger.error("Error parsing configuration file")
            exit(1)


class Bakctl(object):
    def __init__(
            self,
            host: str = "",
            port: int = 0,
            username: str = "",
            priv_key: str = "",
            dbusername: str = "",
            database: str = "",
            tmp: str = "",
            source: str = "",
            destination: str = ""):
        self.host: str = host
        self.port: int = port
        self.username: str = username
        self.priv_key: str = priv_key
        self.dbusername: str = dbusername
        self.source: str = source
        self.tmp: str = tmp
        self.destination: str = destination
        self.database: str = database
        self.source_hash: dict = {}
        self.dest_hash: dict = {}
        self.dbdump_exec: str = get_db_client()
        self.dbdump_opts = ""

        self.dbdump_opts += " -u {0}".format(self.dbusername)
        self.dbdump_opts += " {0}".format(self.database)
        self.dbdump_opts += " -p"

    class SshClient:
        "A wrapper of paramiko.SSHClient"
        TIMEOUT = 4

        def __init__(self,
                     host,
                     port,
                     username,
                     password,
                     key=None,
                     passphrase=None):
            self.username = username
            self.password = password
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(
                                    paramiko.AutoAddPolicy()
                                    )
            # Load private key is provided.
            if key is not None:
                key = paramiko.Ed25519Key\
                                .from_private_key_file(key)

            # .from_private_key(StringIO(key),
            self.client.connect(
                            host,
                            port,
                            username=username,
                            password=password,
                            pkey=key,
                            timeout=self.TIMEOUT)

        # Close SSH-connection
        def close(self) -> None:
            if self.client is not None:
                self.client.close()
                self.client = None

        # execute command through SSH connection
        def execute(self, command, sudo=False) -> dict:
            feed_password = False
            # execute command with sudo if sudo is true
            # and user is not root and password is not empty
            if sudo and self.username != "root":
                command = "sudo -S -p '' %s" % command
                feed_password = self.password is not None\
                    and len(self.password) > 0
            # Capture output, stderr and stdin.
            stdin, stdout, stderr = self.client.exec_command(command)
            # Enter password to sudo
            if feed_password:
                stdin.write(self.password + "\n")
                stdin.flush()
            # return results and return value from execution
            return {'out': stdout.readlines(),
                    'err': stderr.readlines(),
                    'retval': stdout.channel.recv_exit_status()}

        def put(self, filename, destination) -> bool:
            scp = SCPClient(self.client.get_transport())
            scp.put(filename, remote_path=destination)

    class Filehash:
        """Inner class for actions around filehashes"""
        def __init__(self,
                     filename: str = "",
                     remote_file: str = "",
                     host: str = "",
                     port: int = 0,
                     username: str = "",
                     priv_key: str = ""):
            self.host = host
            self.port = port
            self.username = username
            self.priv_key = priv_key
            self.filename = filename
            self.remote_file = remote_file
            self.remote_hash = ""
            self.file_hash = ""

        def calculate_remote_hash(self, filename: str) -> hash:
            """Calculate file hash from remote file"""
            ssh = Bakctl.SshClient(
                        self.host,
                        self.port,
                        self.username,
                        self.priv_key
                    )
            cmd = f'sha256sum {remote_file}'
            stdout_, stdin_, stderr_ = ssh.execute(cmd)
            stdout_.channel.recv_exit_status()
            buffer = stdout_.readlines()

            # Split string of output into list and clean it
            lst = (buffer[0].split(" "))
            lst = [item.strip() for item in lst]
            lst[:] = [item for item in lst if item != '']

            # reverse list and store
            rev = lst[:][::-1]

            # Convert list into dict
            result = dict(
                    itertools.zip_longest(*[iter(rev)] * 2, fillvalue="")
                    )

            client.close()
            return result

        def calculate_hash(self, filename: str = None) -> hash:
            """
            Function calculating the filehash. With the filehash it is
            possible to check and verify the integrity of a file.
            """

            # Create hash object
            hash_object: object = hashlib.sha256()

            # Open the file in binary mode
            with open(filename, 'rb') as file:
                # Read the entire file content
                file_content = file.read()

                # Update the hash object with the file content
                hash_object.update(file_content)

            # Return the hexadecimal representation of the hash
            return hash_object.hexdigest()

    def compress(self,
        """Method for file compression"""
            mode: str = "",
            filename: str = "", 
            source: str = ""):
        match mode:
            case "database":
                backup = os.path.join(self.tmp, f'dbbackup-{date}.tar.gz')
                logger.info("Compressing with tar file %s", backup)
                # Create tarfile with defined name
                with tarfile.open(backup, "w:gz") as tar:
                    logger.info("Compressing file: %s", filename)
                    tar.add(filename)

            case "wordpress":
                # Define tarfile
                backup = os.path.join(self.tmp, f'wpbackup-{date}.tar.gz')
                logger.info("Compressing with tar file %s", backup)

                # Create tarfile with defined name
                with tarfile.open(backup, "w:gz") as tar:
                    # Loop through all files and dirs in self.source
                    # and add them to the tarfile
                    for name in os.listdir(self.source):
                        logger.info("Compressing file: %s", name)
                        tar.add(name)
        return backup

    def create_db_backup(self):
        """
        Function initializes mysqldump or mariadb-dump to create db dumps.

        """
        try:
            # Create SSH client
            ssh = self.SshClient(
                        self.host,
                        self.port,
                        self.username,
                        '',
                        self.priv_key
                    )

            fh = self.Filehash(
                    self.host, 
                    self.port,
                    self.username,
                    self.priv_key)

            # Calling dbdump_exec with subprocess module with
            # arguments given by user.
            opts: str = ''.join(self.dbdump_opts)
            dbdump: str = self.dbdump_exec + " " + opts

            # define name dump file
            dumpfile: str = f"{date}.sql"

            # Create full path of dump file
            fp = os.path.join(self.tmp, dumpfile)

            # Definition of full command to be executed
            cmd = f"{dbdump} > {fp}"
            logger.info(cmd)

            # Execute command
            subprocess.run(cmd, shell=True)

            # Compress dump file
            compressed_file = self.compress(mode="database", filename=fp)

            # Create file hash
            file_hash = fh.calculate_hash(fp)
            logger.info("Hash: %s, File: %s", file_hash, fp)

            # Transfer file
            ssh.put(fp, self.destination)

            remote_file = os.path.join(self.destination, compressed_file)
            remote_file_hash = fh.calculate_remote_hash(filename=remote_file)
        except subprocess.CalledProcessError as sp_err:
            logger.error("Error while trying to make DB backup: ", sp_err)
            logger.error("Exitting")
            exit(1)

    def verify_hash(self, filename: str = None,
                    filehash_src: hash = None,
                    filehash_dest: hash = None) -> bool:
        """
        Function for checking src and dest file hashes
        """
        if filehash_src != filehash_dest:
            return False
        return True

    def create_wp_backup(self) -> str:
        """
        Function for creating a Wordpress backup
        """

        try:
            logger.info("Starting to creating Wordpress backup")
            self.compress(source=self.src)

            # Generate filehash from tarfile and store in memory
            self.source_hash[wpbackup] = self.calculate_hash(wpbackup)
            logger.info("File hash: %s", self.source_hash)

            return wpbackup

        # If error throw exception and print error message
        except subprocess.CalledProcessError as proc_err:
            logging.error("Execution error: ", proc_err)
            exit(1)
        except IOError as io_err:
            logger.error("Error while making file backup: %s", io_err)
            exit(1)


def main():
    config_file = argv[1]
    logger.info("Reading config file: %s", config_file)

    conf = Config(config_file)

    if not os.path.exists(conf.tmp_dir):
        os.makedirs(conf.tmp_dir)

    backup = Bakctl(
                conf.host,
                conf.port,
                conf.username,
                conf.priv_key,
                conf.dbuser,
                conf.dbname,
                conf.tmp_dir,
                conf.src,
                conf.destination)

    if conf.database == 1:
        filename = backup.create_db_backup()
        if filename == "":
            logger.error("Creating DB backup went wrong")
            exit(1)

    if conf.wordpress == 1:
        filename = backup.create_wp_backup()
        if filename == "":
            logger.error("Creating WP backup went wrong")
            exit(1)

    if backup.verify_hash(
                    backup.source_hash,
                    remote_hash is True):
        logger.error("File hashes do not match")
    else:
        logger.error("Backup has succeeded")


if __name__ == '__main__':
    """bakctl is a program to make backups from Wordpress
    and MySQL databases"""

    # Initializing logger
    logging.basicConfig(
            filename=f'bakctl-{date}.log',
            level=logging.DEBUG,
            )


    if len(argv) < 1:
        print("Not enough arguments\n")
        exit(1)

    try:
        main()
    except KeyboardInterrupt as e:
        print('Exiting on user request: ', e)
        exit(1)
