# bakctl.py
bakctl.py is a interface for backuping MySQL or MariaDB database and Wordpress installation 

## How does bakctl.py work
### WordPress
bakctl.py will copy and compress the installation folder in a temporary folder that is indicated in config.json

### Database
bakctl.py will look if there is a mysqldump or mariadb installed on the system. It will then create a database dump

### Checking
In both cases it will generate sha256 hashes before and after transfering the compressed file backup. These hashes will then be compared as a integrity check.

## Installation
Install the prerequisites
`sudo apt install python3-paramiko python3-scp mysql-client`

Clone the repository and change into it's directory  
`git clone git@github.com:cdorsman/bakctl.git && cd bakctl.py 

Execute the following oneliner to do the following
- Create /etc/bakctl.py folder
- Move config.json to /etc/bakctl
- Install bakctl.py into /usr/local/bin

`sudo -s <<< 'mkdir /etc/bakctl.py && mv config.json && install -m 755 bakctl.py /usr/local/bin'`


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
databaseBackup (integer): Enable backup for database Set to '1' to enable

wordpress
host [ string or IP-adres ] : IP or hostnaam of the externe back-upserver
port [ integer ]: SSH-poort om verbinding te maken met de externe back-upserver
username [ string ]: Gebruiker voor inloggen op de externe back-upserver
privateKey [ path ]: Location naar de ed25519-private key voor SSH-authenticatie.
source [ path ]: Locatie naar de WordPress-installatie
database
dbName [ string ]: Naam van de database
dbUser [ string ]: Gebruikersnaam voor inloggen op de database

