#!/usr/bin/env python3
"""
This programm is for backupping:
- Wordpress installations
- MySQL and MySQL databases dmv dbdump
"""

__version__ = '0.1'
__author__ = 'Chris Dorsmam'

from datetime import datetime
from sys import exit, argv
import os
from os.path import basename
import tarfile
import subprocess
from shutil import which

from lib.logging import logger
from lib.config import Config
from lib.transfer import Client
from lib.filehash import Filehash

date: str = datetime.today().strftime('%Y%m%d%H%M%S')
files: dict = {}


def run_dbdump(
            username: str = "",
            db_name: str = "",
            tmp: str = "") -> str:
    """
    Function for executing mysqldump or mariadb-dump
    for creating db dump
    """

    try:
        # Get db dump command
        dbdump_exec = which("mysqldump") or which("mariadb-dump")

        # Calling dbdump_exec with subprocess module with
        # arguments given by user.
        dbdump_opts = ""
        dbdump_opts += " -u {0}".format(username)
        dbdump_opts += " {0}".format(db_name)
        #dbdump_opts += " -p"

        opts: str = ''.join(dbdump_opts)
        dbdump: str = dbdump_exec + " " + opts

        # define name dump file
        dumpfile: str = f"{date}.sql"

        # Create full path of dump file
        fp = os.path.join(tmp, dumpfile)

        # Definition of full command to be executed
        cmd = f"{dbdump} > {fp}"
        logger.info(cmd)

        # Execute command
        output = subprocess.run(cmd, shell=True)
        if output.returncode > 0:
            logger.error("Creating dump failed")
            exit(1)

        return dumpfile
    except ValueError as ve:
        logger.error("Cannot find MariaDB or MySQL client: %s", ve)
        exit(1)
    except subprocess.CalledProcessError as proc_err:
        logging.error("Execution error: ", proc_err)
        exit(1)


def compress(
        filename: str = "",
        out_file: str = "",
        source: str = None,
        tmp_dir: str = "") -> str:
    """
    Function for file compression
    """

    # WordPress
    if source is not None:
        # Definition of outfile
        out_file = os.path.join(tmp_dir, out_file)

        # Create tarfile with defined name
        with tarfile.open(out_file, "w:gz") as tar:
            # Loop through all files and dirs in self.source
            # and add them to the tarfile
            for path, subdirs, files in os.walk(source):
                logger.info("Compressing file: %s", path)
                tar.add(path)
    # Database
    else:
        # Definitions of filename and outfile
        filename = os.path.join(tmp_dir, filename)
        out_file = os.path.join(tmp_dir, out_file)

        # Compress dump file into tar.gz archive
        with tarfile.open(out_file, "w:gz") as tar:
            logger.info("Compressing file: %s", filename)
            tar.add(filename)
    return out_file


def main():
    backup_files = []
    hashes = {}

    # Create tmp dir if not exists
    if not os.path.exists(config.tmp_dir):
        os.makedirs(config.tmp_dir)

    # If database needs to be backupped
    if config.database == 1:
        # Create dump file
        filename = run_dbdump(
                    config.dbuser,
                    config.dbname,
                    config.tmp_dir)

        # define output file
        out_file = f'dbbackup-{date}.tar.gz'

        # Archive dump file
        archive = compress(
                        filename=filename,
                        out_file=out_file,
                        tmp_dir=config.tmp_dir)

        # Store archive name into list
        backup_files.append(archive)

    # If WordPress needs to be backupped
    if config.wordpress == 1:
        # define output file
        out_file = f'wpbackup-{date}.tar.gz'

        # Archive WordPress installation
        archive = compress(
                        out_file=out_file,
                        source=config.src,
                        tmp_dir=config.tmp_dir)

        # Store archive name into list
        backup_files.append(archive)

    filehash = Filehash()

    # Create filehash for each backup file
    for backup_file in backup_files:
        hash_original_file = filehash.calculate_hash(backup_file)
        hashes.update(
                {f'{backup_file}': {'original': f'{hash_original_file}'}})
    # Create SSH-client connection
    client = Client(
                host=config.host,
                port=int(config.port),
                username=config.username,
                password=None,
                key=config.priv_key)

    # Create destination folder
    client.execute("mkdir {0}".format(config.destination))

    # Transfer backup files through SFTP
    for backup_file in backup_files:
        destination = os.path.join(
                            config.destination,
                            basename(backup_file))
        logger.info("Transferring backup file: %s to %s",
                    backup_file, destination)
        client.put(backup_file, destination)
        os.remove(backup_file)

        # Get hash from remote location
        remote_hash = filehash.calculate_remote_hash(
                                            config.host,
                                            int(config.port),
                                            config.username,
                                            config.priv_key,
                                            destination)

    # Update hashes dictionary with hash from backup
    for backup_file in backup_files:
        for key in hashes:
            if backup_file in hashes:
                hashes[backup_file].update({'copy': f'{remote_hash}'})

    logger.info("Hash original: %s\nHash backup: %s",
                hashes[backup_file]['original'],
                hashes[backup_file]['copy'])

    # Compare hashes
    mistakes = 0
    for backup_file in backup_files:
        hash_original = hashes[backup_file]['original']
        hash_backup = hashes[backup_file]['copy']

        if filehash.verify_hash(hash_original, hash_backup) is False:
            logger.error("Backup has failed for file: %s", backup_file)
            mistakes = mistakes + 1

    logger.info("Backup has completed with %s mistakes", mistakes)


if __name__ == '__main__':
    """bakctl is a program to make backups from Wordpress
    and MySQL databases"""

    # Check if there are enough arguments
    if len(argv) < 2:
        config_file = '/etc/bakctl/config.json'
    else:
        config_file = argv[1]

    # Trying to read JSON config file
    logger.info("Reading config file: %s", config_file)
    config = Config(config_file)

    try:
        main()
    except KeyboardInterrupt as e:
        print('Exiting on user request: ', e)
        exit(1)
