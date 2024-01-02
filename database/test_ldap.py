from pathlib import Path
import ldap
import getpass
import json

# Get the LDAP details
with open(Path(__file__).parent.parent / "configuration/conf.json") as infh:
    conf = json.loads(infh.read())

username = input("Username: ").strip()
password = getpass.getpass("Password: ").strip()

conn = ldap.initialize("ldap://"+conf["server"]["ldap"])
conn.set_option(ldap.OPT_REFERRALS, 0)
try:
    conn.simple_bind_s(username+"@"+conf["server"]["ldap"], password)
    filter = f"(&(sAMAccountName={username}))"

    search_attribute = ["distinguishedName","mail"]

    dc_string = ",".join(["DC="+x for x in conf["server"]["ldap"].split(".")])

    res = conn.search(dc_string,ldap.SCOPE_SUBTREE, filter, search_attribute)
    answer = conn.result(res,0)
    print(answer)
    name = answer[1][0][1]["distinguishedName"][0].decode("utf8").split(",")[0].replace("CN=","")
    email = answer[1][0][1]["mail"][0].decode("utf8")
    print("Name of",username,"is",name,"email is",email)

except ldap.INVALID_CREDENTIALS:
    raise Exception("Incorrect Username/Password from LDAP")