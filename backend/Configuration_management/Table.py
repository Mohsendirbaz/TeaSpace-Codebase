import sys
import json
import logging
import os
import pandas as pd

# =====================================================================
# TABLE MODULE - CONFIGURATION TABLE GENERATOR
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

    Example:
        Input: 
            properties = []
            prop_name = "variable_costsAmount4"
            vector = [100, 200, 300]
        Output:
            [
                {'Property Name': 'Variable Costs_1', 'Value': 100},
                {'Property Name': 'Variable Costs_2', 'Value': 200},
                {'Property Name': 'Variable Costs_3', 'Value': 300}
            ]
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

    Processing Steps:
        1. Initialize an empty list to store properties
        2. Iterate through all properties in the config module
        3. Handle vector properties (variable_costsAmount4, amounts_per_unitAmount5, 
           variable_RevAmount6, amounts_per_unitRevAmount7) specially
        4. Map property IDs to readable names using property_mapping
        5. Return the complete list of properties
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
        results_folder (str): Path to the folder containing configuration module files
        version (str or int): Version number to filter configuration module files

    Returns:
        list: List of tuples (start_year, config_module) sorted by start_year

    Example:
        If the results folder contains:
            - 1_config_module_1.json
            - 1_config_module_5.json
            - 1_config_module_10.json

        The function will return:
            [(1, {...}), (5, {...}), (10, {...})]

        where {...} represents the loaded JSON content of each file.
    """
    config_modules = []

    # Scan the results folder for configuration module files
    for file in os.listdir(results_folder):
        # Filter files by prefix and suffix to find configuration modules for the specified version
        if file.startswith(f"{version}_config_module_") and file.endswith('.json'):
            file_path = os.path.join(results_folder, file)

            # Load the configuration module from the JSON file
            with open(file_path, 'r') as f:
                config_module = json.load(f)

                # Extract the start year from the filename
                # The filename format is "{version}_config_module_{start_year}.json"
                start_year = int(file.split('_')[-1].split('.')[0])

                # Add the start year and config module as a tuple to the list
                config_modules.append((start_year, config_module))

    # Sort the config modules by start year to ensure chronological order
    return sorted(config_modules, key=lambda x: x[0])

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
        None: Results are saved to a file

    Processing Steps:
        1. Set up paths to the results folder
        2. Load all configuration modules
        3. Extract properties and set up the DataFrame
        4. Fill the DataFrame with values from each module
        5. Forward-fill missing values
        6. Save the table to a CSV file
    """
    # Set up paths to the results folder
    # Navigate up three levels from the current file to find the "Original" directory
    code_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Original")
    results_folder = os.path.join(code_files_path, f'Batch({version})', f'Results({version})')

    # Load all configuration modules for the specified version
    config_modules = load_config_modules(results_folder, version)
    if not config_modules:
        # If no modules are found, log an error and return
        logging.error("No config modules found in results folder")
        return

    # Get properties from the first module to set up the DataFrame
    # This establishes the columns of the table
    first_module_properties = collect_properties_from_config_module(config_modules[0][1])
    column_headers = [prop['Property Name'] for prop in first_module_properties]

    # Create DataFrame with all properties for each year
    # The rows are years from 1 to plant lifetime
    plant_lifetime = config_modules[0][1].get('plantLifetimeAmount10', 0)
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
    save_path = os.path.join(results_folder, f"Variable_Table({version}).csv")
    df.to_csv(save_path, index_label='Year')
    logging.info(f"Table saved successfully to {save_path}")

def main(version):
    """
    Main function to build and save the configuration table.

    This function serves as the entry point for the Table module.
    It calls build_and_save_table and handles any exceptions that occur.

    Args:
        version (str or int): Version number for the configuration

    Returns:
        None: Results are saved to a file

    Raises:
        Exception: Catches and logs any exceptions that occur during processing
    """
    try:
        # Call the main function to build and save the table
        build_and_save_table(version)
    except Exception as e:
        # Log any errors that occur
        logging.error(f"Error in main function: {str(e)}")

# Main Execution Block
# This section is executed when the script is run directly (not imported)
if __name__ == "__main__":
    # Get the version from command line arguments or use default value 1
    version = sys.argv[1] if len(sys.argv) > 1 else 1

    # Call the main function with the specified version
    main(version)
