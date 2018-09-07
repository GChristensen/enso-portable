import os
import json
from telnetlib import Telnet

options = {}
config = (os.environ["HOME"] if "HOME" in os.environ else "") + "/.enso/dd_wrt.json"

if os.path.exists(config):
    options = json.load(open(config))

HOST = options["host"].encode('ascii', 'ignore') if "host" in options else "192.168.1.1"
USER = options["user"].encode('ascii', 'ignore') if "user" in options else "root"
PASSWORD = options["password"].encode('ascii', 'ignore') if "password" in options else ""
IFACE = options["iface"].encode('ascii', 'ignore') if "iface" in options else "ra0"

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

def cmd_wake_slave(ensoapi):
    """Wake a slave server with a magic packet"""
    tn = Telnet(HOST)
    tn.read_until("login: ")
    tn.write(USER + "\n")
    tn.read_until("Password: ")
    tn.write(PASSWORD + "\n")

    tn.write("/usr/sbin/wol -i 192.168.1.255 -p 9 00:00:00:00:00:00\n") # provide a MAC address
    tn.write("exit\n")
    tn.read_all()

def cmd_wan_reconnect(ensoapi):
    """Reconnect WAN"""
    tn = Telnet(HOST)
    tn.read_until("login: ")
    tn.write(USER + "\n")
    tn.read_until("Password: ")
    tn.write(PASSWORD + "\n")

    tn.write("killall -HUP pppd\n")
    tn.write("exit\n")
    tn.read_all()
