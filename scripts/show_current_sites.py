#!/usr/bin/env python3
from pathlib import Path
import json
from pymongo import MongoClient
import datetime
import subprocess
import shutil


# We need the python in the shebang to be the one in the venv 
# so we've definitely got the packages we need.


def main():

    site_details = []

    # Read the main configuration
    global server_conf
    server_conf = get_server_configuration()

    # Connect to the database
    connect_to_database(server_conf)

    # Find the full list of sites
    site_list = sites.find({})

    for site in site_list:

        person = people.find_one({"_id":site["user_id"]})

        size = int(subprocess.check_output(['du','-s', f"/home/{site['username']}"]).split()[0].decode('utf-8'))

        site_details.append({
            "username": site["username"],
            "owner": person["name"],
            "size": size,
            "name": site["name"]
        })

    site_details.sort(key=lambda x: x["size"], reverse=True)

    


    for site in site_details:
        print(f"{site['username']:<30} {site['owner']:<30} {format_bytes(site['size']*1024):>10} {site['name']}")


def format_bytes(size):
    step = 1024
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    
    for unit in units:
        if abs(size) < step:
            return f"{size:.2f} {unit}" if unit != "B" else f"{size} {unit}"
        size /= step
        
    return f"{size:.2f} {'EB'}"

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


if __name__ == "__main__":
    main()

