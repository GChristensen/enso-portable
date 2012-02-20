import xdg.BaseDirectory

def get_script_folder_name():
  """Returns the folder where Enso commands are found. This function
     is responsible for ensuring that this folder exists: it must not
     return a path that is not present! It is expected to place this
     folder in some platform-specific logical location."""
  return xdg.BaseDirectory.save_data_path('enso','commands')


