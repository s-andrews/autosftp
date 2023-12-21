# Web System Base
This is a starting point for new web resources on our site.

It provides a basic setup of a flask app with bootstrap templates and a mongo db backend.  It handles user logins linked initially to an LDAP server.

Using this code
===============

To use this as a starting point for a new system you need to clone this repository.  To do this create a new github repository with no content then do

```
git clone --bare https://github.com/s-andrews/websystembase.git
cd websystembase.git
git push --mirror https://github.com/s-andrews/newrepositoryname.git
cd ..
rm -rf websystembase.git
```

Changes to make
===============

A number of things have been set up with values that you'll need to change.

Database details
----------------

The system uses a mongo-db database.  The database name and login details must be changed

In ```database/create_database_and_user.txt``` you need to change the name of the database in both the use statement and the createuser.  You also need to change the username and password

You need to create a ```configuration/conf.json``` file from the ```example_conf.json``` template where you input the address, username and password, which must match the ones above.

In the ```database/setup_database.py``` script you'll need to change the name of the database and the collections you want to use.

Cookie Name
-----------

You'll need to select a name for your session cookie.  This will be set in the ```www/static/js/main.js``` file in all of the ```Cookies.set Cookies.get Cookies.remove``` statements


Application Name
----------------

You should rename the main python script which is the flask entrypoint.  This is the ```.py``` file in the root of the ```www``` folder


Setting up the system
=====================

Once you've made the changes above you can follow the steps below to create a working base system from which you can develop.

Create a venv
-------------

From the root of the repository

On windows
```
python -m venv venv
venv\Scripts\activate.bat
pip install flask pymongo json 
```

You'll also need to download and install a binary python-ldap whl from https://www.lfd.uci.edu/~gohlke/pythonlibs/

On linux

```
python -m venv venv
. venv/Scripts/activate
pip install flask pymongo json python-ldap 
```

Create the database
-------------------

You'll need to have mongodb installed and know how to get to a root shell.

Copy the text from ```database/create_database_and_user.txt``` into the shell to create your basic setup.  Beware that mongosh on windows has a bug where some lines of copied text get lost during pasting so you might need to copy/paste one line at a time, which is annoying.

Once that's done run ```database/setup_database.py``` to check the connection and set up the collections you are going to use.


Start the app
-------------

From the shell in which you started the venv

Move to the ```www``` folder

```
flask --debug --app groupactivity.py run
```

This should start the server and you should have a basic system running on 127.0.0.1:5000

You should change the name in this to whatever you changed your app name to.

