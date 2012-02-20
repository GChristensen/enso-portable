from win32com.shell import shell, shellcon
import os

SYSTEMFOLDER_APPDATALOCAL = shellcon.CSIDL_LOCAL_APPDATA

def get_system_folder(folder_id):
   return shell.SHGetFolderPath(0, folder_id, 0, 0)

def get_script_folder_name():
  """Returns the folder where Enso commands are found. This function
     is responsible for ensuring that this folder exists: it must not
     return a path that is not present! It is expected to place this
     folder in some platform-specific logical location."""
#  SPECIALFOLDER_ENSOLOCAL_COMMANDS = os.path.join(
#   get_system_folder(SYSTEMFOLDER_APPDATALOCAL), "Enso", "commands")
#  if not os.path.isdir(SPECIALFOLDER_ENSOLOCAL_COMMANDS):
#    os.makedirs(SPECIALFOLDER_ENSOLOCAL_COMMANDS)
  ensoDir = os.path.dirname(os.path.realpath(__file__))
  ensoDir = os.path.dirname(ensoDir)
  ensoDir = os.path.dirname(ensoDir)
  return os.path.dirname(ensoDir) + "/commands"

