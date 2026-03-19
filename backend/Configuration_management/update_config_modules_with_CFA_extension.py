import json
import os
import pandas as pd
import importlib.util
import sys
import copy
import logging

# Initialize logging
log_file_path = os.path.join(os.getcwd(), 'LogName.log')
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s %(message)s')
# Function to parse the filtered_values string and convert it into a dictionary
def parse_filtered_values(filtered_values):
    try:
        # Convert double-double quotes for strings to single double-quotes before parsing
        filtered_values_dict = json.loads(filtered_values.replace('""', '"'))
        return filtered_values_dict
    except json.JSONDecodeError as e:
        print(f"Error parsing filtered_values: {filtered_values}. Error: {e}")
        return []

# Function to strip unnecessary quotes from numeric values
def strip_value(value):
    """Strips quotes from numeric values and keeps strings quoted."""
    if isinstance(value, str):
        try:
            if '.' in value:
                return float(value)  # Handle floats
            return int(value)  # Handle integers
        except ValueError:
            return value  # Return string as is if conversion fails
    return value

# Helper function to find the index from the fv_id (e.g., Amount4, Amount5)
def find_index_from_id(fv_id):
    """
    Extracts the numeric part from the ID (assuming it ends with a number) 
    and returns the 0-based index.
    """
    try:
        index_part = ''.join([c for c in fv_id if c.isdigit()])
        return int(index_part) - 1  # Convert to 0-based index
    except ValueError:
        return None

# Function to update the config module with filtered values and save it as a JSON file
def update_and_save_config_module(config_received, config_matrix_df, results_folder, version):
    try:
        # Iterate through the config matrix and create distinct config modules for each interval
        for idx, row in config_matrix_df.iterrows():
            start_year = int(row['start'])
            end_year = int(row['end'])
            filtered_values = row['filtered_values']

            # Parse the filtered_values string into a dictionary
            if isinstance(filtered_values, str):
                filtered_values = parse_filtered_values(filtered_values)
            
            # Create a distinct config module for the current interval
            config_module = importlib.util.module_from_spec(importlib.util.spec_from_loader('config_module', loader=None))
          
            for param in dir(config_received):
             
                if not param.startswith('__'):
                    # Make a deep copy to ensure previous updates are not propagated
                    setattr(config_module, param, copy.deepcopy(getattr(config_received, param)))
                

            # Special treatment for Amount4 and Amount5 updates
            for item in filtered_values:
                fv_id = item.get('id')
                value = strip_value(item.get('value'))
                remarks = item.get('remarks')
                
                # Only update if the remark is not "Default entry"
                if remarks != "Default entry":
                    # Handle Amount4 and Amount5 updates
                    if 'Amount4' in fv_id:
                        vector_to_update = getattr(config_module, 'variable_costsAmount4', None)
                        if vector_to_update is not None:
                            index = find_index_from_id(fv_id)
                            if index is not None and 0 <= index < len(vector_to_update):
                                vector_to_update[index] = value
                                print(f"Updated variable_costsAmount4 at index {index} to {value} for module {start_year}-{end_year}")
                            else:
                                print(f"Index {index} for {fv_id} is out of bounds or invalid.")
                        else:
                            print(f"variable_costsAmount4 not found in config module {start_year}-{end_year}.")
                    elif 'Amount5' in fv_id:
                        vector_to_update = getattr(config_module, 'amounts_per_unitAmount5', None)
                        if vector_to_update is not None:
                            index = find_index_from_id(fv_id)
                            if index is not None and 0 <= index < len(vector_to_update):
                                vector_to_update[index] = value
                                print(f"Updated amounts_per_unitAmount5 at index {index} to {value} for module {start_year}-{end_year}")
                            else:
                                print(f"Index {index} for {fv_id} is out of bounds or invalid.")
                        else:
                            print(f"amounts_per_unitAmount5 not found in config module {start_year}-{end_year}.")
                    else:
                        # For other IDs, directly set the value
                        setattr(config_module, fv_id, value)
                        print(f"Updated {fv_id} to {value} for module {start_year}-{end_year}")
                        logging.info(f"Updated {fv_id} to {value} for module {start_year}-{end_year}")
            # Save the distinct updated config module as a JSON file with the version prefix
            config_module_dict = {param: getattr(config_module, param) for param in dir(config_module) if not param.startswith('__')}
            config_module_file = os.path.join(results_folder, f"{version}_config_module_{start_year}.json")
            with open(config_module_file, 'w') as f:
                json.dump(config_module_dict, f, indent=4)

            print(f"Config module {start_year}-{end_year} saved in {results_folder}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example function to demonstrate usage (this is just for context, not part of the core functionality)
def main(version, extension):
    # Set the path to the directory containing the modules
    code_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Original")
    
    results_folder = os.path.join(code_files_path,f"Batch({version}.{extension})", f"Results({version})")
    config_matrix_file = os.path.join(results_folder, f"General_Configuration_Matrix({version}).csv")

    # Load the config matrix (read once)
    config_matrix_df = pd.read_csv(config_matrix_file)

    # Set the path to the directory containing the configurations
    config_file = os.path.join(code_files_path, f"Batch({version}.{extension})", f"ConfigurationPlotSpec({version})", f"configurations({version}).py")
    spec = importlib.util.spec_from_file_location("config", config_file)
    config_received = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_received)

    # Run the update and save config modules
    update_and_save_config_module(config_received, config_matrix_df, results_folder, version)

# Accept version and extension as command-line arguments
if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else 1
    extension = sys.argv[2] if len(sys.argv) > 2 else 1
    main(version, extension)
