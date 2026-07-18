from enso import config

options = vars(config)
MACHINES = options["WAKE_MACHINES"] if "WAKE_MACHINES" in options else {} #b"00:00:00:00:00:00"

def cmd_wake(ensoapi, machine):
    """Wake a machine with a magic packet sent to a given MAC-address
Requires the following variables at the custom initialization block:<br>
WAKE_MACHINES = {'server': "AA:BB:CC:DD:EE:FF"} # machine MACs
"""
    import socket
    mac_clean = MACHINES[machine].replace(':', '').replace('-', '').replace('.', '')
    magic_packet = b'\xff' * 6 + bytes.fromhex(mac_clean) * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.connect((b'192.168.1.255', 9))
        sock.send(magic_packet)

cmd_wake.valid_args = list(MACHINES.keys())
