# bakctl
bakctl is a interface for backuping MySQL database and Wordpress installation 

# Installation
Install the prerequisites
`sudo apt install python3-paramiko python3-scp mysql-client`

Clone the repository and change into it's directory
`git clone git@github.com:cdorsman/bakctl.git && cd bakctl`

Execute the following command to install bakctl into /usr/local/bin
`sudo install -m 755 bakctl.py /usr/local/bin`

# Usage

For backing up Wordpress use the following command
`
