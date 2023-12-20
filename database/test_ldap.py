import ldap
import getpass

username = input("Username: ").strip()
password = getpass.getpass("Password: ").strip()

conn = ldap.initialize("ldap://babraham.ac.uk")
conn.set_option(ldap.OPT_REFERRALS, 0)
try:
    conn.simple_bind_s(username+"@babraham.ac.uk", password)
    filter = f"(&(sAMAccountName={username}))"

    search_attribute = ["distinguishedName","mail"]

    res = conn.search("DC=babraham,DC=ac,DC=uk",ldap.SCOPE_SUBTREE, filter, search_attribute)
    answer = conn.result(res,0)
    print(answer)
    name = answer[1][0][1]["distinguishedName"][0].decode("utf8").split(",")[0].replace("CN=","")
    email = answer[1][0][1]["mail"][0].decode("utf8")
    print("Name of",username,"is",name,"email is",email)

except ldap.INVALID_CREDENTIALS:
    raise Exception("Incorrect Username/Password from LDAP")