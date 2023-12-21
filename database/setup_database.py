#!/usr/bin/env python3
import json
from pymongo import MongoClient
from pathlib import Path
from urllib.parse import quote_plus

def main():
    # Set up the database connection
    with open(Path(__file__).parent.parent / "configuration/conf.json") as infh:
        conf = json.loads(infh.read())

    print("Server",quote_plus(conf['server']['address']))
    print("Username",quote_plus(conf['server']['username']))
    print("Password",quote_plus(conf['server']['password']))

    client = MongoClient(
        conf['server']['address'],
        username = conf['server']['username'],
        password = conf['server']['password'],
        authSource = "groupactivity_database"
    )
    db = client.groupactivity_database
    global sites
    global people
    sites = db.sites_collection
    people = db.people_collection

    # Remove everything so we're starting fresh
    people.delete_many({})
    sites.delete_many({})

if __name__ == "__main__":
    main()