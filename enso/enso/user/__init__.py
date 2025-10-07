# A module for various user code

import os
import sys
import importlib.util

def import_if_exists(file_path):
    # Check if file exists
    if os.path.exists(file_path):
        try:
            # Get the module name from the file path
            module_name = os.path.splitext(os.path.basename(file_path))[0]

            # Create a spec for the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            # Check if spec was created successfully
            if spec is None:
                print(f"Failed to create spec for {file_path}")
                return None

            # Create a new module based on the spec
            module = importlib.util.module_from_spec(spec)

            # Execute the module
            spec.loader.exec_module(module)
            print(f"Successfully imported {file_path}")
            return module

        except Exception as e:
            print(f"Error importing {file_path}: {str(e)}")
            return None
    else:
        print(f"File {file_path} does not exist")
        return None


def import_package_by_path(package_dir_path):
    """
    Imports a Python package by its directory path.

    Args:
        package_dir_path (str): The absolute path to the package directory
                                 (the directory containing __init__.py).

    Returns:
        module: The imported package module, or None if an error occurs.
    """
    if not os.path.isdir(package_dir_path):
        print(f"Error: {package_dir_path} is not a directory.")
        return None
    if not os.path.exists(os.path.join(package_dir_path, '__init__.py')):
        print(f"Error: {package_dir_path} does not appear to be a package (missing __init__.py).")
        return None

    # Get the parent directory of the package
    parent_dir = os.path.dirname(package_dir_path)
    # Get the package name (the directory's base name)
    package_name = os.path.basename(package_dir_path)

    # Add the parent directory to sys.path
    # This allows Python to find the package when imported by name
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir) # Insert at the beginning to prioritize

    try:
        # Import the package by its name
        module = importlib.import_module(package_name)
        print(f"Successfully imported package {package_name} from {package_dir_path}")
        return module
    except ImportError as e:
        print(f"Error importing package {package_name} from {package_dir_path}: {str(e)}")
        return None
    finally:
        # Crucially, remove the added path to avoid side effects
        if parent_dir in sys.path:
            sys.path.remove(parent_dir)