#!/usr/bin/env python3
"""
Dit script is voor het maken van backups van:
- Wordpress installatie
- MySQL database dmv dbdump
"""

__version__ = '0.1'
__author__ = 'Chris Dorsmam'

import argparse
from sys import exit, argv
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

date: str = datetime.today().strftime('%Y%m%d%H%M%S')
files: dict = {}
dbdump_opts: list = []


def get_db_client():
    """
    Function is to find a database parserent

    Clients can be: mysqldump or mariadb-dump
    """
    try:
        return which("mysqldump") or which("mariadb-dump")
    # If database cannot be found throw exception and exit
    except ValueError as ve:
        logging.error("Cannot find MariaDB or MySQL parserent: %s", ve)
        exit(1)


class Parser:
    """ Class to parse arguments"""
    def __init__(self):
        self.host: str = ""
        self.port: int = 0
        self.username: str = ""
        self.password: str = ""
        self.dbhost: str = ""
        self.dbport: int = 0
        self.dbusername: str = ""
        self.dbpassword: str = ""
        self.database: str = ""
        self.tmp_dir: str = ""
        self.source: str = ""
        self.destination: str = ""
        self.exthost: str = ""
        self.extport: int = 0
        self.extusername: str = ""
        self.extpassword: str = ""

        for key, value in vars(self.create_parser()).items():
            if key == 'host':
                self.config_file = value
            if key == 'port':
                self.port = value
            if key == 'user':
                self.username = value
            if key == 'passwd':
                self.password = value
            if key == 'dbhost':
                self.config_file = value
            if key == 'dbport':
                self.port = value
            if key == 'dbuser':
                self.username = value
            if key == 'dbpasswd':
                self.password = value
            if key == 'db':
                self.database = value
            if key == 'tmp_dir':
                self.tmp_dir = value
            if key == 'source':
                self.source = value
            if key == 'dest':
                self.destination = value
            if key == 'exthost':
                self.exthost = value
            if key == 'extport':
                self.extport = value
            if key == 'extuser':
                self.extusername = value
            if key == 'extpasswd':
                self.extpassword = value

    def create_parser(self):
        """
        This ArgsParse function is where you can add
        all your needed options
        """
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')

        # Option definitions for subparser DB
        parser_db = subparsers.add_parser("db")
        parser_db.add_argument('--db',
                               help='MySQL/MariaDB database to backup',
                               default='wordpress')

        parser_db.add_argument('--dbuser',
                               help='Username to log in',
                               type=str)

        parser_db.add_argument('--dbport',
                               help='Port to conect to',
                               default=3306,
                               type=int)

        parser_db.add_argument('--dbhost',
                               help='Hostname of database server')

        parser_db.add_argument('--dbpasswd',
                               help='Ask for password for log into database',
                               action='store_true')

        parser_db.add_argument('--exthost',
                               help='Hostname of backup server')

        parser_db.add_argument('--extport',
                               type=int,
                               default=22,
                               help='port of backup server')

        parser_db.add_argument('--extuser',
                               help='user of backup server')

        parser_db.add_argument('--extpasswd',
                               help='Ask for password for log into database',
                               action='store_true')

        parser_db.add_argument('--src',
                               help='Source directory of \
                                       Wordpress installation')

        parser_db.add_argument('--dest',
                               help='Destination directory to place backup')

        parser_db.add_argument('--tmp',
                               help='Temporary directory to place db backup')

        # Option definitions for subparser WP
        parser_wp = subparsers.add_parser('wp')

        parser_wp.add_argument('--port',
                               help='Port to conect to',
                               default=22,
                               type=int)

        parser_wp.add_argument('--host',
                               help='Hostname to connect to')

        parser_wp.add_argument('--user',
                               help='Username to log in',
                               type=str)

        parser_wp.add_argument('--exthost',
                               help='Hostname of backup server')

        parser_wp.add_argument('--extport',
                               type=int,
                               default=22,
                               help='port of backup server')

        parser_wp.add_argument('--extuser',
                               help='user of backup server')

        parser_wp.add_argument('--src',
                               help='Source directory of \
                                       Wordpress installation')

        parser_wp.add_argument('--dest',
                               help='Destination directory to place backup')

        parser_wp.add_argument('--password',
                               help='Ask for password for log into database',
                               action='store_true')

        parser_wp.add_argument('--extpasswd',
                               help='Ask for password for log into database',
                               action='store_true')

        return parser.parse_args()


class Bakctl:
    def init(
            self,
            host: str = "",
            port: int = 0,
            username: str = "",
            password: str = "",
            database: str = "",
            tmp_dir: str = "",
            source: str = "",
            destination: str = "",
            exthost: str = "",
            extport: int = 0,
            extusername: str = "",
            extpassword: str = ""):
        self.host: str = host
        self.port: int = port
        self.username: str = username
        self.password: str = password
        self.source: str = source
        self.tmp_dir: str = tmp_dir
        self.destination: str = destination
        self.database: str = database
        self.exthost: str = exthost
        self.extport: int = extport
        self.extusername: str = extusername
        self.extpassword: str = extpassword
        self.dbdump_exec: str = get_db_client()

    def createSSHClient(self) -> object:
        parserent: object = paramiko.SSHClient()
        parserent.load_system_host_keys()
        parserent.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        parserent.connect(self.host, self.port, self.username, self.password)
        return parserent

    def create_db_backup(self):
        """
        Function initializes mysqldump or mariadb-dump to create db dumps.

        """
        try:
            # Calling mysql_dump with subprocess module with
            # arguments given by user.

            dbdump: str = join(self.dbdump_exec, dbdump_opts)
            cmd = f"{dbdump} > {self.tmp_dir}"

            subprocess.run(
                cmd,
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
        hash_object: object = hashlib.sha256()

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
        ...

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
                    results[filepath] = self.calculate_hash(filepath)

            copytree(src, dest)

            for root, _, files in os.walk(dest):
                for filename in filter(files, '*'):
                    filepath = os.path.join(root, filename)
                    results[filepath] = self.calculate_hash(filepath)
            return True

        # If error throw exception and print error message
        except IOError as io_err:
            print("Error while making file backup: ", io_err)
            exit(1)


def main():
    backup = Bakctl(
            parser.host,
            parser.port,
            parser.username,
            parser.password,
            parser.database,
            parser.tmp_dir,
            parser.source,
            parser.destination,
            parser.exthost,
            parser.extport,
            parser.extusername,
            parser.extpassword)

    if parser.command == 'db':
        backup.create_db_backup()

    else:
        backup.create_wp_backup(src, dest)


if __name__ == '__main__':
    """bakctl is a program to make backups from Wordpress
    and MySQL databases"""

    logging.basicConfig(
            filename=f'bakctl-{date}.log',
            level=logging.DEBUG,
            )

    parser = Parser()

    try:
        # Check arguments
        if parser.command == 'db':
            if parser.host:
                dbdump_opts += " -h {0}".format(parser.host)
            if parser.port:
                dbdump_opts += " -P {0}".format(parser.port)
            if parser.user:
                dbdump_opts += " -u {0}".format(parser.user)
            if parser.db:
                dbdump_opts += " -D {0}".format(parser.db)
            if parser.password:
                dbdump_opts += " -p"

            logger.debug('\
mysql_dump args: Host: %s, Port: %s, Username: %s, Database %s',
                         parser.host,
                         parser.port,
                         parser.user,
                         parser.db)

        if parser.command == 'wp':
            logger.debug('\
Copying: Source: %s to dest: %s:%d:%s',
                         parser.src,
                         parser.host,
                         parser.port,
                         parser.dest)
    except ValueError as parser_err:
        print("Argument error:", parser_err)
        exit(1)

    try:
        main()
    except KeyboardInterrupt as e:
        print('Exiting on user request: ', e)
        exit(exitcode)
