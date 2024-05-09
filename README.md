<img src="../main/www/static/images/autosftp_logo_path.svg?raw=true" width="100%">

This is the code for the automatic generation and management of sFTP sites.  It is hosted on the Babraham ftp1 server.

Running the app
===============

Once the app is installed you can start it by doing:

```
cd /srv/autosftp
source venv/bin/activate
cd www
nohup waitress-serve --host 127.0.0.1 --port 5000 --trusted-proxy 127.0.0.1 --trusted-proxy-headers "x-forwarded-for"  autosftp:app > /dev/null &
```


Installation
============

This system is designed to be installed on an AlmaLinux 9 system.

Install the base system, including the apache sever and mongodb

### Clone the repository
```
cd /srv/
git clone http://github.com/s-andrews/autosftp.git
```

### Build a venv
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
pip3 install python-ldap
```
You might need to install some more OS packages to get the package installs to complete successfully.

### Create the database
Decide on a password.

Edit the ```database/create_database_and_user.txt``` file to insert the password you picked then copy and paste that text into a ```mongosh``` shell to create the user and database.

### Create a config file
Copy the ```configuration/example_conf.json``` file to ```configuration/conf.json``` and edit this with the actual values you want to use.  You'll need to add the same password you used above and will need to
set the domain for the LDAP authentication.

### Initialise the database
Run the ```database/setup_database.py``` file in your activated venv.  This should connect to the database and create the collections you'll need.

### Configure SSHD
```
cd /etc/ssh/sshd_config.d
cp /srv/autosftp/configuration/02_autosftp_sshd.conf .
rm 50-redhat.conf
systemctl restart sshd
```

### Configure apache
```
systemctl enable httpd
cd /etc/httpd/conf.d/
cp /srv/autosftp/configuration/apache_autosftp.conf .
rm welcome.conf
systemctl restart httpd
```

### Create the sftp group
```
groupadd sftp
```

### Disable selinux
```
grubby --update-kernel ALL --args selinux=0
```



