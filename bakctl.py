#!/usr/bin/env python3
"""
Dit script is voor het maken van backups van:
- Wordpress installatie
- MySQL database dmv mysqldump
"""

__version__ = '0.1'
__author__ = 'Chris Dorsmam'

import argparse
from sys import exit
from datetime import datetime
import os
import fnmatch
from fnmatch import filter
import gzip
import subprocess
import hashlib
import logging
from shutil import copytree, which
import paramiko
from scp import SCPClient

logger = logging.getLogger(__name__)

date = datetime.today().strftime('%Y%m%d%H%M%S')
files = {}

class Bakctl:
    def init(
            self, 
            host: str = "", 
            port: int = 0, 
            username: str = "", 
            password: str = "",
            source: str = "",
            destionation: str = ""
        ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.source = source
        self.destination = destination
        self.mysqldump = which("mysqldump")

    def createSSHClient(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.host, self.port, self.username, self.password)
        return client

    def create_db_backup(self):
        """
        Function initializes mysqldump to create db dumps.

        """
        try:
            # Calling mysql_dump with subprocess module with
            # arguments given by user.
            subprocess.run(
                mysql_dump_exec,
                shell=True,
                capture_output=True
                )
        except subprocess.CalledProcessError as sp_err:
            logger.error("Error while trying to make DB backup: ", sp_err)
            logger.error("Exitting")
            exit(1)


    def calculate_hash(self, filename: str = None) -> hash:
        """
        Function calculating the filehash. With the filehash it is
        possible to check and verify the integrity of a file.
        """

        # Create hash object
        hash_object = hashlib.sha256()

        # Open the file in binary mode
        with open(filename, 'rb') as file:
            # Read the entire file content
            file_content = file.read()

            # Update the hash object with the file content
            hash_object.update(file_content)

        # Return the hexadecimal representation of the hash
        return hash_object.hexdigest()


    def verify_hash(self, filename: str = None,
        filehash_src: hash = None,
        filehash_dest: hash = None) -> bool:
        """
        Function for checking the hash of copied file.
        """
        return True


    def create_wp_backup(self, src: str = None, dest: str = None) -> bool:
        """
        Function for creating a Wordpress backup
        """

        try:
            logger.info("Starting to creating Wordpress backup")
            results_src = {}
            results_dest = {}

            for root, _, files in os.walk(src):
                for filename in filter(files, '*'):
                    filepath = os.path.join(root, filename)
                    results[filepath] = calculate_hash(filepath)
                    
            shutil.copytree(src, dest)

            for root, _, files in os.walk(dest):
                for filename in filter(files, '*'):
                    filepath = os.path.join(root, filename)
                    results[filepath] = calculate_hash(filepath)
            

            return True

        # If error throw exception and print error message
        except IOError as io_err:
            print("Error while making file backup: ", io_err)
            exit(1)


def main():
    if cli.action == 'database':
        backup = Bakctl()
        create_db_backup()

    else:
        create_wp_backup(src, dest)


if __name__ == '__main__':
    """bakctl is a program to make backups from Wordpress
    and MySQL databases"""

    logging.basicConfig(
            filename=f'bakctl-{date}.log',
            level=logging.DEBUG,
            )

    parser = argparse.ArgumentParser()
    parser.add_argument("--action",
                        choices=["database", "wordpress"],
                        help="Backup MySQL database or Wordpress"
                        )

    parser.add_argument("-D", "--db",
                        help="MySQL/MariaDB database to backup",
                        default='wordpress'
                        )

    parser.add_argument("-u", "--username",
                        help="Username to log in",
                        type=str
                        )

    parser.add_argument("-P", "--port",
                        help="Port to conect to",
                        type=int,
                        )

    parser.add_argument("-H", "--host",
                        help="Hostname to connect to",
                        )

    parser.add_argument("-s", "--src",
                        help="Source directory of Wordpress installation"
                        )

    parser.add_argument("wordpress",
                        help="Backup Wordpress",
                        action="store_true"
                        )

    parser.add_argument("-d", "--dest",
                        help="Destination directory to place backup"
                        )

    parser.add_argument("-p", "--password",
                        help="Ask for password for log into database",
                        action="store_true"
                        )

    cli = parser.parse_args()

    # Check arguments
    if cli.action == 'database':
        if cli.host:
            mysql_dump_exec += " -h {0}".format(cli.host)
        if cli.port:
            mysql_dump_exec += " -P {0}".format(cli.port)
        if cli.username:
            mysql_dump_exec += " -u {0}".format(cli.username)
        if cli.db:
            mysql_dump_exec += " -D {0}".format(cli.db)
        if cli.password:
            mysql_dump_exec += " -p"
        logger.debug('\
mysql_dump args: Host: %s, Port: %s, Username: %s, Database %s',
                     cli.host,
                     cli.port,
                     cli.username,
                     cli.db)

    if cli.action == 'wordpress':
        logger.debug('\
                Copying: Source: %s Dest: %s:%d:%s',
                    cli.src,
                    cli.host,
                    cli.port,
                    cli.dest)

    #main()
