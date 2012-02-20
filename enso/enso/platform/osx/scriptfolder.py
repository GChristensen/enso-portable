import os

def get_script_folder_name():
  """Returns the folder where Enso commands are found. This function
     is responsible for ensuring that this folder exists: it must not
     return a path that is not present! It is expected to place this
     folder in some platform-specific logical location."""
  enso_command_path = os.path.expanduser('~/Library/Application Support/enso/commands')
  if (not os.path.isdir(enso_command_path)):
    os.makedirs(enso_command_path)
  return enso_command_path 

