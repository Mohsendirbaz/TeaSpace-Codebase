import os
import json
import pandas as pd
import sys
import importlib.util
import shutil
import logging
from pathlib import Path

# =====================================================================
# MODULE1 - CONFIGURATION MATRIX BUILDER (Updated for Matrix-Based Form Values)
# =====================================================================
# This module is responsible for building configuration matrices from filtered values.
# It processes configuration data from the matrix-based form values and creates 
# various matrices and data structures used by other modules in the system.
#
# The module handles:
# 1. Processing filtered values from matrix-based configuration files
# 2. Building configuration matrices with intervals and their properties
# 3. Applying property mappings to make IDs more readable
# 4. Saving configuration matrices and related data to CSV files
# 5. Managing the results directory structure
# =====================================================================

# Import using a proper relative import syntax
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Get the directory where this script is located
script_dir = Path(__file__).resolve().parent.parent
uploads_dir = script_dir.parent / "Original"
code_files_path = uploads_dir  # Maintain the same variable name for compatibility

# Initialize logging
log_file_path = Path(os.getcwd()) / 'module1.log'
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s %(message)s')

def apply_property_mapping(filtered_value_intervals):
    """
    Apply human-readable property names to filtered value intervals.

    This function replaces technical property IDs with more readable names
    using the property_mapping dictionary. This makes the output more
    user-friendly and easier to understand.

    Args:
        filtered_value_intervals (list): List of tuples containing filtered value intervals
                                        Each tuple has format (id, start_year, end_year, value, [remarks])

    Returns:
        list: New list of tuples with the ID replaced by its mapped name if available

    Example:
        Input: [("plantLifetimeAmount10", 1, 20, 25)]
        Output: [("Plant Lifetime", 1, 20, 25)]
    """
    mapped_intervals = []
    for interval in filtered_value_intervals:
        interval_id = interval[0]  # Get the ID from the first element of the tuple
        if interval_id in property_mapping:
            # If the ID exists in the mapping, replace it with the mapped name
            interval_list = list(interval)
            interval_list[0] = property_mapping[interval_id]
            mapped_intervals.append(tuple(interval_list))
        else:
            # If the ID doesn't exist in the mapping, keep it as is
            mapped_intervals.append(interval)
    return mapped_intervals

def apply_filtered_values_and_build_matrix(config_received, filtered_values_json):
    """
    Process filtered values and build configuration matrices.

    This function is the core of the configuration matrix building process.
    It takes filtered values from the configuration and builds two types of matrices:
    1. A config_matrix based on the actual start/end points of filtered values
    2. A general_config_matrix based on a continuous range of years

    Args:
        config_received: Configuration object containing plant lifetime and other settings
        filtered_values_json (list): List of JSON strings representing filtered values

    Returns:
        tuple: A tuple containing:
            - config_matrix (list): Matrix based on filtered value intervals
            - sorted_points (list): Sorted list of all start/end points
            - filtered_value_intervals (list): List of tuples with filtered value data
            - general_config_matrix (list): Matrix based on continuous year range
    """
    # Parse the JSON strings into Python objects
    filtered_values = [json.loads(item) for item in filtered_values_json]
    filtered_value_intervals = []  # Will store tuples of (id, start_year, end_year, value, [remarks])
    logging.info(f"filtered_values: {filtered_values}")

    # Initialize the set of start/end points with the minimum (1) and maximum (plant lifetime)
    start_end_points = set()
    start_end_points.update([1, config_received.plantLifetimeAmount10])

    # Create a continuous list of years from 1 to plant lifetime + 1
    # This is used for the general_config_matrix
    general_year_sorted_list = list(range(1, config_received.plantLifetimeAmount10 + 2))
    logging.info(f"general_year_sorted_list: {general_year_sorted_list}")

    # Extract filtered values and their properties
    for value in filtered_values:
        if isinstance(value, dict) and 'filteredValue' in value:
            fv = value['filteredValue']
            # Ensure the filtered value has all required fields
            if 'id' in fv and 'value' in fv and 'start' in fv and 'end' in fv:
                # Convert start and end years to integers
                start_year = int(fv['start'])
                end_year = int(fv['end'])
                # Add these points to the set of start/end points
                start_end_points.update([start_year, end_year])
                logging.info(f"start_end_points: {start_end_points}")

                # Create a tuple with the filtered value data
                # Include remarks if available
                if 'remarks' in fv:
                    filtered_value_intervals.append((fv['id'], start_year, end_year, fv['value'], fv['remarks']))
                else:
                    filtered_value_intervals.append((fv['id'], start_year, end_year, fv['value']))

    # Sort the start/end points to create ordered intervals
    sorted_points = sorted(start_end_points)
    logging.info(f"sorted_points: {sorted_points}")

    # Create intervals from adjacent points
    # For example, if sorted_points is [1, 5, 10], intervals will be [(1, 5), (5, 10)]
    intervals = [(sorted_points[i], sorted_points[i + 1]) for i in range(len(sorted_points) - 1)]

    # Create general intervals from the continuous year list
    general_intervals = [(general_year_sorted_list[i], general_year_sorted_list[i + 1]) for i in range(len(general_year_sorted_list) - 1)]
    logging.info(f"general_intervals: {general_intervals}")
    logging.info(f"intervals: {intervals}")

    # Build the config_matrix from the intervals
    # Each row represents an interval with start, end, length, and filtered values
    config_matrix = []
    for start, end in intervals:
        length = end - start
        config_matrix.append({
            'start': start,
            'end': end,
            'length': length+1,  # +1 because the interval is inclusive
            'filtered_values': []  # Will be populated with filtered values for this interval
        })

    # Build the general_config_matrix from the general intervals
    # This matrix has a row for each year in the plant lifetime
    general_config_matrix = []
    for start, end in general_intervals:
        length = end - start
        general_config_matrix.append({
            'start': start,
            'end': end-1,  # -1 to make the end inclusive
            'length': length,
            'filtered_values': []  # Will be populated with filtered values for this interval
        })

    # Populate the matrices with filtered values
    # For each filtered value, add it to all intervals that overlap with its start/end years
    for fv_tuple in filtered_value_intervals:
        fv_id = fv_tuple[0]
        hs = fv_tuple[1]  # Filtered value start year
        he = fv_tuple[2]  # Filtered value end year
        value = fv_tuple[3]
        remarks = fv_tuple[4] if len(fv_tuple) > 4 else None
        logging.info(f"Processing filtered value: {fv_tuple}")
        
        # Add the filtered value to all intervals in the config_matrix that overlap with it
        for row in config_matrix:
            # Skip if the interval doesn't overlap with the filtered value's period
            if hs > row['end'] or he < row['start']:
                continue
            
            # Create an item for the filtered value and add it to the row
            item = {"id": fv_id, "value": value}
            if remarks:
                item["remarks"] = remarks
            row['filtered_values'].append(item)

        # Add the filtered value to all intervals in the general_config_matrix that overlap with it
        for row in general_config_matrix:
            # Skip if the interval doesn't overlap with the filtered value's period
            if hs > row['end'] or he < row['start']:
                continue
            
            # Create an item for the filtered value and add it to the row
            item = {"id": fv_id, "value": value}
            if remarks:
                item["remarks"] = remarks
            row['filtered_values'].append(item)

    # Convert the filtered_values arrays to JSON strings for storage in CSV
    for row in config_matrix:
        row['filtered_values'] = json.dumps(row['filtered_values'], indent=None)

    for row in general_config_matrix:
        row['filtered_values'] = json.dumps(row['filtered_values'], indent=None)

    # Apply property mapping to make the filtered value intervals more readable
    filtered_value_intervals = apply_property_mapping(filtered_value_intervals)
    
    return config_matrix, sorted_points, filtered_value_intervals, general_config_matrix

def empty_folder(folder_path):
    """
    Empty a folder by deleting all its contents.

    This function removes all files and subdirectories from the specified folder,
    but keeps the folder itself. It's used to clean up the results folder before
    writing new configuration files.

    Args:
        folder_path (str or Path): Path to the folder to be emptied

    Returns:
        None
    """
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = Path(folder_path) / filename
            try:
                if file_path.is_file() or file_path.is_symlink():
                    # Delete files and symbolic links
                    file_path.unlink()
                elif file_path.is_dir():
                    # Delete directories and their contents
                    shutil.rmtree(file_path)
            except Exception as e:
                # Log the error but continue with other files
                print(f"Failed to delete {file_path}. Reason: {e}")

def test_list_building(version, config_received):
    """
    Build and save configuration matrices and related data.

    This function is the main entry point for the configuration matrix building process.
    It processes filtered values from the configuration, builds matrices, and saves
    them to CSV files in the results folder.

    Args:
        version (str or int): Version number for the configuration
        config_received: Configuration object containing filtered values and settings

    Returns:
        None: Results are saved to files
    """
    try:
        # Extract filtered values from the configuration
        filtered_values_json = config_received.filtered_values_json
        logging.info(f"Processing filtered values for version {version}")

        # Build configuration matrices and related data
        config_matrix, sorted_points, filtered_value_intervals, general_config_matrix = apply_filtered_values_and_build_matrix(config_received, filtered_values_json)

        # Prepare the results folder
        results_folder = code_files_path / f"Batch({version})" / f"Results({version})"
        results_folder.mkdir(parents=True, exist_ok=True)  # Create the folder if it doesn't exist

        # Empty the results folder to ensure clean output
        empty_folder(results_folder)

        # Define file paths for the output files
        config_matrix_file = results_folder / f"Configuration_Matrix({version}).csv"
        sorted_points_file = results_folder / f"Sorted_Points({version}).csv"
        filtered_value_intervals_file = results_folder / f"Filtered_Value_Intervals({version}).csv"
        general_config_matrix_file = results_folder / f"General_Configuration_Matrix({version}).csv"

        # Convert the config_matrix to a DataFrame and save it to CSV
        config_matrix_df = pd.DataFrame(config_matrix)
        config_matrix_df.to_csv(config_matrix_file, index=False)
        logging.info(f"Saved configuration matrix to {config_matrix_file}")

        # Convert the general_config_matrix to a DataFrame and save it to CSV
        general_config_matrix_df = pd.DataFrame(general_config_matrix)
        general_config_matrix_df.to_csv(general_config_matrix_file, index=False)
        logging.info(f"Saved general configuration matrix to {general_config_matrix_file}")

        # Convert the sorted_points to a DataFrame and save it to CSV
        sorted_points_df = pd.DataFrame(sorted_points, columns=["Points"])
        sorted_points_df.to_csv(sorted_points_file, index=False)
        logging.info(f"Saved sorted points to {sorted_points_file}")

        # Convert the filtered_value_intervals to a DataFrame and save it to CSV
        filtered_value_intervals_df = pd.DataFrame(filtered_value_intervals, columns=["ID", "Start", "End", "Value", "Remarks"])
        filtered_value_intervals_df.to_csv(filtered_value_intervals_file, index=False)
        logging.info(f"Saved filtered value intervals to {filtered_value_intervals_file}")

        # Print summaries of the generated data for debugging and verification
        print("Config Matrix:")
        print(config_matrix_df)
        print("Sorted Points:")
        print(sorted_points_df)
        print("Filtered Value Intervals:")
        print(filtered_value_intervals_df)
        
        return {
            "message": f"Successfully built configuration matrices for version {version}",
            "files": {
                "config_matrix": str(config_matrix_file),
                "sorted_points": str(sorted_points_file),
                "filtered_value_intervals": str(filtered_value_intervals_file),
                "general_config_matrix": str(general_config_matrix_file)
            }
        }
    except Exception as e:
        error_msg = f"Error building configuration matrices: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}

# Create Flask API handler if this file is used as a server
def create_module1_api():
    """Create a Flask API for the module1 functionality.
    
    Returns:
        Flask app: A Flask application with module1 endpoints
    """
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/module1/<version>', methods=['GET'])
    def run_module1(version):
        """Run module1 for a specific version."""
        try:
            # Path to the configuration file
            config_file = code_files_path / f"Batch({version})" / f"ConfigurationPlotSpec({version})" / f"configurations({version}).py"
            
            # Dynamically import the configuration file
            spec = importlib.util.spec_from_file_location("config", str(config_file))
            config_received = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_received)
            
            # Run the main function
            result = test_list_building(version, config_received)
            return jsonify(result)
        except Exception as e:
            error_msg = f"Error running module1: {str(e)}"
            logging.error(error_msg)
            return jsonify({"error": error_msg})
    
    return app

# Main Execution Block
if __name__ == '__main__':
    # Get the version from command line arguments or use default value 1
    version = sys.argv[1] if len(sys.argv) > 1 else 1

    try:
        # Add the code_files_path to sys.path if it's not already there
        if str(code_files_path) not in sys.path:
            sys.path.append(str(code_files_path))

        # Construct the path to the configuration file for the specified version
        config_file = code_files_path / f"Batch({version})" / f"ConfigurationPlotSpec({version})" / f"configurations({version}).py"

        # Dynamically import the configuration file
        spec = importlib.util.spec_from_file_location("config", str(config_file))
        config_received = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_received)

        # Call the main function with the loaded configuration
        result = test_list_building(version, config_received)
        print(result)
    except Exception as e:
        error_msg = f"Error in main execution: {str(e)}"
        logging.error(error_msg)
        print(error_msg)
    
    # If there are more than 2 arguments and the second one is "server",
    # start the Flask server for API access
    if len(sys.argv) > 2 and sys.argv[2] == "server":
        app = create_module1_api()
        app.run(host='0.0.0.0', port=3051)
