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
# ---------------- Logging Setup Block Start ----------------
import sys
print(sys.executable)
print(sys.path)
# Determine the directory for log files
log_directory = os.getcwd()
# Define the log file paths
price_optimization_log = os.path.join(log_directory, 'price_optimization.log')



# Set up paths for log files
log_directory = os.getcwd()
price_optimization_log = os.path.join(log_directory, 'price_optimization.log')
app_cfa_log = os.path.join(log_directory, 'app_CFA.log')

# Ensure the log directory exists
os.makedirs(log_directory, exist_ok=True)

# Basic logger setup for price optimization and CFA
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO for both loggers
    format='%(asctime)s - %(message)s',
)

# Create specific loggers with separate file handlers
price_logger = logging.getLogger('price_optimization')
price_handler = logging.FileHandler(price_optimization_log)
price_handler.setLevel(logging.INFO)
price_logger.addHandler(price_handler)

cfa_logger = logging.getLogger('app_cfa')
cfa_handler = logging.FileHandler(app_cfa_log)
cfa_handler.setLevel(logging.INFO)
cfa_logger.addHandler(cfa_handler)

# Example log usage
price_logger.info("Price optimization started.")
cfa_logger.info("CFA process initiated.")

# ---------------- cfa_logger Setup Block End ----------------

# ---------------- Logging Setup Block End ----------------


# ---------------- Utility Function Block Start ----------------

# Function to remove existing files
def remove_existing_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.debug(f"Removed existing file: {file_path}")
    else:
        logging.debug(f"No existing file to remove: {file_path}")

# ---------------- Utility Function Block End ----------------


# ---------------- Revenue and Expense Calculation Block Start ----------------

# Function to calculate annual revenue
def calculate_annual_revenue(numberOfUnitsAmount12, initialSellingPriceAmount13, generalInflationRateAmount23, years, construction_years):
    revenue = [0] * construction_years + [
        int(numberOfUnitsAmount12 * initialSellingPriceAmount13 * (1 + generalInflationRateAmount23) )
        for year in range(construction_years, years)
    ]
    logging.debug(f"Annual Revenue: {revenue}")
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

    logging.info(f"Filtered variable costs: {variable_costs_filtered}")
    logging.info(f"Filtered amounts per unit: {amounts_per_unit_filtered}")

    # Filter fixed costs based on selected_f
    # If 'off', set corresponding value to 0
    fixed_costs_filtered = [
        round(cost * (1 + generalInflationRateAmount23)) if selected_f.get(f'F{i+1}') == 'on' else 0
        for i, cost in enumerate(fixed_costs)
    ]


    logging.info(f"Filtered fixed costs: {fixed_costs_filtered}")

    # Calculate total fixed cost
    total_fixed_cost = sum(fixed_costs_filtered)
    logging.info(f"Total fixed costs: {total_fixed_cost}")

    # If direct operating expenses are used, calculate using total operating cost percentage
    if use_direct_operating_expensesAmount18:

        expenses = [0] * construction_years + [
            int(totalOperatingCostPercentageAmount14 * revenue) for revenue in annual_revenue[construction_years:]
        ]
        logging.info(f"Operating expenses (direct method): {expenses}")
    else:
        logging.info("Using indirect calculation for operating expenses.")
        # Calculate total variable costs (filtered based on selected_v)
        annual_variable_cost = np.sum([
            cost * amount for cost, amount in zip(variable_costs_filtered, amounts_per_unit_filtered)
        ])
        logging.info(f"Annual variable costs: {annual_variable_cost}")

        # Calculate the total expenses over the years, applying inflation after construction years
        expenses = [0] * construction_years + [
            int((annual_variable_cost + total_fixed_cost))
            for year in range(construction_years, years)
        ]
        logging.info(f"Operating expenses (indirect method): {expenses}")

        # Log the final result
        logging.info(f"Final operating expenses: {expenses}")
        logging.info(f"Filtered variable costs returned: {variable_costs_filtered}")
        logging.info(f"Filtered fixed costs returned: {fixed_costs_filtered}")

    return expenses, variable_costs_filtered, fixed_costs_filtered



# ---------------- Revenue and Expense Calculation Block End ----------------import pandas as pd

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

def calculate_revenue_and_expenses_from_modules(config_received, config_matrix_df, results_folder, version, selected_v, selected_f, price, target_row, iteration):


    # Extract parameters
    plant_lifetime = config_received.plantLifetimeAmount10
    construction_years = config_received.numberofconstructionYearsAmount28

    BEC = config_received.bECAmount11
    EPC = config_received.engineering_Procurement_and_Construction_EPC_Amount15
    PC = config_received.process_contingency_PC_Amount16
    PT = config_received.project_Contingency_PT_BEC_EPC_PCAmount17

    TOC = BEC + EPC * BEC + PC * (BEC + EPC * BEC) + PT * (BEC + EPC * BEC + PC * (BEC + EPC * BEC))

    logging.debug(f"Total Overnight Cost (TOC) calculated: {TOC}")

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
        logging.debug(f"cumulative_length: {cumulative_length}")
        config_module_file = os.path.join(results_folder, f"{version}_config_module_{row['start']}.json")
        if not os.path.exists(config_module_file):
            logging.warning(f"Config module file not found: {config_module_file}")
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
        logging.debug(f"Annual Revenue calculated: {annual_revenue}")
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
        cfa_logger.info(f"total units sold: {total_units_sold}")


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
            logging.info("Finished CFA calculation")
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
    cfa_logger.info(f"total_units_sold: {total_units_sold}")
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
            'Calculation Mode'
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
            f"{sys.argv[5]}"

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




    # ---------------- Economic Summary and Plotting Block End ----------------

    # Define labels and corresponding average operational costs
    labels = [
        'Feedstock Cost',
        'Labor Cost',
        'Utility Cost',
        'Maintenance Cost',
        'Insurance Cost'
    ]
    sizes = [
        average_feedstock_cost_operational,
        average_labor_cost_operational,
        average_utility_cost_operational,
        average_maintenance_cost_operational,
        average_insurance_cost_operational
    ]




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

    # Set title with chosen font
    ax.set_title('Operational Cost Breakdown', fontsize=14, fontname=chosen_title_font, pad=25)

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

    png_path = os.path.join(static_plot, f"Operational_Cost_Breakdown_Pie_Chart({version}).png")
    plt.savefig(png_path, bbox_inches='tight', dpi=300)
    plt.close()

    # ---------------- Economic Summary and Plotting Block End ----------------



    # ---------------- Economic Summary and Plotting Block End ----------------

    # ---------------- Price Finding Block Start ----------------
    NPV_year=target_row # Set the NPV year to the target row (user specified) plus construction years (cfa table compatibility)
    npv=CFA_matrix.at[NPV_year, 'Cumulative Cash Flow']
    iteration+=1  # Increment the iteration counter

    price_logger.info(f"Calculated Current NPV: {npv:.2f} from row {NPV_year}")
    price_logger.info(f"'primary_result': {npv},'secondary_result': {iteration}")
    # ---------------- Price Finding Block End ----------------
    return {
        'primary_result': npv,
        'secondary_result': iteration,
    }  # Return the calculated NPV and iteration count


# ---------------- Main Function Block Start ----------------

# Main function to load config matrix and run the update
def main(version, selected_v, selected_f, target_row):
    # Set up paths for modules and results
    code_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Original")

    results_folder = os.path.join(code_files_path, f"Batch({version})", f"Results({version})")
    config_matrix_file = os.path.join(results_folder, f"General_Configuration_Matrix({version}).csv")

    # Load the config matrix
    config_matrix_df = pd.read_csv(config_matrix_file)

    # Load configuration file
    config_file = os.path.join(code_files_path, f"Batch({version})", f"ConfigurationPlotSpec({version})", f"configurations({version}).py")
    spec = importlib.util.spec_from_file_location("config", config_file)
    config_received = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_received)
    iteration = 0
    # Initial price and NPV calculation
    price = config_received.initialSellingPriceAmount13
    results = calculate_revenue_and_expenses_from_modules(config_received, config_matrix_df, results_folder, version, selected_v, selected_f, price, target_row, iteration)
    npv = results['primary_result']
    iteration = results['secondary_result']
    price_logger.info(f"Initial NPV: ${npv:.2f}, Iteration: {iteration}")

    # Define convergence tolerance
    TOLERANCE_LOWER = -1000
    TOLERANCE_UPPER = 1000

    # Optimization loop
    while npv < TOLERANCE_LOWER or npv > TOLERANCE_UPPER:
        price_logger.info(f"Current NPV: ${npv:.2f}, Iteration: {iteration}, Price: ${price:.2f}")

        # Adjust price based on NPV
        if npv < 0:
            price *= 1.02  # Increment price by 2%
            price_logger.info(f"Increasing price to ${price:.2f} due to NPV below tolerance.")
        elif npv > 0:
            price *= 0.985  # Decrement price by 2%
            price_logger.info(f"Decreasing price to ${price:.2f} due to NPV above tolerance.")

        # Recalculate NPV with the updated price
        results = calculate_revenue_and_expenses_from_modules(config_received, config_matrix_df, results_folder, version, selected_v, selected_f, price, target_row, iteration)
        npv = results['primary_result']
        iteration = results['secondary_result']

        # Check if within tolerance to break the loop
        if TOLERANCE_LOWER <= npv <= TOLERANCE_UPPER:
            price_logger.info("NPV is within tolerance bounds. Exiting optimization loop.")
            break

    return price, npv  # Optionally return the final price and NPV

# Ensure script runs as expected when invoked
if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else 1
    selected_v = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {f'V{i+1}': 'off' for i in range(10)}
    selected_f = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {f'F{i+1}': 'off' for i in range(5)}
    target_row = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    selected_calculation_option = sys.argv[5] if len(sys.argv) > 5 else 'calculateforprice'  # Default to calculateforprice
    senParameters = json.loads(sys.argv[6]) if len(sys.argv) > 6 else {}

    cfa_logger.info(f"Script started with version: {version}, V selections: {selected_v}, F selections: {selected_f}, Target row: {target_row}")
    main(version, selected_v, selected_f, target_row)
    cfa_logger.info("Script finished execution.")