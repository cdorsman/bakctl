# bakctl
bakctl is a interface for backuping MySQL or MariaDB database and Wordpress installation 

## Installation
Install the prerequisites
`sudo apt install python3-paramiko python3-scp mysql-client`

Clone the repository and change into it's directory
`git clone git@github.com:cdorsman/bakctl.git && cd bakctl`

Execute the following command to install bakctl into /usr/local/bin
`sudo install -m 755 bakctl.py /usr/local/bin`

## Usage

There are two action modes: database and wordpress. To define a mode, you can use the
'db' for database or 'wp' for Wordpress

Within the modes it is possible to define the following:

db:
- dbhost: Database host. 
- dbport: database port. 
- db: Name of the database
- dbuser: Username to log into the database
- dbpasswd: Ask DB password
- exthost: external backup host
- extport: port of the external backup host
- extuser: User to connect with
- extpasswd: Ask password for extuser
- tmp: Temporary directory to place the dump before transfer. Default is /tmp
- dest: Destination directory

When invoked it will create a database dump into the temporary directory, where it will 
be compressed in GZIP-format. When finished, it will create a file hash and send the GZIP-file to
the given back-up server over SSH. As finalization, it will create another file hash, what will
be compared with the previous generated file hash for possible corruption. 


wp:
- host: Wordpress host. 
- port: SSH port 
- username: Username to log into the server
- extpasswd: Ask password for user
- exthost: external backup host
- extport: port of the external backup host
- extuser: User to connect with
- extpasswd: Ask for password for extuser
- src: Source directory of the Wordpress installation 
- dest: Destination directory

When invoked it will create a GZIP-file from the Wordpress installation. When finished, it will create a file hash 
and be sended the given back-up server over SSH. As finalization, it will create another file hash, what will
be compared with the previous generated file hash for possible corruption. 


## Examples

To backup a Wordpress installation on a local server to external backup server and ask for password:
`bakctl --action wordpress -H hostname or ip -P 22 -u user_name -p -s /var/www/wordpress -d /backup/dir`

To backup a database on a local server to external backup server and ask for password:
`bakctl.py db --db wordpress \
	--dbhost 127.0.0.1 \
	--dbport 3306 \
	--dbuser bubba \
	--db wordpress \
	--dbpasswd  \
	--exthost 192.168.50.81 \ 
	--extport 22 \
	--extuser bubba \ 
	--extpasswd`

