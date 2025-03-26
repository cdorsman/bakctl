# bakctl
bakctl is a interface for backuping MySQL or MariaDB database and Wordpress installation 

# Installation
Install the prerequisites
`sudo apt install python3-paramiko python3-scp mysql-client`

Clone the repository and change into it's directory
`git clone git@github.com:cdorsman/bakctl.git && cd bakctl`

Execute the following command to install bakctl into /usr/local/bin
`sudo install -m 755 bakctl.py /usr/local/bin`

# Usage

There are two action modes: database and wordpress. To define a mode, you can use the
--action option.

Within the modes it is possible to define the following:

database:
- host: Database host. 
- port: database port. 
- db: Name of the database
- username: Username to log into the database
- tmp: Temporary directory to place the dump before transfer. Default is /tmp
- dest: Destination directory

wordpress:
- host: Wordpress host. 
- port: SSH port 
- username: Username to log into the server
- src: Source directory of the Wordpress installation 
- dest: Destination directory


# Examples

To backup a Wordpress installation on a local server to external backup server and ask for password:
`bakctl --action wordpress -H hostname or ip -P 22 -u user_name -p -s /var/www/wordpress -d /backup/dir`

To backup a database on a local server to external backup server and ask for password:
`bakctl --action database -H hostname or ip -P 3306  -u user_name -p -s /var/www/wordpress -d /backup/dir`

For security reasons it is not possible to 
