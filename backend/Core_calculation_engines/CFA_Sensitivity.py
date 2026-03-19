#!/usr/bin/env python
"""
Sensitivity-aware Calculation for Financial Analysis (CFA_sensitivity.py)
This version of CFA is designed specifically for sensitivity analysis processing.

Key differences from standard CFA.py:
1. Uses paths compatible with sensitivity analysis directory structure
2. Saves output files to parameter-specific variation directories
3. Properly updates sensitivity parameter JSON with calculated prices
4. Provides structured logging for sensitivity analysis workflow
5. Supports direct command-line sensitivity parameters

Usage:
    python CFA_sensitivity.py <version> <selected_v> <selected_f> <target_row> <calculation_option> --sensitivity <param_id> <variation> <compare_to_key>
"""
import json
import os
import pandas as pd
import numpy as np
import sys
import importlib.util
import logging
import logging.config
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import matplotlib.patches as patches
import seaborn as sns
import itertools
import argparse
import glob
import time

# ---------------- Path Configuration Block Start ----------------
# Determine correct base directories for sensitivity analysis
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_DIR = os.path.join(BASE_DIR, 'backend')
LOGS_DIR = os.path.join(SCRIPT_DIR, 'Logs')
SENSITIVITY_LOG_PATH = os.path.join(LOGS_DIR, "SENSITIVITY_CFA.log")

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# ---------------- Logging Setup Block Start ----------------
# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
)

# Create specific loggers with separate file handlers
sensitivity_logger = logging.getLogger('sensitivity_cfa')
sensitivity_handler = logging.FileHandler(SENSITIVITY_LOG_PATH)
sensitivity_handler.setLevel(logging.INFO)
sensitivity_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
sensitivity_handler.setFormatter(sensitivity_formatter)
sensitivity_logger.addHandler(sensitivity_handler)
sensitivity_logger.setLevel(logging.INFO)
sensitivity_logger.propagate = False  # Prevent propagation to root logger

# Example log usage
sensitivity_logger.info("CFA Sensitivity calculation started.")
# ---------------- Logging Setup Block End ----------------

# ---------------- Helper Functions for Arg Parsing ----------------
def parse_arguments():
    """Parse command-line arguments for sensitivity analysis."""
    parser = argparse.ArgumentParser(description='CFA Sensitivity Analysis')
    parser.add_argument('version', type=int, help='Version number')
    parser.add_argument('selected_v', type=str, help='Selected V parameters (JSON string)')
    parser.add_argument('selected_f', type=str, help='Selected F parameters (JSON string)')
    parser.add_argument('target_row', type=str, help='Target row (JSON string or int)')
    parser.add_argument('calculation_option', type=str, help='Calculation option')

    # Optional sensitivity parameters
    parser.add_argument('--sensitivity', action='store_true', help='Enable sensitivity mode')
    parser.add_argument('param_id', nargs='?', type=str, help='Parameter ID (e.g., S13)')
    parser.add_argument('variation', nargs='?', type=float, help='Variation value')
    parser.add_argument('compare_to_key', nargs='?', type=str, help='Comparison parameter ID')

    # Optional config file path
    parser.add_argument('-c', '--config-file', type=str, help='Path to specific config module file')

    args = parser.parse_args()

    # Parse JSON strings
    try:
        args.selected_v = json.loads(args.selected_v)
    except:
        args.selected_v = {f'V{i+1}': 'off' for i in range(10)}

    try:
        args.selected_f = json.loads(args.selected_f)
    except:
        args.selected_f = {f'F{i+1}': 'off' for i in range(5)}

    try:
        args.target_row = json.loads(args.target_row)
    except:
        try:
            args.target_row = int(args.target_row)
        except:
            args.target_row = 20

    return args

# ---------------- Utility Function Block Start ----------------
def find_sensitivity_directories(version, param_id, variation):
    """
    Find appropriate sensitivity directories for a specific parameter variation.

    Args:
        version (int): Version number
        param_id (str): Parameter ID (e.g., "S35")
        variation (float): Variation value

    Returns:
        tuple: (param_var_dir, sensitivity_dir, results_folder) - Paths to directories
    """
    # Format variation string for directory name
    var_str = f"{variation:+.2f}"

    # Base directories for Original path
    base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
    batch_dir = os.path.join(base_dir, f'Batch({version})')
    results_folder = os.path.join(batch_dir, f'Results({version})')
    sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

    # Search for the parameter directory first
    param_dir = os.path.join(sensitivity_dir, param_id)

    if not os.path.exists(param_dir):
        sensitivity_logger.warning(f"Parameter directory not found: {param_dir}")
        sensitivity_logger.info(f"Creating parameter directory: {param_dir}")
        os.makedirs(param_dir, exist_ok=True)

    # Determine mode based on the directory structure
    mode_dirs = []
    for mode in ['symmetrical', 'multipoint']:
        mode_dir = os.path.join(param_dir, mode)
        if os.path.exists(mode_dir):
            mode_dirs.append((mode, mode_dir))

    if not mode_dirs:
        # Default to symmetrical if no mode directory exists
        default_mode = 'symmetrical'
        default_mode_dir = os.path.join(param_dir, default_mode)
        os.makedirs(default_mode_dir, exist_ok=True)
        mode_dirs = [(default_mode, default_mode_dir)]
        sensitivity_logger.info(f"Created default mode directory: {default_mode_dir}")

    # Use the first found mode
    mode, mode_dir = mode_dirs[0]

    # Create variation directory if it doesn't exist
    var_dir = os.path.join(mode_dir, var_str)
    if not os.path.exists(var_dir):
        os.makedirs(var_dir, exist_ok=True)
        sensitivity_logger.info(f"Created variation directory: {var_dir}")

    return var_dir, sensitivity_dir, results_folder

def update_sensitivity_parameter_price(results_folder, price, param_id=None, variation=None):
    """
    Finds and updates the sensitivity parameter JSON file with the calculated price.
    Silently continues if no appropriate files are found.

    Args:
        results_folder (str): Path to results folder
        price (float): Calculated price to add to JSON
        param_id (str, optional): Parameter ID (e.g., "S35")
        variation (float, optional): Variation value

    Returns:
        bool: True if any files were updated, False otherwise
    """
    try:
        # Construct the sensitivity directory path
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        # If no sensitivity directory exists, continue without error
        if not os.path.exists(sensitivity_dir):
            sensitivity_logger.info(f"No sensitivity directory found at {sensitivity_dir}. Continuing without updating parameters.")
            return False

        # If param_id and variation are provided, update specific param config
        if param_id and variation is not None:
            var_str = f"{variation:+.2f}"
            json_files = []

            # Try different modes
            for mode in ['symmetrical', 'multiple', 'multipoint']:
                param_config_path = os.path.join(
                    sensitivity_dir,
                    param_id,
                    mode,
                    var_str,
                    f"{param_id}_config.json"
                )
                if os.path.exists(param_config_path):
                    json_files.append(param_config_path)

            # If no specific config found, search in sensitivity directory
            if not json_files:
                # Find all related JSON files in the sensitivity directory and its subdirectories
                for root, dirs, files in os.walk(sensitivity_dir):
                    for file in files:
                        if file.endswith('.json') and param_id in file and var_str in root:
                            json_files.append(os.path.join(root, file))
        else:
            # Find all JSON files in the sensitivity directory and its subdirectories
            json_files = []
            for root, dirs, files in os.walk(sensitivity_dir):
                for file in files:
                    if file.endswith('.json') and file.startswith('S'):
                        json_files.append(os.path.join(root, file))

        # If no matching files found, continue without error
        if not json_files:
            sensitivity_logger.info(f"No sensitivity parameter JSON files found in {sensitivity_dir}. Continuing without updating.")
            return False

        # Update each found JSON file with the price
        updated_count = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                # Add or update the price
                data['price'] = price

                with open(json_file, 'w') as f:
                    json.dump(data, f, indent=2)

                updated_count += 1
                sensitivity_logger.info(f"Updated price ${price:.2f} in {json_file}")
            except Exception as e:
                # Log but continue if an individual file update fails
                sensitivity_logger.info(f"Note: Could not update {json_file}: {str(e)}")

        if updated_count > 0:
            sensitivity_logger.info(f"Successfully updated price in {updated_count} sensitivity parameter files.")

        return updated_count > 0

    except Exception as e:
        # Log but continue execution even if the entire function encounters an error
        sensitivity_logger.info(f"Note: Could not update sensitivity parameter prices: {str(e)}")
        return False

# Function to remove existing files
def remove_existing_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        sensitivity_logger.debug(f"Removed existing file: {file_path}")
    else:
        sensitivity_logger.debug(f"No existing file to remove: {file_path}")

def copy_baseline_files(source_folder, target_folder, version, files_to_copy=None):
    """
    Copy baseline calculation files to the sensitivity variation directory.

    Args:
        source_folder (str): Source folder (usually main Results folder)
        target_folder (str): Target folder (parameter variation folder)
        version (int): Version number
        files_to_copy (list, optional): List of file patterns to copy

    Returns:
        int: Number of files copied
    """
    if files_to_copy is None:
        files_to_copy = [
            f"Fixed_Opex_Table_({version}).csv",
            f"Variable_Opex_Table_({version}).csv",
            f"Cumulative_Opex_Table_({version}).csv",
            f"Distance_From_Paying_Taxes({version}).csv",
            f"CFA({version}).csv",
            f"Economic_Summary({version}).csv",
            f"{version}_PieStaticPlots/*.png"
        ]

    copied_count = 0

    for file_pattern in files_to_copy:
        # Handle directory patterns
        if '/' in file_pattern:
            # Extract directory and file pattern
            dir_part, file_part = file_pattern.split('/', 1)
            source_dir = os.path.join(source_folder, dir_part)
            target_dir = os.path.join(target_folder, dir_part)

            # Ensure target directory exists
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            # Find matching files
            if os.path.exists(source_dir):
                for file in glob.glob(os.path.join(source_dir, file_part)):
                    target_file = os.path.join(target_dir, os.path.basename(file))
                    try:
                        import shutil
                        shutil.copy2(file, target_file)
                        copied_count += 1
                        sensitivity_logger.debug(f"Copied file: {file} to {target_file}")
                    except Exception as e:
                        sensitivity_logger.error(f"Error copying file {file}: {str(e)}")
        else:
            # Regular file pattern
            for file in glob.glob(os.path.join(source_folder, file_pattern)):
                target_file = os.path.join(target_folder, os.path.basename(file))
                try:
                    import shutil
                    shutil.copy2(file, target_file)
                    copied_count += 1
                    sensitivity_logger.debug(f"Copied file: {file} to {target_file}")
                except Exception as e:
                    sensitivity_logger.error(f"Error copying file {file}: {str(e)}")

    return copied_count

# ---------------- Utility Function Block End ----------------

# ---------------- Revenue and Expense Calculation Block Start ----------------

# Function to calculate annual revenue
def calculate_annual_revenue(numberOfUnitsAmount12, initialSellingPriceAmount13, generalInflationRateAmount23, years, construction_years):
    revenue = [0] * construction_years + [
        int(numberOfUnitsAmount12 * initialSellingPriceAmount13 * (1 + generalInflationRateAmount23))
        for year in range(construction_years, years)
    ]
    sensitivity_logger.debug(f"Annual Revenue: {revenue}")
    return revenue

def calculate_annual_operating_expenses(
        use_direct_operating_expensesAmount18,
        totalOperatingCostPercentageAmount14,
        variable_costsAmount4,
        amounts_per_unitAmount5,
        MaterialInventory,
        Labor,
        utility,
        maintenance_amount,
        insurance_amount,
        annual_revenue,
        generalInflationRateAmount23,
        years,
        construction_years,
        selected_v,
        selected_f
):


    # List of fixed costs (corresponding to selected_f)
    fixed_costs = [MaterialInventory, Labor, utility, maintenance_amount, insurance_amount]

    # Filter variable costs and amounts per unit based on selected_v
    # If 'off', set corresponding value to 0
    variable_costs_filtered = [
        round(cost * (1 + generalInflationRateAmount23)) if selected_v.get(f'V{i+1}') == 'on' else 0
        for i, cost in enumerate(variable_costsAmount4)
    ]

    amounts_per_unit_filtered = [
        amount if selected_v.get(f'V{i+1}') == 'on' else 0 for i, amount in enumerate(amounts_per_unitAmount5)
    ]

    sensitivity_logger.debug(f"Filtered variable costs: {variable_costs_filtered}")
    sensitivity_logger.debug(f"Filtered amounts per unit: {amounts_per_unit_filtered}")

    # Filter fixed costs based on selected_f
    # If 'off', set corresponding value to 0
    fixed_costs_filtered = [
        round(cost * (1 + generalInflationRateAmount23)) if selected_f.get(f'F{i+1}') == 'on' else 0
        for i, cost in enumerate(fixed_costs)
    ]


    sensitivity_logger.debug(f"Filtered fixed costs: {fixed_costs_filtered}")

    # Calculate total fixed cost
    total_fixed_cost = sum(fixed_costs_filtered)
    sensitivity_logger.debug(f"Total fixed costs: {total_fixed_cost}")

    # If direct operating expenses are used, calculate using total operating cost percentage
    if use_direct_operating_expensesAmount18:

        expenses = [0] * construction_years + [
            int(totalOperatingCostPercentageAmount14 * revenue) for revenue in annual_revenue[construction_years:]
        ]
        sensitivity_logger.debug(f"Operating expenses (direct method): {expenses}")
    else:
        sensitivity_logger.debug("Using indirect calculation for operating expenses.")
        # Calculate total variable costs (filtered based on selected_v)
        annual_variable_cost = np.sum([
            cost * amount for cost, amount in zip(variable_costs_filtered, amounts_per_unit_filtered)
        ])
        sensitivity_logger.debug(f"Annual variable costs: {annual_variable_cost}")

        # Calculate the total expenses over the years, applying inflation after construction years
        expenses = [0] * construction_years + [
            int((annual_variable_cost + total_fixed_cost))
            for year in range(construction_years, years)
        ]
        sensitivity_logger.debug(f"Operating expenses (indirect method): {expenses}")

        # Log the final result
        sensitivity_logger.debug(f"Final operating expenses: {expenses}")
        sensitivity_logger.debug(f"Filtered variable costs returned: {variable_costs_filtered}")
        sensitivity_logger.debug(f"Filtered fixed costs returned: {fixed_costs_filtered}")

    return expenses, variable_costs_filtered, fixed_costs_filtered

# ---------------- Revenue and Expense Calculation Block End ----------------

# ---------------- Opex Table Generation Functions ----------------

# Helper function to pad or trim costs
def pad_or_trim(costs, target_length):
    if len(costs) < target_length:
        return costs + [0] * (target_length - len(costs))
    return costs[:target_length]


# ---------------- OPEX Generation Block (Three Tables) ----------------

def generate_fixed_opex_table(fixed_costs_results, plant_lifetime):
    columns = ['Year', 'F1', 'F2', 'F3', 'F4', 'F5']
    fixed_opex_table = pd.DataFrame(0, index=range(plant_lifetime), columns=columns)
    fixed_opex_table['Year'] = range(1, plant_lifetime + 1)

    for (start_year, end_year), fixed_costs in fixed_costs_results.items():
        fixed_costs = pad_or_trim(fixed_costs, 5)
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                fixed_opex_table.loc[year_idx, 'F1':'F5'] = fixed_costs

    return fixed_opex_table

def generate_variable_opex_table(variable_costs_results, plant_lifetime):
    columns = ['Year', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10']
    variable_opex_table = pd.DataFrame(0, index=range(plant_lifetime), columns=columns)
    variable_opex_table['Year'] = range(1, plant_lifetime + 1)

    for (start_year, end_year), variable_costs in variable_costs_results.items():
        variable_costs = pad_or_trim(variable_costs, 10)
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                variable_opex_table.loc[year_idx, 'V1':'V10'] = variable_costs

    return variable_opex_table

def generate_cumulative_opex_table(fixed_costs_results, variable_costs_results, expenses_results, plant_lifetime):
    columns = ['Year', 'F1', 'F2', 'F3', 'F4', 'F5', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10','Operating Expenses']
    cumulative_opex_table = pd.DataFrame(0, index=range(plant_lifetime), columns=columns)
    cumulative_opex_table['Year'] = range(1, plant_lifetime + 1)

    for (start_year, end_year), fixed_costs in fixed_costs_results.items():
        fixed_costs = pad_or_trim(fixed_costs, 5)
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                cumulative_opex_table.loc[year_idx, 'F1':'F5'] = fixed_costs

    for (start_year, end_year), variable_costs in variable_costs_results.items():
        variable_costs = pad_or_trim(variable_costs, 10)
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                cumulative_opex_table.loc[year_idx, 'V1':'V10'] = variable_costs

    for (start_year, end_year), expenses in expenses_results.items():
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                cumulative_opex_table.loc[year_idx, 'Operating Expenses'] = expenses[year - start_year]

    return cumulative_opex_table

def save_opex_tables(fixed_costs_results, variable_costs_results, expenses_results, plant_lifetime, results_folder,
                     version):
    # Generate the tables
    fixed_opex_table = generate_fixed_opex_table(fixed_costs_results, plant_lifetime)
    variable_opex_table = generate_variable_opex_table(variable_costs_results, plant_lifetime)
    cumulative_opex_table = generate_cumulative_opex_table(fixed_costs_results, variable_costs_results,
                                                           expenses_results, plant_lifetime)

    # Define the file paths
    fixed_opex_path = os.path.join(results_folder, f"Fixed_Opex_Table_({version}).csv")
    variable_opex_path = os.path.join(results_folder, f"Variable_Opex_Table_({version}).csv")
    cumulative_opex_path = os.path.join(results_folder, f"Cumulative_Opex_Table_({version}).csv")

    # Remove existing files if they exist
    remove_existing_file(fixed_opex_path)
    remove_existing_file(variable_opex_path)
    remove_existing_file(cumulative_opex_path)

    # Save the new tables
    fixed_opex_table.to_csv(fixed_opex_path, index=False)
    variable_opex_table.to_csv(variable_opex_path, index=False)
    cumulative_opex_table.to_csv(cumulative_opex_path, index=False)


# Function to calculate state tax
def calculate_state_tax(revenue, stateTaxRateAmount32, operating_expenses, depreciation):
    taxable_income = revenue - operating_expenses - depreciation
    tax = max(taxable_income, 0) * stateTaxRateAmount32

    return tax

# Function to calculate federal tax
def calculate_federal_tax(revenue, federalTaxRateAmount33, operating_expenses, depreciation):
    taxable_income = revenue - operating_expenses - depreciation
    tax = max(taxable_income, 0) * federalTaxRateAmount33

    return tax

# ---------------- Tax Calculation Block End ----------------


# ---------------- Config Module Handling Block Start ----------------

# Function to read the config module from a JSON file
def read_config_module(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# ---------------- Config Module Handling Block End ----------------


# ---------------- Revenue and Expense Calculation from Config Block Start ----------------

def calculate_revenue_and_expenses_from_modules(config_received, config_matrix_df, results_folder, version, selected_v, selected_f, price, target_row, iteration, param_id=None, variation=None):
    sensitivity_logger.info(f"Starting sensitivity calculation for version {version}, parameter {param_id}, variation {variation}")

    # Extract parameters
    plant_lifetime = config_received.plantLifetimeAmount10
    construction_years = config_received.numberofconstructionYearsAmount28

    BEC = config_received.bECAmount11
    EPC = config_received.engineering_Procurement_and_Construction_EPC_Amount15
    PC = config_received.process_contingency_PC_Amount16
    PT = config_received.project_Contingency_PT_BEC_EPC_PCAmount17

    TOC = BEC + EPC * BEC + PC * (BEC + EPC * BEC) + PT * (BEC + EPC * BEC + PC * (BEC + EPC * BEC))

    sensitivity_logger.debug(f"Total Overnight Cost (TOC) calculated: {TOC}")

    CFA_matrix = pd.DataFrame(np.zeros(((plant_lifetime + construction_years), 10)),
                              columns=['Year', 'Revenue', 'Operating Expenses', 'Loan', 'Depreciation', 'State Taxes', 'Federal Taxes', 'After-Tax Cash Flow','Discounted Cash Flow' ,'Cumulative Cash Flow'])
    CFA_matrix['Year'] = range(1, len(CFA_matrix)+1)

    # Complete set for CFA matrix
    revenue_results = {}
    expenses_results = {}
    fixed_costs_results = {}
    variable_costs_results = {}

    # Operational set for OPEX (without construction years)
    revenue_operational = {}
    expenses_operational = {}
    fixed_costs_operational = {}
    variable_costs_operational = {}
    module_selling_price_operational = {}
    # Initialize dictionaries for each cost component
    feedstock_cost_operational = {}
    labor_cost_operational = {}
    utility_cost_operational = {}
    maintenance_cost_operational = {}
    insurance_cost_operational = {}


    interval_units_sold = {}
    total_units_sold = 0
    cumulative_length = 0
    cumulative_total_units_sold = 0
    up_to_year={}
    # Iterate through the config matrix
    for idx, row in config_matrix_df.iterrows():
        start_year = int(row['start']) + construction_years
        end_year = int(row['end']) + construction_years
        length = int(row['end']) - int(row['start']) + 1
        cumulative_length += length
        sensitivity_logger.debug(f"cumulative_length: {cumulative_length}")
        config_module_file = os.path.join(results_folder, f"{version}_config_module_{row['start']}.json")
        if not os.path.exists(config_module_file):
            sensitivity_logger.warning(f"Config module file not found: {config_module_file}")
            continue

        config_module = read_config_module(config_module_file)
        if int(row['start'])+1> target_row:
            # Use the initial selling price if the period is after the target row
            annual_revenue = calculate_annual_revenue(
                config_module['numberOfUnitsAmount12'],
                config_module['initialSellingPriceAmount13'],
                config_module['generalInflationRateAmount23'],
                plant_lifetime + construction_years,
                construction_years
            )
        else:
            # Use the calculated price if the period is before the target row
            annual_revenue = calculate_annual_revenue(
                config_module['numberOfUnitsAmount12'],
                price,  # Assuming 'price' has been defined earlier in your script as a dynamic value
                config_module['generalInflationRateAmount23'],
                plant_lifetime + construction_years,
                construction_years
            )
        sensitivity_logger.debug(f"Annual Revenue calculated: {annual_revenue}")
        annual_operating_expenses, variable_costs, fixed_costs = calculate_annual_operating_expenses(
            config_module['use_direct_operating_expensesAmount18'],
            config_module['totalOperatingCostPercentageAmount14'],
            config_module['variable_costsAmount4'],
            config_module['amounts_per_unitAmount5'],
            config_module['rawmaterialAmount34'],
            config_module['laborAmount35'],
            config_module['utilityAmount36'],
            config_module['maintenanceAmount37'],
            config_module['insuranceAmount38'],
            annual_revenue,
            config_module['generalInflationRateAmount23'],
            plant_lifetime + construction_years,
            construction_years,
            selected_v,
            selected_f
        )

        adjusted_length_calculation = length

        up_to_year[idx]=adjusted_length_calculation
        interval_units_sold[idx]=config_module['numberOfUnitsAmount12']* adjusted_length_calculation




        # Store individual cost components for each row
        # Assign fixed costs to respective operations
        feedstock_cost_operational[idx] = fixed_costs[0] * adjusted_length_calculation
        labor_cost_operational[idx] = fixed_costs[1] * adjusted_length_calculation
        utility_cost_operational[idx] = fixed_costs[2] * adjusted_length_calculation
        maintenance_cost_operational[idx] = fixed_costs[3] * adjusted_length_calculation
        insurance_cost_operational[idx] = fixed_costs[4] * adjusted_length_calculation

        if int(row['start'])+1> target_row:
            # Store module selling price for each row
            module_selling_price_operational[idx] = config_module['initialSellingPriceAmount13'] * adjusted_length_calculation
        else:
            module_selling_price_operational[idx] = price * adjusted_length_calculation

        # Store for CFA
        revenue_results[(start_year, end_year)] = annual_revenue
        expenses_results[(start_year, end_year)] = annual_operating_expenses
        fixed_costs_results[(start_year, end_year)] = fixed_costs
        variable_costs_results[(start_year, end_year)] = variable_costs

        # Store for OPEX
        operational_start_year = int(row['start'])
        operational_end_year = int(row['end'])

        revenue_operational[(operational_start_year, operational_end_year)] = annual_revenue[construction_years:]
        expenses_operational[(operational_start_year, operational_end_year)] = annual_operating_expenses[construction_years:]
        fixed_costs_operational[(operational_start_year, operational_end_year)] = fixed_costs
        variable_costs_operational[(operational_start_year, operational_end_year)] = variable_costs

        # Calculate average values for each cost component operational
        average_feedstock_cost_operational = sum(feedstock_cost_operational.values()) / sum(up_to_year.values())
        average_labor_cost_operational = sum(labor_cost_operational.values()) / sum(up_to_year.values())
        average_utility_cost_operational = sum(utility_cost_operational.values()) / sum(up_to_year.values())
        average_maintenance_cost_operational = sum(maintenance_cost_operational.values()) / sum(up_to_year.values())
        average_insurance_cost_operational = sum(insurance_cost_operational.values()) / sum(up_to_year.values())

        total_units_sold = sum(interval_units_sold.values())*plant_lifetime/(plant_lifetime-1)
        sensitivity_logger.info(f"total units sold: {total_units_sold}")


        # Check if cumulative length has reached or exceeded the target
        if cumulative_length >= target_row and cumulative_length <= target_row+1:
            cumulative_total_units_sold+= interval_units_sold[idx]
            cumulative_total_units_sold_npv= cumulative_total_units_sold
        else:
            continue

    # Save OPEX tables
    save_opex_tables(fixed_costs_operational, variable_costs_operational, expenses_operational, plant_lifetime, results_folder, version)

    # Populate CFA matrix
    for idx, row in config_matrix_df.iterrows():
        start_year = int(row['start']) + construction_years
        end_year = int(row['end']) + construction_years

        annual_revenue = revenue_results.get((start_year, end_year), [])
        annual_operating_expenses = expenses_results.get((start_year, end_year), [])

        for year in range(start_year, end_year + 1):
            cfa_year = year
            if year < len(annual_revenue):
                CFA_matrix.at[cfa_year, 'Revenue'] = annual_revenue[year]
            if year < len(annual_operating_expenses):
                CFA_matrix.at[cfa_year, 'Operating Expenses'] = annual_operating_expenses[year]

    # Save CFA matrix
    CFA_matrix_file = os.path.join(results_folder, f"CFA({version}).csv")
    remove_existing_file(CFA_matrix_file)
    CFA_matrix.to_csv(CFA_matrix_file, index=False)



    # Second loop to place results in the correct places in the CFA matrix
    for idx, row in config_matrix_df.iterrows():
        start_year = int(row['start']) + construction_years
        end_year = int(row['end']) + construction_years
        length = int(row['length'])

        # Get the results for the current interval
        annual_revenue = revenue_results.get((start_year, end_year), [])

        annual_operating_expenses = expenses_results.get((start_year, end_year), [])

        # Update the CFA matrix with annual revenue and expenses
        for year in range(start_year, end_year + 1):
            cfa_year = year-1

            if year < len(annual_revenue):

                CFA_matrix.at[cfa_year, 'Revenue'] = annual_revenue[year]

            if year < len(annual_operating_expenses):
                CFA_matrix.at[cfa_year, 'Operating Expenses'] = annual_operating_expenses[year]

    # ---------------- Construction Year Handling Block Start ----------------

    # Populate the CFA matrix for construction years
    cumulative_cash_flow = 0
    for year in range(construction_years):
        operating_expenses = -TOC / construction_years
        CFA_matrix.loc[year, 'Operating Expenses'] = operating_expenses
        CFA_matrix.loc[year, 'Cumulative Cash Flow'] = cumulative_cash_flow + operating_expenses
        cumulative_cash_flow += operating_expenses

    # ---------------- Construction Year Handling Block End ----------------


    # ---------------- Tax Exemption and Depreciation Calculation Block Start ----------------

    # Create a matrix for distance from paying taxes
    distance_matrix = pd.DataFrame(0, index=range(len(CFA_matrix)), columns=['Potentially Taxable Income', 'Fraction of TOC'])

    # Calculate the difference (revenue - operating expenses) and (revenue - operating expenses)/TOC
    for i in range(construction_years, len(CFA_matrix)):
        revenue = CFA_matrix.at[i, 'Revenue']
        operating_expenses = CFA_matrix.at[i, 'Operating Expenses']
        distance_matrix.at[i, 'Potentially Taxable Income'] = revenue - operating_expenses
        distance_matrix.at[i, 'Fraction of TOC'] = round((revenue - operating_expenses) / TOC, 9)

    # Save the distance matrix
    distance_matrix_file = os.path.join(results_folder, f"Distance_From_Paying_Taxes({version}).csv")
    remove_existing_file(distance_matrix_file)  # Remove if the file already exists
    distance_matrix.to_csv(distance_matrix_file, index=False)


    # Calculate the sum of the fraction of TOC (sigma)
    sigma = distance_matrix['Fraction of TOC'].sum()

    # Determine the depreciation period based on sigma
    depreciation_end_year = None
    cumulative_fraction = 0
    for i in range(construction_years, len(CFA_matrix)):
        cumulative_fraction += distance_matrix.at[i, 'Fraction of TOC']
        if cumulative_fraction > 1:
            depreciation_end_year = i
            break

    # Populate depreciation in the CFA matrix
    if depreciation_end_year:
        for year in range(construction_years, depreciation_end_year):
            depreciation_value = int(distance_matrix.at[year, 'Fraction of TOC'] * TOC)
            CFA_matrix.at[year, 'Depreciation'] = depreciation_value
            sensitivity_logger.info("Finished CFA calculation")
        remaining_toc = int(TOC - CFA_matrix['Depreciation'].sum())
        CFA_matrix.at[depreciation_end_year, 'Depreciation'] = remaining_toc


    # ---------------- Tax Calculation and After-Tax Cash Flow Block Start ----------------

    # Calculate and populate state and federal taxes in the CFA matrix
    for year in range(construction_years, plant_lifetime + construction_years):
        revenue = CFA_matrix.at[year, 'Revenue']
        operating_expenses = CFA_matrix.at[year, 'Operating Expenses']
        depreciation = CFA_matrix.at[year, 'Depreciation']

        state_tax = calculate_state_tax(revenue, config_received.stateTaxRateAmount32, operating_expenses, depreciation)
        federal_tax = calculate_federal_tax(revenue, config_received.federalTaxRateAmount33, operating_expenses, depreciation)

        CFA_matrix.at[year, 'State Taxes'] = state_tax
        CFA_matrix.at[year, 'Federal Taxes'] = federal_tax

        after_tax_cash_flow = revenue - operating_expenses - state_tax - federal_tax
        CFA_matrix.at[year, 'After-Tax Cash Flow'] = after_tax_cash_flow
        Discounted_cash_flow = after_tax_cash_flow/(1 + config_received.iRRAmount30)
        CFA_matrix.at[year, 'Discounted Cash Flow'] = Discounted_cash_flow

        cumulative_cash_flow += Discounted_cash_flow
        CFA_matrix.at[year, 'Cumulative Cash Flow'] = cumulative_cash_flow


    CFA_matrix = CFA_matrix.astype(int)

    # ---------------- CFA Matrix Saving Block Start ----------------

    CFA_matrix_file = os.path.join(results_folder, f"CFA({version}).csv")
    remove_existing_file(CFA_matrix_file)
    CFA_matrix.to_csv(CFA_matrix_file, index=False)


    # ---------------- Economic Summary and Plotting Block Start ----------------

    # Calculate economic summary
    operational_years = plant_lifetime

    total_revenue = CFA_matrix.loc[construction_years:, 'Revenue'].sum()
    total_operating_expenses = CFA_matrix.loc[construction_years:, 'Operating Expenses'].sum()
    total_depreciation = CFA_matrix.loc[construction_years:, 'Depreciation'].sum()
    total_state_taxes = CFA_matrix.loc[construction_years:, 'State Taxes'].sum()
    total_federal_taxes = CFA_matrix.loc[construction_years:, 'Federal Taxes'].sum()
    total_after_tax_cash_flow = CFA_matrix.loc[construction_years:, 'After-Tax Cash Flow'].sum()
    total_discounted_cash_flow = CFA_matrix.loc[construction_years:, 'Discounted Cash Flow'].sum()
    average_selling_price_operational=total_revenue/ total_units_sold
    cumulative_npv = CFA_matrix.loc[construction_years:, 'Cumulative Cash Flow'].iloc[-1]
    sensitivity_logger.info(f"total_units_sold: {total_units_sold}")
    average_annual_revenue = total_revenue / operational_years
    average_annual_operating_expenses = total_operating_expenses / operational_years
    average_annual_depreciation = total_depreciation / operational_years
    average_annual_state_taxes = total_state_taxes / operational_years
    average_annual_federal_taxes = total_federal_taxes / operational_years
    average_annual_discounted_cash_flow = total_discounted_cash_flow / operational_years
    average_annual_after_tax_cash_flow = total_after_tax_cash_flow / operational_years

    economic_summary = pd.DataFrame({
        'Metric': [
            'Internal Rate of Return',
            'Average Selling Price (Project Life Cycle)',
            'Total Overnight Cost (TOC)',
            'Average Annual Revenue',
            'Average Annual Operating Expenses',
            'Average Annual Depreciation',
            'Average Annual State Taxes',
            'Average Annual Federal Taxes',
            'Average Annual After-Tax Cash Flow',
            'Cumulative NPV',
            'Calculation Mode',
            'Sensitivity Parameter',
            'Variation'
        ],
        'Value': [
            f"{config_received.iRRAmount30:.2%}",
            f"${average_selling_price_operational:,.2f}",
            f"${TOC:,.0f}",
            f"${average_annual_revenue:,.0f}",
            f"${average_annual_operating_expenses:,.0f}",
            f"${average_annual_depreciation:,.0f}",
            f"${average_annual_state_taxes:,.0f}",
            f"${average_annual_federal_taxes:,.0f}",
            f"${average_annual_after_tax_cash_flow:,.0f}",
            f"${cumulative_npv:,.0f}",
            f"{sys.argv[5]}",
            f"{param_id if param_id else 'None'}",
            f"{variation if variation is not None else 'None'}"
        ]
    })

    economic_summary_file = os.path.join(results_folder, f"Economic_Summary({version}).csv")
    remove_existing_file(economic_summary_file)  # Remove if the file already exists
    economic_summary.to_csv(economic_summary_file, index=False)


    # Generate and save the pie chart for relative magnitudes using Plotly
    labels = [
        'Annual Revenue',
        'Annual Operating Expenses',
        'Annual State Taxes',
        'Annual Federal Taxes'
    ]
    sizes = [
        average_annual_revenue,
        average_annual_operating_expenses,
        average_annual_state_taxes,
        average_annual_federal_taxes
    ]

    # Update any sensitivity parameter JSON files with the calculated price
    if param_id and variation is not None:
        update_sensitivity_parameter_price(results_folder, average_selling_price_operational, param_id, variation)
    else:
        update_sensitivity_parameter_price(results_folder, average_selling_price_operational)

    # Define labels and sizes for the operational cost breakdown
    operational_labels = [
        'Feedstock Cost',
        'Labor Cost',
        'Utility Cost',
        'Maintenance Cost',
        'Insurance Cost'
    ]
    operational_sizes = [
        average_feedstock_cost_operational,
        average_labor_cost_operational,
        average_utility_cost_operational,
        average_maintenance_cost_operational,
        average_insurance_cost_operational
    ]

    # Example list of fonts to choose from
    available_fonts = ['Arial', 'Verdana', 'Helvetica', 'Times New Roman', 'Courier New', 'Georgia']

    # Selected fonts
    chosen_title_font = 'Georgia'
    chosen_label_font = 'Georgia'
    chosen_numbers_font = 'Georgia'

    # Filter labels and sizes based on the 'on' or 'off' status in selected_f
    filtered_labels = [
        label for i, label in enumerate(operational_labels) if selected_f.get(f'F{i+1}') == 'on'
    ]
    filtered_sizes = [
        size for i, size in enumerate(operational_sizes) if selected_f.get(f'F{i+1}') == 'on'
    ]

    # Generate the pie chart
    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)

    def autopct_filter(pct):
        """Show percentage only if >= 3%."""
        return f'{pct:.1f}%' if pct >= 3 else ''

    wedges, texts, autotexts = ax.pie(
        filtered_sizes,
        labels=None,  # Labels will be added with arrows
        autopct=autopct_filter,
        startangle=45,
        explode=[0.02] * len(filtered_labels),  # Slight explosion
        wedgeprops={'linewidth': 0.5, 'edgecolor': 'grey'},
        radius=0.7  # Smaller pie radius
    )

    # Add parameter and variation info to title if available
    title_text = 'Operational Cost Breakdown'
    if param_id and variation is not None:
        title_text += f' - {param_id} [{variation:+.2f}%]'

    # Set title with chosen font
    ax.set_title(title_text, fontsize=14, fontname=chosen_title_font, pad=25)

    # Annotate labels with arrows pointing outward, using chosen fonts
    for i, (wedge, label) in enumerate(zip(wedges, filtered_labels)):
        angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
        x, y = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))

        ax.annotate(
            f'{label}\n${filtered_sizes[i]:,.0f}',  # Dollar sign, comma formatting, no decimals
            xy=(x * 0.7, y * 0.7),
            xytext=(x * 1.2, y * 1.2),
            arrowprops=dict(facecolor='black', arrowstyle='->', lw=0.7),
            fontsize=10, ha='center', fontname=chosen_label_font  # Set font for labels
        )

    # Set font for the numbers in the pie chart (autotexts)
    for autotext in autotexts:
        autotext.set_fontname(chosen_numbers_font)
        autotext.set_fontsize(10)

    # Set background color and adjust layout
    ax.set_facecolor('#f7f7f7')
    plt.tight_layout()

    # Save the chart as PNG
    static_plot=os.path.join(results_folder, f'{version}_PieStaticPlots')
    os.makedirs(static_plot, exist_ok=True)

    # Include parameter ID and variation in filename if provided
    filename_suffix = ""
    if param_id and variation is not None:
        filename_suffix = f"_{param_id}_{variation:+.2f}"

    png_path = os.path.join(static_plot, f"Operational_Cost_Breakdown_Pie_Chart({version}){filename_suffix}.png")
    plt.savefig(png_path, bbox_inches='tight', dpi=300)
    plt.close()

    # ---------------- Economic Summary and Plotting Block End ----------------

    # ---------------- Price Finding Block Start ----------------
    NPV_year = target_row # Set the NPV year to the target row (user specified) plus construction years (cfa table compatibility)
    npv = CFA_matrix.at[NPV_year, 'Cumulative Cash Flow']
    iteration += 1  # Increment the iteration counter

    sensitivity_logger.info(f"Calculated Current NPV: {npv:.2f} from row {NPV_year}")
    sensitivity_logger.info(f"'primary_result': {npv},'secondary_result': {iteration}")
    # ---------------- Price Finding Block End ----------------

    # Log completion message
    if param_id and variation is not None:
        sensitivity_logger.info(f"Completed sensitivity calculation for parameter {param_id}, variation {variation}%")
        sensitivity_logger.info(f"Final average selling price: ${average_selling_price_operational:.2f}")

    return {
        'primary_result': npv,
        'secondary_result': iteration,
        'price': average_selling_price_operational,
        'param_id': param_id,
        'variation': variation
    }  # Return the calculated NPV, iteration count, and price


# ---------------- Main Function Block Start ----------------

# Main function to load config matrix and run the update
def main():
    # Parse command-line arguments
    args = parse_arguments()
    version = args.version
    selected_v = args.selected_v
    selected_f = args.selected_f
    target_row = args.target_row
    calculation_option = args.calculation_option

    sensitivity_logger.info(f"Starting CFA sensitivity calculation process")
    sensitivity_logger.info(f"Version: {version}")
    sensitivity_logger.info(f"Target row: {target_row}")
    sensitivity_logger.info(f"Calculation option: {calculation_option}")

    # Check if this is a sensitivity run
    is_sensitivity_run = args.sensitivity
    param_id = args.param_id if is_sensitivity_run else None
    variation = args.variation if is_sensitivity_run else None
    compare_to_key = args.compare_to_key if is_sensitivity_run else None

    if is_sensitivity_run:
        sensitivity_logger.info(f"Running in sensitivity mode")
        sensitivity_logger.info(f"Parameter: {param_id}")
        sensitivity_logger.info(f"Variation: {variation}")
        sensitivity_logger.info(f"Compare to: {compare_to_key}")

    # Determine the results folder based on whether this is a sensitivity run
    if is_sensitivity_run and param_id and variation is not None:
        # For sensitivity runs, find the appropriate variation directory
        param_var_dir, sensitivity_dir, base_results_folder = find_sensitivity_directories(
            version, param_id, variation
        )
        results_folder = param_var_dir
        sensitivity_logger.info(f"Using sensitivity variation directory: {results_folder}")
    else:
        # For standard runs, use the main results directory
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        base_results_folder = os.path.join(base_dir, f"Batch({version})", f"Results({version})")
        results_folder = base_results_folder
        sensitivity_logger.info(f"Using standard results directory: {results_folder}")

    # If a specific config file is provided, use it
    if args.config_file and os.path.exists(args.config_file):
        config_matrix_file = os.path.dirname(args.config_file)
        sensitivity_logger.info(f"Using specific config file: {args.config_file}")
    else:
        # Find or create the config matrix file
        config_matrix_file = os.path.join(results_folder, f"General_Configuration_Matrix({version}).csv")

        # If the matrix file doesn't exist in the sensitivity directory, copy it from the main results
        if not os.path.exists(config_matrix_file) and is_sensitivity_run:
            base_config_matrix_file = os.path.join(base_results_folder, f"General_Configuration_Matrix({version}).csv")

            if os.path.exists(base_config_matrix_file):
                os.makedirs(os.path.dirname(config_matrix_file), exist_ok=True)
                import shutil
                shutil.copy2(base_config_matrix_file, config_matrix_file)
                sensitivity_logger.info(f"Copied config matrix from: {base_config_matrix_file} to {config_matrix_file}")

        # If still not found, look for Configuration_Matrix
        if not os.path.exists(config_matrix_file):
            alt_config_matrix_file = os.path.join(results_folder, f"Configuration_Matrix({version}).csv")
            if os.path.exists(alt_config_matrix_file):
                config_matrix_file = alt_config_matrix_file
                sensitivity_logger.info(f"Using alternative config matrix: {config_matrix_file}")
            else:
                # Copy from base results folder if available
                base_alt_config_matrix_file = os.path.join(base_results_folder, f"Configuration_Matrix({version}).csv")
                if os.path.exists(base_alt_config_matrix_file):
                    os.makedirs(os.path.dirname(config_matrix_file), exist_ok=True)
                    import shutil
                    shutil.copy2(base_alt_config_matrix_file, config_matrix_file)
                    sensitivity_logger.info(f"Copied alt config matrix from: {base_alt_config_matrix_file} to {config_matrix_file}")

    # Ensure the matrix file exists
    if not os.path.exists(config_matrix_file):
        sensitivity_logger.error(f"Config matrix file not found at: {config_matrix_file}")
        sys.exit(1)

    # Load the config matrix
    config_matrix_df = pd.read_csv(config_matrix_file)
    sensitivity_logger.info(f"Loaded config matrix with {len(config_matrix_df)} rows")

    # Load main configuration file or use config module from specific file
    if args.config_file and os.path.exists(args.config_file):
        config_received = importlib.util.module_from_spec(importlib.util.spec_from_file_location("config", args.config_file))
        sensitivity_logger.info(f"Loaded configuration from specific file: {args.config_file}")
    else:
        # Try to find the standard configuration file
        config_file_paths = [
            # In Sensitivity variation dir/ConfigurationPlotSpec
            os.path.join(results_folder, f"ConfigurationPlotSpec({version})", f"configurations({version}).py"),
            # In base results/ConfigurationPlotSpec
            os.path.join(base_results_folder, f"ConfigurationPlotSpec({version})", f"configurations({version}).py"),
            # In Original/Batch/ConfigurationPlotSpec
            os.path.join(BASE_DIR, 'backend', 'Original', f"Batch({version})", f"ConfigurationPlotSpec({version})", f"configurations({version}).py"),
            # In Original/ConfigurationPlotSpec
            os.path.join(BASE_DIR, 'backend', 'Original', f"ConfigurationPlotSpec({version})", f"configurations({version}).py")
        ]

        config_file = None
        for cf_path in config_file_paths:
            if os.path.exists(cf_path):
                config_file = cf_path
                sensitivity_logger.info(f"Found configuration file at: {config_file}")
                break

        if not config_file:
            sensitivity_logger.error(f"Configuration file not found. Tried paths: {config_file_paths}")
            sys.exit(1)

        # Load the configuration file
        spec = importlib.util.spec_from_file_location("config", config_file)
        config_received = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_received)

    # Initialize iteration counter
    iteration = 0

    # Initial price and NPV calculation
    price = config_received.initialSellingPriceAmount13
    results = calculate_revenue_and_expenses_from_modules(
        config_received,
        config_matrix_df,
        results_folder,
        version,
        selected_v,
        selected_f,
        price,
        target_row,
        iteration,
        param_id,
        variation
    )

    # Extract results
    npv = results['primary_result']
    iteration = results['secondary_result']
    price = results['price']
    sensitivity_logger.info(f"Final NPV: ${npv:.2f}, Iteration: {iteration}, Price: ${price:.2f}")

    # For sensitivity runs, we need to ensure we have all necessary files in the variation directory
    if is_sensitivity_run and param_id and variation is not None:
        # Copy any missing baseline files to the variation directory
        num_copied = copy_baseline_files(base_results_folder, results_folder, version)
        if num_copied > 0:
            sensitivity_logger.info(f"Copied {num_copied} baseline files to variation directory")

        # Create a result JSON file for the process_sensitivity_results.py script to find
        result_file_path = os.path.join(os.path.dirname(results_folder), f"{param_id}_variation_result.json")
        with open(result_file_path, 'w') as f:
            json.dump({
                'param_id': param_id,
                'variation': variation,
                'compare_to_key': compare_to_key,
                'price': price,
                'npv': float(npv),
                'iteration': iteration,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        sensitivity_logger.info(f"Saved variation result to: {result_file_path}")

    sensitivity_logger.info("CFA sensitivity calculation process completed successfully")
    return price, npv

# Ensure script runs as expected when invoked
if __name__ == "__main__":
    main()
