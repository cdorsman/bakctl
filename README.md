# bakctl.py
bakctl.py is a interface for backuping MySQL or MariaDB database and Wordpress installation 

## How does bakctl.py work
### WordPress
bakctl.py will copy and compress the installation folder in a temporary folder that is indicated in config.json

### Database
bakctl.py will look if there is a mysqldump or mariadb installed on the system. It will then create a database dump

### Integrity checking
In both cases it will generate sha256 hashes before and after transfering the compressed file backup. These hashes will then be compared as a integrity check.

## Installation
Install the prerequisites
`sudo apt install python3-paramiko python3-scp mysql-client`

Clone the repository and change into it's directory  
`git clone git@github.com:cdorsman/bakctl.git && cd bakctl.py` 

Execute the following oneliner to do the following
- Create /etc/bakctl.py folder
- Move config.json to /etc/bakctl
- Install bakctl.py into /usr/local/bin

`sudo -s <<< 'mkdir /etc/bakctl.py && mv config.json && install -m 755 bakctl.py /usr/local/bin' `

On the database side there following steps needs to be done:

For bakctl.py to be able to create a database backups, it is necessary that the dump command, mariadb-dump or mysqldump, is configured. 
In case of mariadb:
Open /etc/mariadb/mariadb in a text editor
add into the mariadb-dump section in /etc/mysql/mariadb.conf.d/50-mariadb-clients.cnf the following:
user="database_user"
password="database_password"

Save the file



## Usage
You can execute bakctl.py in two ways:  
- Execute bakctl.py without arguments.
  It will look for /etc/bakctl.py config.json
- Execute bakctl.py with a JSON-configuration file like so
`bakctl.py ./custom-config.json`

## bakctl.py configuration
You can configure bakctl.py by editting /etc/bakctl/config.json

Configuration file consists of three sections:
- general
- wordpress
- database 

Each section has their own configuration items

### Configuration items per sections
general  
tmp [ path ]: location of temporary folder  
destination [ path ]: destination folder on the external server  
wordpressBackup [ integer ]: Enable back-up for WordPress. Set to '1' to enable.  
databaseBackup [ integer ]: Enable backup for database Set to '1' to enable  
  
wordpress  
host [ string or IP-adres ] : IP or hostnaam of the external back-upserver  
port [ integer ]: SSH-port to connect with external back-upserver  
username [ string ]: User to login   
privateKey [ path ]: Location of the ed25519-private key for SSH-authentication.  
source [ path ]: Location to the WordPress-installation  
  
database  
dbName [ string ]: Name of database  
dbUser [ string ]: Username to login on the database  

## Configration example
```
{
  "general": [
    {
  	"tmpDir": "/tmp/baktmp",
  	"destination": "/tmp/result",
  	"wordpressBackup": 1,
  	"databaseBackup": 1
    }
  ],
  "wordpress": [
    {
      "host": "127.0.0.1",
      "port": 22,
      "username": "user",
      "privateKey": "/home/user/.ssh/id_ed25519",
      "source": "/var/www/wordpress"
    }
  ],
  "database":
  [
    {
      "dbUser": "db-user",
      "dbName": "wordpress"
    }
  ]
}
```


