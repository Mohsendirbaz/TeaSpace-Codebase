import json
import os
import pandas as pd
import importlib.util
import sys
import copy
import logging
from pathlib import Path

# =====================================================================
# CONFIG_MODULES - CONFIGURATION MODULE PROCESSOR (Updated for Matrix-Based Form Values)
# =====================================================================
# This module is responsible for processing configuration matrices and creating
# distinct configuration modules for different time intervals. It reads configuration
# data from matrices created by module1.py and generates JSON configuration files
# for each interval with the appropriate filtered values.
#
# The module handles:
# 1. Reading configuration matrices from CSV files
# 2. Processing filtered values for each interval
# 3. Creating distinct configuration modules for each interval
# 4. Handling special vector values (Amount4, Amount5, Amount6, Amount7)
# 5. Saving configuration modules as JSON files
# =====================================================================

# Initialize logging
log_file_path = os.path.join(os.getcwd(), 'config_modules.log')
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s %(message)s')

# Function to parse the filtered_values string and convert it into a dictionary
def parse_filtered_values(filtered_values):
    """
    Parse a filtered_values string into a Python dictionary.

    This function converts a JSON string representation of filtered values into
    a Python dictionary. It handles special cases where double quotes might be
    escaped incorrectly.

    Args:
        filtered_values (str): JSON string representation of filtered values

    Returns:
        list or dict: Parsed filtered values as a Python object
                     Returns an empty list if parsing fails
    """
    try:
        # Convert double-double quotes for strings to single double-quotes before parsing
        # This is needed because some JSON strings might have incorrectly escaped quotes
        filtered_values_dict = json.loads(filtered_values.replace('""', '"'))
        return filtered_values_dict
    except json.JSONDecodeError as e:
        # Log the error and return an empty list if parsing fails
        print(f"Error parsing filtered_values: {filtered_values}. Error: {e}")
        return []

# Function to strip unnecessary quotes from numeric values
def strip_value(value):
    """
    Strip quotes from numeric values and convert to appropriate types.

    This function attempts to convert string values to their appropriate
    numeric types (float or int) when possible. It keeps non-numeric
    values as strings.

    Args:
        value (str or other): The value to process

    Returns:
        int, float, or original type: Converted value if possible, otherwise original value
    """
    if isinstance(value, str):
        try:
            if '.' in value:
                return float(value)  # Handle floats
            return int(value)  # Handle integers
        except ValueError:
            return value  # Return string as is if conversion fails
    return value  # Return non-string values unchanged

# Helper function to find the index from the fv_id (e.g., Amount4, Amount5)
def find_index_from_id(fv_id):
    """
    Extract the numeric index from an ID string.

    This function extracts the numeric part from an ID string (assuming it ends with a number)
    and returns the 0-based index. This is used for mapping IDs like "variableCostsAmount4_1"
    to the correct index in a vector.

    Args:
        fv_id (str): ID string containing a numeric part

    Returns:
        int or None: 0-based index extracted from the ID, or None if extraction fails
    """
    try:
        # For variableCostsAmount4_1 or similar patterns
        if '_' in fv_id:
            index_part = fv_id.split('_')[-1]
            return int(index_part) - 1  # Convert to 0-based index
        else:
            # For older format IDs, extract all digits
            index_part = ''.join([c for c in fv_id if c.isdigit()])
            return int(index_part) - 1  # Convert to 0-based index
    except ValueError:
        # Return None if no valid index can be extracted
        return None

def ensure_clean_directory(file_path):
    """
    Ensure the directory exists and the file doesn't exist before saving.

    This function prepares the filesystem for saving a new file by:
    1. Creating the directory path if it doesn't exist
    2. Removing the file if it already exists

    Args:
        file_path (str): Full path to the file to be saved

    Returns:
        None
    """
    # Extract the directory path from the file path
    dir_path = os.path.dirname(file_path)

    # Create the directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Remove the file if it already exists
    if os.path.exists(file_path):
        os.remove(file_path)

# Function to update the config module with filtered values and save it as a JSON file
def update_and_save_config_module(config_received, config_matrix_df, results_folder, version):
    """
    Update configuration modules with filtered values and save them as JSON files.

    This function is the core of the config_modules processing. It:
    1. Iterates through each row in the configuration matrix
    2. Creates a distinct configuration module for each interval
    3. Updates the module with the appropriate filtered values
    4. Handles special vector values (Amount4, Amount5, Amount6, Amount7)
    5. Saves each module as a JSON file

    Args:
        config_received: Base configuration object with default values
        config_matrix_df (DataFrame): DataFrame containing configuration matrix data
                                     with start, end, and filtered_values columns
        results_folder (str): Path to the folder where results will be saved
        version (str or int): Version number for the configuration

    Returns:
        None: Results are saved to files

    Raises:
        Exception: Catches and logs any exceptions that occur during processing
    """
    try:
        # Iterate through the config matrix and create distinct config modules for each interval
        for idx, row in config_matrix_df.iterrows():
            # Extract the start and end years for this interval
            start_year = int(row['start'])
            end_year = int(row['end'])
            filtered_values = row['filtered_values']

            # Parse the filtered_values string into a dictionary if it's a string
            # This is needed because the filtered_values column might contain JSON strings
            if isinstance(filtered_values, str):
                filtered_values = parse_filtered_values(filtered_values)

            # Create a distinct config module for the current interval
            # This uses Python's importlib to create a module object dynamically
            config_module = importlib.util.module_from_spec(importlib.util.spec_from_loader('config_module', loader=None))

            # Copy all attributes from the base configuration to the new module
            for param in dir(config_received):
                if not param.startswith('__'):  # Skip built-in attributes
                    # Make a deep copy to ensure previous updates are not propagated
                    # This is important to avoid modifying the same object across different intervals
                    setattr(config_module, param, copy.deepcopy(getattr(config_received, param)))

            # Process filtered values and update the config module
            for item in filtered_values:
                # Extract the ID, value, and remarks from the filtered value
                fv_id = item.get('id')
                value = strip_value(item.get('value'))  # Convert to appropriate type
                remarks = item.get('remarks')

                # Skip processing if ID is missing
                if not fv_id:
                    continue

                # Only update if the remark is not "Default entry"
                # Default entries are skipped to avoid overriding with default values
                if remarks != "Default entry":
                    # Special handling for vector values (Amount4, Amount5, Amount6, Amount7)
                    if 'variableCostsAmount4' in fv_id:
                        # Update variable_costsAmount4 vector
                        vector_to_update = getattr(config_module, 'variable_costsAmount4', None)
                        if vector_to_update is not None:
                            # Find the index in the vector to update
                            index = find_index_from_id(fv_id)
                            if index is not None and 0 <= index < len(vector_to_update):
                                # Update the value at the specified index
                                vector_to_update[index] = value
                                print(f"Updated variable_costsAmount4 at index {index} to {value} for module {start_year}-{end_year}")
                            else:
                                print(f"Index {index} for {fv_id} is out of bounds or invalid.")
                        else:
                            print(f"variable_costsAmount4 not found in config module {start_year}-{end_year}.")
                    elif 'amounts_per_unitAmount5' in fv_id:
                        # Update amounts_per_unitAmount5 vector
                        vector_to_update = getattr(config_module, 'amounts_per_unitAmount5', None)
                        if vector_to_update is not None:
                            # Find the index in the vector to update
                            index = find_index_from_id(fv_id)
                            if index is not None and 0 <= index < len(vector_to_update):
                                # Update the value at the specified index
                                vector_to_update[index] = value
                                print(f"Updated amounts_per_unitAmount5 at index {index} to {value} for module {start_year}-{end_year}")
                            else:
                                print(f"Index {index} for {fv_id} is out of bounds or invalid.")
                        else:
                            print(f"amounts_per_unitAmount5 not found in config module {start_year}-{end_year}.")
                    elif 'variable_RevAmount6' in fv_id:
                        # Update variable_RevAmount6 vector
                        vector_to_update = getattr(config_module, 'variable_RevAmount6', None)
                        if vector_to_update is not None:
                            # Find the index in the vector to update
                            index = find_index_from_id(fv_id)
                            if index is not None and 0 <= index < len(vector_to_update):
                                # Update the value at the specified index
                                vector_to_update[index] = value
                                print(f"Updated variable_RevAmount6 at index {index} to {value} for module {start_year}-{end_year}")
                            else:
                                print(f"Index {index} for {fv_id} is out of bounds or invalid.")
                        else:
                            print(f"variable_RevAmount6 not found in config module {start_year}-{end_year}.")
                    elif 'amounts_per_unitRevAmount7' in fv_id:
                        # Update amounts_per_unitRevAmount7 vector
                        vector_to_update = getattr(config_module, 'amounts_per_unitRevAmount7', None)
                        if vector_to_update is not None:
                            # Find the index in the vector to update
                            index = find_index_from_id(fv_id)
                            if index is not None and 0 <= index < len(vector_to_update):
                                # Update the value at the specified index
                                vector_to_update[index] = value
                                print(f"Updated amounts_per_unitRevAmount7 at index {index} to {value} for module {start_year}-{end_year}")
                            else:
                                print(f"Index {index} for {fv_id} is out of bounds or invalid.")
                        else:
                            print(f"amounts_per_unitRevAmount7 not found in config module {start_year}-{end_year}.")
                    # Handle special vAmount and rAmount fields from matrix
                    elif 'vAmount' in fv_id:
                        # For vAmount fields, also update the corresponding variableCostsAmount4 index
                        # Example: vAmount40 corresponds to variableCostsAmount4[0]
                        setattr(config_module, fv_id, value)
                        
                        vIndex = int(fv_id.replace('vAmount', ''))
                        vector_index = vIndex - 40  # Calculate vector index (40 -> 0, 41 -> 1, etc.)
                        
                        if 0 <= vector_index < 10:  # Ensure index is in range
                            vector_to_update = getattr(config_module, 'variable_costsAmount4', None)
                            if vector_to_update is not None:
                                vector_to_update[vector_index] = value
                                print(f"Updated variable_costsAmount4 at index {vector_index} to {value} from {fv_id}")
                    elif 'rAmount' in fv_id:
                        # For rAmount fields, also update the corresponding amounts_per_unitAmount5 index
                        # Example: rAmount60 corresponds to amounts_per_unitAmount5[0]
                        setattr(config_module, fv_id, value)
                        
                        rIndex = int(fv_id.replace('rAmount', ''))
                        vector_index = rIndex - 60  # Calculate vector index (60 -> 0, 61 -> 1, etc.)
                        
                        if 0 <= vector_index < 10:  # Ensure index is in range
                            vector_to_update = getattr(config_module, 'amounts_per_unitAmount5', None)
                            if vector_to_update is not None:
                                vector_to_update[vector_index] = value
                                print(f"Updated amounts_per_unitAmount5 at index {vector_index} to {value} from {fv_id}")
                    else:
                        # For other IDs, directly set the value as an attribute
                        setattr(config_module, fv_id, value)
                        print(f"Updated {fv_id} to {value} for module {start_year}-{end_year}")
                        logging.info(f"Updated {fv_id} to {value} for module {start_year}-{end_year}")

            # Convert the config module to a dictionary for JSON serialization
            # This extracts all non-built-in attributes from the module
            config_module_dict = {param: getattr(config_module, param) for param in dir(config_module) if not param.startswith('__')}

            # Define the output file path
            config_module_file = os.path.join(results_folder, f"{version}_config_module_{start_year}.json")

            # Ensure the directory exists and the file doesn't exist
            ensure_clean_directory(config_module_file)

            # Write the config module to a JSON file
            with open(config_module_file, 'w') as f:
                json.dump(config_module_dict, f, indent=4)

            print(f"Config module {start_year}-{end_year} saved in {results_folder}")

    except Exception as e:
        # Catch and log any exceptions that occur during processing
        print(f"An error occurred: {str(e)}")
        logging.error(f"Error in update_and_save_config_module: {str(e)}")
        raise