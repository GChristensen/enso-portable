
from telnetlib import Telnet

HOST = "192.168.1.1"
USER = "root"
PASSWORD = "" # provide a password
IFACE = "ra0"

def cmd_switch_wireless(ensoapi):
    """Turn wi-fi on/off"""
    tn = Telnet(HOST)
    tn.read_until("login: ")
    tn.write(USER + "\n")
    tn.read_until("Password: ")
    tn.write(PASSWORD + "\n")
    tn.write("".join(("ifconfig ", IFACE, "\n")))
    
    tn_out = tn.read_until("Interrupt")
    
    cmd = ""
    
    if tn_out.find(" UP ") != -1: 
        cmd = " down"
    else:
        cmd = " up"
    
    if len(cmd) != 0:
        tn.write("".join(("ifconfig ", IFACE, cmd, "\n")))
    
    tn.write("exit\n")
    tn.read_all()