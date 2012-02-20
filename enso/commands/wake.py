
from telnetlib import Telnet

HOST = "192.168.1.1"
USER = "root"
PASSWORD = "" # provide a password

def cmd_wake_slave(ensoapi):
    """Wake slave server"""
    tn = Telnet(HOST)
    tn.read_until("login: ")
    tn.write(USER + "\n")
    tn.read_until("Password: ")
    tn.write(PASSWORD + "\n")

    tn.write("/usr/sbin/wol -i 192.168.1.255 -p 9 xx:xx:xx:xx:xx:xx\n") # provide a MAC address
    tn.write("exit\n")
    tn.read_all()