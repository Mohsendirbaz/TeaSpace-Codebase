import sys
import json
import logging
import os
import pandas as pd
from pathlib import Path

# =====================================================================
# TABLE MODULE - CONFIGURATION TABLE GENERATOR (Updated for Matrix-Based Form Values)
# =====================================================================
# This module is responsible for building a comprehensive table of configuration
# properties from multiple configuration modules. It reads configuration modules
# created by config_modules.py and combines them into a single table that shows
# how property values change over time.
#
# The module handles:
# 1. Loading configuration modules from JSON files
# 2. Extracting properties from each module, including vector properties
# 3. Building a time-series table with years as rows and properties as columns
# 4. Forward-filling missing values to ensure continuity
# 5. Saving the resulting table as a CSV file
# =====================================================================

# Set pandas option to handle future behavior for downcasting
# This prevents warnings about implicit downcasting in pandas operations
pd.set_option('future.no_silent_downcasting', True)

# Add the parent directory to the Python path to enable imports from sibling modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize logging
log_file_path = os.path.join(os.getcwd(), 'Table.log')
logging.basicConfig(
    filename=log_file_path,
    filemode='w',  # 'w' mode overwrites the log file each time
    level=logging.INFO,
    format='%(message)s'  # Simple message format without timestamps
)

# Property mapping from IDs to human-readable names
property_mapping = {
    "plantLifetimeAmount10": "Plant Lifetime",
    "bECAmount11": "Bare Erected Cost",
    "numberOfUnitsAmount12": "Number of Units",
    "initialSellingPriceAmount13": "Price",
    "totalOperatingCostPercentageAmount14": "Direct Total Operating Cost Percentage as % of Revenue",
    "engineering_Procurement_and_Construction_EPC_Amount15": "Engineering Procurement and Construction as % of BEC",
    "process_contingency_PC_Amount16": "Process Contingency as % of BEC",
    "project_Contingency_PT_BEC_EPC_PCAmount17": "Project Contingency as % of BEC, EPC, PC",
    "use_direct_operating_expensesAmount18": "Use Direct Operating Expenses",
    "use_direct_revenueAmount19": "Use Direct Revenue",
    "depreciationMethodAmount20": "Depreciation Method",
    "loanTypeAmount21": "Loan Type",
    "interestTypeAmount22": "Interest Type",
    "generalInflationRateAmount23": "General Inflation Rate",
    "interestProportionAmount24": "Interest Proportion",
    "principalProportionAmount25": "Principal Proportion",
    "loanPercentageAmount26": "Loan Percentage of TOC",
    "repaymentPercentageOfRevenueAmount27": "Repayment Percentage Of Revenue",
    "numberofconstructionYearsAmount28": "Number of Construction Years",
    "iRRAmount30": "Internal Rate of Return",
    "annualInterestRateAmount31": "Annual Interest Rate",
    "stateTaxRateAmount32": "State Tax Rate",
    "federalTaxRateAmount33": "Federal Tax Rate",
    "rawmaterialAmount34": "Feedstock Cost",
    "laborAmount35": "Labor Cost",
    "utilityAmount36": "Utility Cost",
    "maintenanceAmount37": "Maintenance Cost",
    "insuranceAmount38": "Insurance Cost",
    "RFAmount80": "Material Revenue",
    "RFAmount81": "Labor Revenue",
    "RFAmount82": "Utility Revenue",
    "RFAmount83": "Maintenance Revenue",
    "RFAmount84": "Insurance Revenue",
    "vAmount40": "v40",
    "vAmount41": "v41",
    "vAmount42": "v42",
    "vAmount43": "v43",
    "vAmount44": "v44",
    "vAmount45": "v45",
    "vAmount46": "v46",
    "vAmount47": "v47",
    "vAmount48": "v48",
    "vAmount49": "v49",
    "vAmount50": "v50",
    "vAmount51": "v51",
    "vAmount52": "v52",
    "vAmount53": "v53",
    "vAmount54": "v54",
    "vAmount55": "v55",
    "vAmount56": "v56",
    "vAmount57": "v57",
    "vAmount58": "v58",
    "vAmount59": "v59",
    "rAmount60": "r60",
    "rAmount61": "r61",
    "rAmount62": "r62",
    "rAmount63": "r63",
    "rAmount64": "r64",
    "rAmount65": "r65",
    "rAmount66": "r66",
    "rAmount67": "r67",
    "rAmount68": "r68",
    "rAmount69": "r69",
    "rAmount70": "r70",
    "rAmount71": "r71",
    "rAmount72": "r72",
    "rAmount73": "r73",
    "rAmount74": "r74",
    "rAmount75": "r75",
    "rAmount76": "r76",
    "rAmount77": "r77",
    "rAmount78": "r78",
    "rAmount79": "r79",
    "variableCostsAmount4_1": "Variable Costs Item 1",
    "variableCostsAmount4_2": "Variable Costs Item 2",
    "variableCostsAmount4_3": "Variable Costs Item 3",
    "variableCostsAmount4_4": "Variable Costs Item 4",
    "variableCostsAmount4_5": "Variable Costs Item 5",
    "variableCostsAmount4_6": "Variable Costs Item 6",
    "variableCostsAmount4_7": "Variable Costs Item 7",
    "variableCostsAmount4_8": "Variable Costs Item 8",
    "variableCostsAmount4_9": "Variable Costs Item 9",
    "variableCostsAmount4_10": "Variable Costs Item 10",
    "amounts_per_unitAmount5_1": "Amounts Per Unit Item 1",
    "amounts_per_unitAmount5_2": "Amounts Per Unit Item 2",
    "amounts_per_unitAmount5_3": "Amounts Per Unit Item 3",
    "amounts_per_unitAmount5_4": "Amounts Per Unit Item 4",
    "amounts_per_unitAmount5_5": "Amounts Per Unit Item 5",
    "amounts_per_unitAmount5_6": "Amounts Per Unit Item 6",
    "amounts_per_unitAmount5_7": "Amounts Per Unit Item 7",
    "amounts_per_unitAmount5_8": "Amounts Per Unit Item 8",
    "amounts_per_unitAmount5_9": "Amounts Per Unit Item 9",
    "amounts_per_unitAmount5_10": "Amounts Per Unit Item 10",
    "variable_RevAmount6_1": "Variable Rev Item 1",
    "variable_RevAmount6_2": "Variable Rev Item 2",
    "variable_RevAmount6_3": "Variable Rev Item 3",
    "variable_RevAmount6_4": "Variable Rev Item 4",
    "variable_RevAmount6_5": "Variable Rev Item 5",
    "variable_RevAmount6_6": "Variable Rev Item 6",
    "variable_RevAmount6_7": "Variable Rev Item 7",
    "variable_RevAmount6_8": "Variable Rev Item 8",
    "variable_RevAmount6_9": "Variable Rev Item 9",
    "variable_RevAmount6_10": "Variable Rev Item 10",
    "amounts_per_unitRevAmount7_1": "Amounts Per Unit Rev Item 1",
    "amounts_per_unitRevAmount7_2": "Amounts Per Unit Rev Item 2",
    "amounts_per_unitRevAmount7_3": "Amounts Per Unit Rev Item 3",
    "amounts_per_unitRevAmount7_4": "Amounts Per Unit Rev Item 4",
    "amounts_per_unitRevAmount7_5": "Amounts Per Unit Rev Item 5",
    "amounts_per_unitRevAmount7_6": "Amounts Per Unit Rev Item 6",
    "amounts_per_unitRevAmount7_7": "Amounts Per Unit Rev Item 7",
    "amounts_per_unitRevAmount7_8": "Amounts Per Unit Rev Item 8",
    "amounts_per_unitRevAmount7_9": "Amounts Per Unit Rev Item 9",
    "amounts_per_unitRevAmount7_10": "Amounts Per Unit Rev Item 10",
}

def expand_vector_properties(properties, prop_name, vector):
    """
    Helper function to expand vector properties with numbered extensions.

    This function takes a vector property (like variable_costsAmount4) and expands it
    into multiple individual properties with numbered extensions (e.g., Variable Costs_1,
    Variable Costs_2, etc.). This makes it easier to represent vector values in a table.

    Args:
        properties (list): List of property dictionaries to append to
        prop_name (str): Name of the property (used for mapping to a readable name)
        vector (list): List of values to expand into individual properties

    Returns:
        list: Updated list of properties with the expanded vector properties added
    """
    if isinstance(vector, list):
        # Enumerate starting from 1 to give human-readable indices
        for i, value in enumerate(vector, 1):
            # Get the mapped name or use the original name if no mapping exists
            # Then append the index to create a unique name for each vector element
            presentable_name = f"{property_mapping.get(prop_name, prop_name)}_{i}"
            properties.append({'Property Name': presentable_name, 'Value': value})
    return properties

def collect_properties_from_config_module(config_module):
    """
    Collect properties from a config module, properly handling vectors.

    This function extracts all properties from a configuration module and
    converts them to a list of dictionaries with 'Property Name' and 'Value' keys.
    It handles special vector properties by expanding them using expand_vector_properties.

    Args:
        config_module (dict): Configuration module dictionary loaded from JSON

    Returns:
        list: List of dictionaries with 'Property Name' and 'Value' keys
    """
    properties = []

    # Iterate through all properties in the config module
    for prop in config_module.keys():
        if prop == 'variable_costsAmount4':
            # Handle variable_costsAmount4 vector specially
            properties = expand_vector_properties(properties, prop, config_module[prop])
        elif prop == 'amounts_per_unitAmount5':
            # Handle amounts_per_unitAmount5 vector specially
            properties = expand_vector_properties(properties, prop, config_module[prop])
        elif prop == 'variable_RevAmount6':
            # Handle variable_RevAmount6 vector specially
            properties = expand_vector_properties(properties, prop, config_module[prop])
        elif prop == 'amounts_per_unitRevAmount7':
            # Handle amounts_per_unitRevAmount7 vector specially
            properties = expand_vector_properties(properties, prop, config_module[prop])
        # Handle matrix-based form values with special naming conventions
        elif prop.startswith('vAmount'):
            # For vAmount properties, use property mapping or default name with index
            presentable_name = property_mapping.get(prop, prop)
            properties.append({'Property Name': presentable_name, 'Value': config_module[prop]})
        elif prop.startswith('rAmount'):
            # For rAmount properties, use property mapping or default name with index
            presentable_name = property_mapping.get(prop, prop)
            properties.append({'Property Name': presentable_name, 'Value': config_module[prop]})
        else:
            # For non-vector properties, just map the name and add to the list
            presentable_name = property_mapping.get(prop, prop)
            properties.append({'Property Name': presentable_name, 'Value': config_module[prop]})

    return properties

def load_config_modules(results_folder, version):
    """
    Load all config modules from the results folder.

    This function scans the results folder for configuration module JSON files
    that match the specified version, loads them, and returns them as a list
    of tuples containing the start year and the module data.

    Args:
        results_folder (str or Path): Path to the folder containing configuration module files
        version (str or int): Version number to filter configuration module files

    Returns:
        list: List of tuples (start_year, config_module) sorted by start_year
    """
    config_modules = []
    results_folder = Path(results_folder)  # Convert to Path object for better path handling

    # Scan the results folder for configuration module files
    for file in results_folder.glob(f"{version}_config_module_*.json"):
        # Extract the start year from the filename
        # The filename format is "{version}_config_module_{start_year}.json"
        start_year = int(file.stem.split('_')[-1])
        
        # Load the configuration module from the JSON file
        try:
            with open(file, 'r') as f:
                config_module = json.load(f)
                # Add the start year and config module as a tuple to the list
                config_modules.append((start_year, config_module))
        except Exception as e:
            logging.error(f"Error loading config module {file}: {str(e)}")
    
    # Sort the config modules by start year to ensure chronological order
    config_modules.sort(key=lambda x: x[0])
    logging.info(f"Loaded {len(config_modules)} config modules.")
    
    return config_modules

def build_and_save_table(version):
    """
    Build and save a comprehensive table of configuration properties.

    This function is the core of the Table module. It:
    1. Loads all configuration modules for the specified version
    2. Extracts properties from each module
    3. Creates a DataFrame with years as rows and properties as columns
    4. Fills the DataFrame with values from each module
    5. Forward-fills missing values to ensure continuity
    6. Saves the resulting table as a CSV file

    Args:
        version (str or int): Version number for the configuration

    Returns:
        dict: Result status of the operation with either:
            - {"message": "success message", "file": "file_path"} for successful operations
            - {"error": "error message"} for failed operations
    """
    try:
        # Set up paths to the results folder
        script_dir = Path(__file__).resolve().parent.parent
        code_files_path = script_dir.parent / "Original"
        results_folder = code_files_path / f"Batch({version})" / f"Results({version})"
        
        # Ensure the results folder exists
        if not results_folder.exists():
            os.makedirs(results_folder)

        # Load all configuration modules for the specified version
        config_modules = load_config_modules(results_folder, version)
        if not config_modules:
            # If no modules are found, log an error and return
            error_msg = "No config modules found in results folder"
            logging.error(error_msg)
            return {"error": error_msg}

        # Get properties from the first module to set up the DataFrame
        # This establishes the columns of the table
        first_module_properties = collect_properties_from_config_module(config_modules[0][1])
        column_headers = [prop['Property Name'] for prop in first_module_properties]

        # Create DataFrame with all properties for each year
        # The rows are years from 1 to plant lifetime
        plant_lifetime = config_modules[0][1].get('plantLifetimeAmount10', 20)  # Default to 20 if not found
        df = pd.DataFrame(index=range(1, plant_lifetime + 1), columns=column_headers)

        # Fill the DataFrame with values from each config module
        # Each module corresponds to a specific start year
        for start_year, config_module in config_modules:
            # Extract properties from the module
            properties = collect_properties_from_config_module(config_module)
            # Assign each property value to the corresponding cell in the DataFrame
            for prop in properties:
                df.loc[start_year, prop['Property Name']] = prop['Value']

        # Forward fill any missing values and handle deprecation warning
        # This ensures that property values persist until they are explicitly changed
        df = df.ffill().infer_objects(copy=False)

        # Save the DataFrame to a CSV file
        save_path = results_folder / f"Variable_Table({version}).csv"
        df.to_csv(save_path, index_label='Year')
        logging.info(f"Table saved successfully to {save_path}")
        
        return {
            "message": f"Successfully built and saved variable table for version {version}",
            "file": str(save_path)
        }
    
    except Exception as e:
        # Log any errors that occur
        error_msg = f"Error building table: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}

# Create Flask API handler if this file is used as a server
def create_table_api():
    """Create a Flask API for the Table module functionality.
    
    Returns:
        Flask app: A Flask application with Table module endpoints
    """
    from flask import Flask, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/table/<version>', methods=['GET'])
    def run_table(version):
        """Run the Table module for a specific version."""
        result = build_and_save_table(version)
        return jsonify(result)
    
    return app

def main(version):
    """
    Main function to build and save the configuration table.

    This function serves as the entry point for the Table module.
    It calls build_and_save_table and handles any exceptions that occur.

    Args:
        version (str or int): Version number for the configuration

    Returns:
        dict: Result status of the operation
    """
    try:
        # Call the main function to build and save the table
        return build_and_save_table(version)
    except Exception as e:
        # Log any errors that occur
        error_msg = f"Error in main function: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}

# Main Execution Block
# This section is executed when the script is run directly (not imported)
if __name__ == "__main__":
    # Get the version from command line arguments or use default value 1
    version = sys.argv[1] if len(sys.argv) > 1 else 1

    # Call the main function with the specified version
    result = main(version)
    print(result)
    
    # If there are more than 2 arguments and the second one is "server",
    # start the Flask server for API access
    if len(sys.argv) > 2 and sys.argv[2] == "server":
        app = create_table_api()
        app.run(host='0.0.0.0', port=3054)
