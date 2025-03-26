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

mysql_dump_exec = which("mysql")
logger = logging.getLogger(__name__)
src = ""
dest = ""
date = datetime.today().strftime('%Y%m%d%H%M%S')
files = {}


def create_db_backup():
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


def calculate_hash(filename: str = None):
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


def verify_hash(filename: str = None,
        filehash_src: hash = None,
        filehash_dest: hash = None):
    """
    Function for checking the hash of copied file.
    """
    ...


def create_wp_backup(src: str = None, dest: str = None):
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
        

        return results

    # If error throw exception and print error message
    except IOError as io_err:
        print("Error while making file backup: ", io_err)
        exit(1)


def main():
    if cli.action == 'database':
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
                        help="Username to log into the database",
                        type=str
                        )

    parser.add_argument("-P", "--port",
                        help="MySQL/MariaDB port",
                        type=int,
                        default=33006
                        )

    parser.add_argument("-H", "--host",
                        help="MySQL/MariaDB host",
                        default='127.0.0.1'
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
        if cli.src:
            src = cli.src
        if cli.dest:
            dest = cli.dest
        logger.debug(f"Copying: Source: {cli.src} Dest: {cli.dest}")

    main()
