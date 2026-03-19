import json
import os
import importlib.util
import logging

# Function to read the config module from a JSON file
def read_config_module(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Function to load configuration file
def load_configuration(version, code_files_path):
    config_file = os.path.join(code_files_path, f"Batch({version})", f"ConfigurationPlotSpec({version})", f"configurations({version}).py")
    spec = importlib.util.spec_from_file_location("config", config_file)
    config_received = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_received)
    return config_received