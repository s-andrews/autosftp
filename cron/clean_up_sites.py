#!/srv/autosftp/venv/bin/python
from pathlib import Path
import json
from pymongo import MongoClient
import datetime
import subprocess
import shutil


# We need the python in the shebang to be the one in the venv 
# so we've definitely got the packages we need.


def main():
    # Read the main configuration
    global server_conf
    server_conf = get_server_configuration()

    # Connect to the database
    connect_to_database(server_conf)

    # Find the full list of sites
    site_list = sites.find({})

    for site in site_list:
        if site["expires"] < datetime.datetime.now():
            print(site["username"]+" has expired - deleting")
            delete_site(site)

    # Find the set of home directories and see
    # if any don't match to sites
            
    for account in Path(server_conf["server"]["home"]).iterdir():
        site = account.name.split("/")[-1]

        # Let's do a quick sanity check that we're not deleting something we
        # shouldn't
        sections = site.split("-")
        if len(sections) == 3 and sections[-1].isdigit():
            # It looks like a real account name

            # We need to check if there is a database entry associated 
            # with this directory
            found_site = sites.find_one({"username":site})
            if found_site:
                continue

            print(site+" appears to be an abandoned account")
            delete_user_data(site)
        else:
            print("Account "+site+" doesn't look like one of ours.")


def delete_site(site):
    # We're deleting a site that's going to happen in a couple of stages
    # 1. Delete the entry from the database
    # 2. Delete the user from the system
    # 3. Delete the home directory and all files

    # Delete the database entry - pretty simple
    sites.delete_one(site)

    # Delete the user and data
    delete_user_data(site["username"])


def delete_user_data(site):

    print("Deleting data from "+site)
    # We may or may not have a user.  If there is a user they could be logged in so we need to 
    # kill all of their processes before we can remove them.  They should be removed already

    subprocess.run(["/usr/bin/killall","-9","-u",site], check=False)
    subprocess.run(["/usr/sbin/userdel",site], check=False)

    # Now we need to remove their home directory and all data
    homedir = Path(server_conf["server"]["home"]+"/"+site)
    if homedir.exists():
        shutil.rmtree(homedir)




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

