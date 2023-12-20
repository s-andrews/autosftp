#!/usr/bin/env python3

from flask import Flask, request, render_template, make_response
import random
from urllib.parse import quote_plus
from pymongo import MongoClient
from bson.json_util import dumps
from pathlib import Path
import json
import ldap

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods = ['POST', 'GET'])
def process_login():
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

    # Check the password against AD
    conn = ldap.initialize("ldap://babraham.ac.uk")
    conn.set_option(ldap.OPT_REFERRALS, 0)
    try:
        conn.simple_bind_s(username+"@babraham.ac.uk", password)
        sessioncode = generate_id(20)

        # We either need to update an existing person, or create
        # a new entry
        person = people.find_one({"username":username})

        if not person:
            new_person = {
                "username": username,
                "disabled": False,
                "sessioncode": ""
            }
        
            people.insert_one(new_person)


        people.update_one({"username":username},{"$set":{"sessioncode": sessioncode}})

        return(sessioncode)
    
    except ldap.INVALID_CREDENTIALS:
        raise Exception("Incorrect Username/Password from LDAP")

@app.route("/validate_session", methods = ['POST', 'GET'])
def validate_session():
    form = get_form()
    person = checksession(form["session"])
    return(str(person["username"]))

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
    with open(Path(__file__).parent.parent / "configuration/conf.json") as infh:
        conf = json.loads(infh.read())
    return conf


def connect_to_database(conf):

    client = MongoClient(
        conf['server']['address'],
        username = conf['server']['username'],
        password = conf['server']['password'],
        authSource = "groupactivity_database"
    )


    db = client.groupactivity_database

    global people
    people = db.people_collection


# Read the main configuration
server_conf = get_server_configuration()

# Connect to the database
connect_to_database(server_conf)


