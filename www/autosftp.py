#!/usr/bin/env python3

from flask import Flask, request, render_template, make_response, send_file
import random
from urllib.parse import quote_plus, unquote
from pymongo import MongoClient
from bson.json_util import dumps
from bson import ObjectId
from pathlib import Path
import json
import ldap
import time
import random
import datetime
import subprocess
import os
import pwd
import ipaddress
import base64


app = Flask(__name__)

def validate_location():
    # We only want to allow requests from internal addresses for
    # some of our functions.
    #
    # We need the remote address of the user.  If we're behind a 
    # proxy then this will be in the request.headers["X-Forwarded-For"]
    # field.  If not then it will be in the request.remote_addr

    ip = request.remote_addr

    if "X-Forwarded-For" in request.headers:
        ip = request.headers["X-Forwarded-For"]

    ip = ipaddress.ip_address(ip)

    # We're OK if we're just testing locally
    if str(ip) == "127.0.0.1":
        return

    # Now we need to match the ip against our allowed range.
    if ip in ipaddress.ip_network("149.155.144.0/255.255.248.0") or ip in ipaddress.ip_network("149.155.134.0/255.255.255.0"):
        return
    
    raise Exception("Page only accessible internally")

@app.route("/")
def index():
    validate_location()
    return render_template("index.html")

@app.route("/login", methods = ['POST', 'GET'])
def process_login():
    validate_location()
    """
    Validates an username / password combination and generates
    a session id to authenticate them in future

    @username:  Their BI username
    @password:  The unhashed version of their password

    @returns:   Forwards the session code to the json response
    """
    form = get_form()
    username = form["username"]
    password = form["password"]

    # We might not try the authentication for a couple of reasons
    # 
    # 1. We might have blocked this IP for too many failed logins
    # 2. We might have locked this account for too many failed logins

    # Calculate when any timeout ban would have to have started so that
    # it's expired now
    timeout_time = int(time.time())-(60*(int(server_conf["security"]["lockout_time_mins"])))


    # We'll check the IP first
    ip = ips.find_one({"ip":request.remote_addr})
    
    if ip and len(ip["failed_logins"])>=server_conf["security"]["failed_logins_per_ip"]:
        # Find if they've served the timeout
        last_time = ip["failed_logins"][-1]

        if last_time < timeout_time:
            # They've served their time so remove the records of failures
            ips.update_one({"ip":request.remote_addr},{"$set":{"failed_logins":[]}})

        else:
            raise Exception("IP block timeout")

    # See if we have a record of failed logins for this user
    person = people.find_one({"username":username})

    if person and person["locked_at"]:
        if person["locked_at"] > timeout_time:
            # Their account is locked
            raise Exception("User account locked")
        else:
            # They've served their time, so remove the lock
            # and failed logins
            people.update_one({"username":username},{"$set":{"locked_at":0}})
            people.update_one({"username":username},{"$set":{"failed_logins":[]}})


    # Check the password against AD
    conn = ldap.initialize("ldap://"+server_conf["server"]["ldap"])
    conn.set_option(ldap.OPT_REFERRALS, 0)
    try:
    
        conn.simple_bind_s(username+"@"+server_conf["server"]["ldap"], password)

        # Clear any IP recorded login fails
        ips.delete_one({"ip":request.remote_addr})

        sessioncode = generate_id(20)


        if not person:
            # We're making a new person.  We can therefore query AD
            # to get their proper name and email.

            # We can theoretically look anyone up, but this filter says
            # that we're only interested in the person who logged in
            filter = f"(&(sAMAccountName={username}))"

            # The values we want to retrive are their real name (not 
            # split by first and last) and their email
            search_attribute = ["distinguishedName","mail"]

            # This does the search and gives us back a search ID (number)
            # which we can then use to fetch the result data structure
            dc_string = ",".join(["DC="+x for x in server_conf["server"]["ldap"].split(".")])
            res = conn.search(dc_string,ldap.SCOPE_SUBTREE, filter, search_attribute)
            answer = conn.result(res,0)

            # We can then pull the relevant fields from the results
            name = answer[1][0][1]["distinguishedName"][0].decode("utf8").split(",")[0].replace("CN=","")
            email = answer[1][0][1]["mail"][0].decode("utf8")

            # Now we can make the database entry for them
            new_person = {
                "username": username,
                "name": name,
                "email": email,
                "disabled": False,
                "sessioncode": "",
                "locked_at": 0,
                "failed_logins": [],
            }
        
            people.insert_one(new_person)

        # We can assign the new sessioncode to them and then return it
        people.update_one({"username":username},{"$set":{"sessioncode": sessioncode}})

        return(sessioncode)
    
    except ldap.INVALID_CREDENTIALS:
        # We need to record this failure.  If there is a user with this name we record
        # against that.  If not then we just record against the IP
        if person:
            people.update_one({"username":username},{"$push":{"failed_logins":int(time.time())}})
            if len(person["failed_logins"])+1 >= server_conf["security"]["failed_logins_per_user"]:
                # We need to lock their account
                people.update_one({"username":username},{"$set":{"locked_at":int(time.time())}})
                


        if not ip:
            ips.insert_one({"ip":request.remote_addr,"failed_logins":[]})

        ips.update_one({"ip":request.remote_addr},{"$push":{"failed_logins":int(time.time())}})

        raise Exception("Incorrect Username/Password from LDAP")

@app.route("/validate_session", methods = ['POST', 'GET'])
def validate_session():
    form = get_form()
    person = checksession(form["session"])
    return(str(person["name"]))


@app.route("/sites/<username>/", methods = ['POST', 'GET'])
def site_root(username):
    return site(username,"/")


@app.route("/sites/<username>/<path:path>", methods = ['POST', 'GET'])
def site(username,path):
    return render_template("site.html")

@app.route("/download/<username>/<path:path>", methods = ['POST', 'GET'])
def download(username,path):

    validated,_ = validate_site(username)

    if not validated:
        # They shouldn't be here
        raise Exception("Not authenticated")

    file = Path(server_conf["server"]["home"]+"/"+username+server_conf["server"]["home"]+"/"+username+"/"+path)
    
    return send_file(file)


@app.route("/create_site", methods = ['POST', 'GET'])
def create_site():
    validate_location()
    form = get_form()
    person = checksession(form["session"])

    name = form["name"]
    days = form["days"]
    anonymous = form["anonymous"]
    siteid = form["siteid"]


    # We need the date to expire.  We add one to the number of
    # days to account that we're part way through a day already
    # so we err on the side of caution
    expires = datetime.datetime.today() + datetime.timedelta(days=int(days)+1)

    # If siteid is empty then this is a new site
    if not siteid:
        username,password = create_username_password()

        # Now make the actual account
        create_user_account(username, password)

        sites.insert_one({
            "user_id":person["_id"],
            "name": name,
            "username": username,
            "password": password,
            "expires": expires,
            "anonymous_https": anonymous
        })

    # If it's not empty then we're updating an existing
    # site. Let's check we can find it and that it's owned
    # by this person
    else:
        existingsite = sites.find_one({"user_id":person["_id"], "_id":ObjectId(siteid)})

        if not existingsite:
            raise Exception("Couldn't find existing site to edit")

        sites.update_one({"_id":ObjectId(siteid)},{"$set":{"name":name, "expires": expires, "anonymous_https": anonymous}})

    return jsonify([True])


def create_user_account(username,password):
    # First we need to make the user account.  The folder structure is a bit weird so
    # that we can accommodate the needs of the sftp chroot.
    # 
    # We set the home dir to be /home/user
    # we make /home/user owned by root, with read only for the user
    # we make /home/user/home owned by root with read only for the user
    # we make /home/user/home/[username] owned by the user
    subprocess.run(["/usr/sbin/useradd","-b",server_conf["server"]["home"],"-M","-g","sftp",username], check=True)

    homedir = Path(server_conf["server"]["home"]) / username

    homedir.mkdir(mode=0o755)

    chroothome = homedir.joinpath(server_conf["server"]["home"][1:])
    chroothome.mkdir(parents=True,mode=0o755)

    chrootuser = chroothome / username
    chrootuser.mkdir(mode=0o755)
    os.chown(chrootuser,pwd.getpwnam(username).pw_uid,pwd.getpwnam(username).pw_gid)

    # Then we need to set the password
    with subprocess.Popen(["/usr/bin/passwd",username,"--stdin"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL) as passwd_proc:
        passwd_proc.stdin.write(password.encode("utf8"))    

    # That should be it


def create_username_password ():
    adjectives = []

    with open(Path(__file__).resolve().parent.parent / "database/adjectives.txt") as infh:
        for adjective in infh:
            adjectives.append(adjective.strip())

    animals = []

    with open(Path(__file__).resolve().parent.parent / "database/animals.txt") as infh:
        for animal in infh:
            animals.append(animal.strip())


    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!%*?#@:_"

    username = random.choice(adjectives)+"-"+random.choice(animals)+"-"+str(random.randint(1000,9999))

    password = ""
    for _ in range(20):
        password += random.choice(letters)

    return (username,password)


@app.route("/delete_site", methods = ['POST', 'GET'])
def delete_site():
    validate_location()
    form = get_form()
    person = checksession(form["session"])
    site_id = form["id"]

    site = sites.find_one({"user_id":person["_id"], "_id":ObjectId(site_id)})

    if not site:
        raise Exception("Couldn't find site")
    
    sites.delete_one({"user_id":person["_id"], "_id":ObjectId(site_id)})

    # We also want to remove the users account.  We need to kill any 
    # processes owned by this user in case they're logged in at the 
    # moment, then we can remove the account.

    # The killall often exits in a nonzero state but it does work so we
    # just don't check.  It will log out any running sftp sessions for this
    # user.
    subprocess.run(["/usr/bin/killall","-9","-u",site["username"]], check=False)

    # Then we actually delete the account.
    subprocess.run(["/usr/sbin/userdel",site["username"]], check=True)
    

    return jsonify([True])


@app.route("/filezilla/<sitename>", methods = ['GET'])
def filezilla(sitename):
    validate_location()
    form = get_form()
    person = checksession(form["session"])

    # Check that this person owns this site

    site = sites.find_one({"username":sitename})

    if not site["user_id"] == person["_id"]:
        raise Exception("This person doesn't own this site")

    # We need to make up an XML template with the appropriate
    # parts filled in.

    site = {
        "host": server_conf["address"],
        "username": site["username"],
        "name": site["name"],
        "encoded_password": base64.b64encode(site["password"].encode("utf8"))
    }

    return render_template("filezilla.xml", site=site)



@app.route("/site_list", methods = ['POST', 'GET'])
def site_list():
    validate_location()
    form = get_form()
    person = checksession(form["session"])

    site_list = sites.find({"user_id":person["_id"]})

    sites_to_return = []

    for site in site_list:
        new_site = {}

        for key in site.keys():
            if key == "expires":
                # Calculate the number of days until the expiry date
                new_site["days"] = (site["expires"] - datetime.datetime.today()).days

            elif key == "user_id":
                continue

            else:
                new_site[key] = site[key]

        # Don't show sites which have expired but haven't yet been deleted.
        if new_site["days"] >= 1:
            sites_to_return.append(new_site)
        

    return jsonify(sites_to_return)

def validate_site(sitename):
    # We can validate the site in one of three ways.
    # 1. With a session cookie from a main login
    # 2. With a password cookie from the site
    # 3. With a password in the form

    site = sites.find_one({"username":sitename})

    # It's possible this site doesn't need validation
    # so that's an easy way out.
        # Check if they need a password 
    if site["anonymous_https"]=="true":
        return (True,False)

    # Let's try the session cookie first
    if "autosftp_session_id" in request.cookies:
        person = checksession(request.cookies.get("autosftp_session_id"))
        if person and site["user_id"] == person["_id"]:
            return (True,False)

    # Nope, let's try the site cookie
    if "autosftp_"+sitename in request.cookies:
        if site["password"] == request.cookies.get("autosftp_"+sitename):
            return (True,False)

    # Finally let's see if they send a password in a form
    form = get_form()

    if "password" in form:
        if form["password"] == site["password"]:
            return (True,True)


    return (False,False)


@app.route("/get_content", methods = ['POST', 'GET'])
def get_content():
    form = get_form()

    username = form["username"]
    path = form["path"]

    # The path will be URL encoded so we need to fix that
    path = unquote(path)

    # Quick sanity check
    if ".." in path:
        raise Exception("Invalid Path")

    site = sites.find_one({"username":username})

    if not site:
        raise Exception("Couldn't find site")

    validated,needs_cookie = validate_site(username)

    if not validated:
        return jsonify("password")

    # We're all good and authenticated (if needed) so send the content
    # Get actual site data
    folder = Path(server_conf["server"]["home"]+"/"+username+server_conf["server"]["home"]+"/"+username+"/"+path)    

    # We need a sanity check here.  This path must be a subdirectory of the users home dir.  If it
    # isn't then they've done something bad so we need to stop that.

    if not folder.exists() and folder.is_dir():
        raise Exception("Invalid Path")

    # We'll keep the files and folders separate so we can sort them later.
    files = []
    folders = []

    for file in folder.iterdir():
        if file.is_dir():
            folders.append({"name":file.name,"type":"folder"})
        else:
            files.append({"name":file.name,"type":"file","size": format_file_size(file.stat().st_size)})
        

    # We need to sort the content. We sort alphabetically, case insensitive
    files.sort(key=lambda x: x["name"].lower())
    folders.sort(key=lambda x: x["name"].lower())

    folders.extend(files)

    response = jsonify(folders)

    if needs_cookie:
        response.set_cookie("autosftp_"+username,form["password"])

    return response


def format_file_size (bytenum):
    unit = "bytes"
    number = bytenum

    if number > 1024:
        number /= 1024
        unit = "kb"

    if number > 1024:
        number /= 1024
        unit = "Mb"

    if number > 1024:
        number /= 1024
        unit = "Gb"

    if number > 1024:
        number /= 1024
        unit = "Tb"


    if number != int(number):
        number = round(number,1)
        if float(number) == int(number):
            number = int(number)

    return f"{number} {unit}"



def get_form():
    if request.method == "GET":
        return request.args

    elif request.method == "POST":
        return request.form


def generate_id(size):
    """
    Generic function used for creating IDs.  Makes random IDs
    just using uppercase letters

    @size:    The length of ID to generate

    @returns: A random ID of the requested size
    """
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    code = ""

    for _ in range(size):
        code += random.choice(letters)

    return code


def checksession (sessioncode):
    """
    Validates a session code and retrieves a person document

    @sessioncode : The session code from the browser cookie

    @returns:      The document for the person associated with this session
    """

    person = people.find_one({"sessioncode":sessioncode})

    if "disabled" in person and person["disabled"]:
        raise Exception("Account disabled")

    if person:
        return person

    raise Exception("Couldn't validate session")



def jsonify(data):
    # This is a function which deals with the bson structures
    # specifically ObjectID which can't auto convert to json 
    # and will make a flask response object from it.
    response = make_response(dumps(data))
    response.content_type = 'application/json'

    return response

def get_server_configuration():
    with open(Path(__file__).resolve().parent.parent / "configuration/conf.json") as infh:
        conf = json.loads(infh.read())
    return conf


def connect_to_database(conf):

    client = MongoClient(
        conf['server']['address'],
        username = conf['server']['username'],
        password = conf['server']['password'],
        authSource = "autosftp_database"
    )


    db = client.autosftp_database

    global people
    people = db.people_collection

    global ips
    ips = db.ips_collection

    global sites
    sites = db.sites_collection


# Read the main configuration
server_conf = get_server_configuration()

# Connect to the database
connect_to_database(server_conf)


