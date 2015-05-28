import os
import sys
import zlib
import pickle
import base64
import StringIO
import subprocess
from enso.platform import win32
from enso.platform.win32.scriptfolder import get_script_folder_name

def dump_table(table, file_path):
    dst = StringIO.StringIO()
    p = pickle.Pickler(dst)
    out = open(file_path, 'wb')
    pickle.dump(table, dst)
    out.write(base64.b64encode(zlib.compress(dst.getvalue())))
    out.close()

def restore_table(file_path):
    inp = open(file_path, 'rb')
    data = inp.read()
    inp.close()
    src = StringIO.StringIO(zlib.decompress(base64.b64decode(data)))
    up = pickle.Unpickler(src)
    return up.load()
    
def cmd_truecrypt_mount(ensoapi, letter):
    """Mount a truecrypt volume"""
    args = letter.split()
    containers = restore_table(get_script_folder_name() + "\\vdata.dat")
    if args[0] in containers:
        container = containers[args[0]]
        subprocess.call([os.environ["ProgramW6432"] +
                         "\\TrueCrypt\\TrueCrypt.exe", 
                         "/v", container,
                         "/l" + args[0], "/a", "/p", "", "/q"])

def cmd_truecrypt_umount(ensoapi):
    """Dismount a truecrypt volume"""
    subprocess.call([os.environ["ProgramW6432"] +
                     "\\TrueCrypt\\TrueCrypt.exe",
                     "/d", "/q", "/f"])
