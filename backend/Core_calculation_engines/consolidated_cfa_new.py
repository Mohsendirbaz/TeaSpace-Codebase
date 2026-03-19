import json
import os
import pandas as pd
import numpy as np
import sys
import importlib.util
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import itertools

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import keyword constants to ensure each keyword is used exactly once
from backend.Core_calculation_engines.keyword_constants import (
    get_keyword, capitalize_keyword, get_component_names,
    get_column_names, get_result_dict_names, get_operational_dict_names,
    get_component_cost_keys, get_component_rev_keys,
    get_operational_labels, get_revenue_labels
)

# Import from CFA_operations modules
from backend.Core_calculation_engines.CFA_operations.utility import remove_existing_file, pad_or_trim, price_logger, cfa_logger
from backend.Core_calculation_engines.CFA_operations.revenue_operations import (
    calculate_annual_revenue, calculate_annual_revenue_extended,
    generate_fixed_revenue_table, generate_variable_revenue_table,
    generate_cumulative_revenue_table, save_revenue_tables
)
from backend.Core_calculation_engines.CFA_operations.expense_operations import (
    calculate_annual_operating_expenses, generate_fixed_opex_table,
    generate_variable_opex_table, generate_cumulative_opex_table, save_opex_tables
)
from backend.Core_calculation_engines.CFA_operations.tax_operations import calculate_state_tax, calculate_federal_tax
from backend.Core_calculation_engines.CFA_operations.config_operations import read_config_module, load_configuration
from backend.Core_calculation_engines.CFA_operations.visualization_operations import (
    create_operational_cost_pie_chart, create_operational_revenue_pie_chart,
    create_economic_summary
)

def calculate_revenue_and_expenses_from_modules(config_received, config_matrix_df, results_folder, version, selected_v, selected_f, selected_r, selected_rf, price, target_row, iteration):
    # Extract parameters
    plant_lifetime = config_received.plantLifetimeAmount10
    construction_years = config_received.numberofconstructionYearsAmount28

    BEC = config_received.bECAmount11
    EPC = config_received.engineering_Procurement_and_Construction_EPC_Amount15
    PC = config_received.process_contingency_PC_Amount16
    PT = config_received.project_Contingency_PT_BEC_EPC_PCAmount17

    TOC = BEC + EPC * BEC + PC * (BEC + EPC * BEC) + PT * (BEC + EPC * BEC + PC * (BEC + EPC * BEC))

    cfa_logger.debug(f"Total Overnight Cost (TOC) calculated: {TOC}")

    # Get column names from the helper function
    columns = get_column_names()
    YEAR_COL = columns['year']
    REVENUE_COL = columns['revenue']
    EXPENSES_COL = columns['expenses']
    LOAN_COL = columns['loan']
    DEPRECIATION_COL = columns['depreciation']
    STATE_TAXES_COL = columns['state_taxes']
    FEDERAL_TAXES_COL = columns['federal_taxes']
    AFTER_TAX_CASH_FLOW_COL = columns['after_tax_cash_flow']
    DISCOUNTED_CASH_FLOW_COL = columns['discounted_cash_flow']
    CUMULATIVE_CASH_FLOW_COL = columns['cumulative_cash_flow']

    CFA_matrix = pd.DataFrame(np.zeros(((plant_lifetime + construction_years), 10)),
                              columns=[YEAR_COL, REVENUE_COL, EXPENSES_COL, LOAN_COL, DEPRECIATION_COL, 
                                      STATE_TAXES_COL, FEDERAL_TAXES_COL, AFTER_TAX_CASH_FLOW_COL,
                                      DISCOUNTED_CASH_FLOW_COL, CUMULATIVE_CASH_FLOW_COL])
    CFA_matrix[YEAR_COL] = range(1, len(CFA_matrix)+1)

    # Helper function to create multiple empty dictionaries
    def create_empty_dicts(names):
        return {name: {} for name in names}

    # Complete set for CFA matrix - using dictionary comprehension
    result_dict_names = get_result_dict_names()
    results_dicts = create_empty_dicts(result_dict_names)

    # Unpack the dictionaries into individual variables
    revenue_results, expenses_results, fixed_costs_results, variable_costs_results, fixed_rev_results, variable_rev_results = [
        results_dicts[name] for name in result_dict_names
    ]

    # Operational set for OPEX (without construction years) - using dictionary comprehension
    operational_dict_names = get_operational_dict_names()
    operational_dicts = create_empty_dicts(operational_dict_names)

    # Unpack the dictionaries into individual variables
    revenue_operational, expenses_operational, fixed_costs_operational, variable_costs_operational, fixed_rev_operational, variable_rev_operational = [
        operational_dicts[name] for name in operational_dict_names
    ]
    module_selling_price_operational = {}

    # Get component cost keys
    component_cost_keys = get_component_cost_keys()
    cost_operational_dicts = {key: {} for key in component_cost_keys.keys()}

    # Unpack the dictionaries into individual variables using the variable names from component_cost_keys
    feedstock_cost_operational, labor_cost_operational, utility_cost_operational, maintenance_cost_operational, insurance_cost_operational = [
        cost_operational_dicts[key] for key in component_cost_keys.keys()
    ]

    # Get component revenue keys
    component_rev_keys = get_component_rev_keys()
    rev_operational_dicts = {key: {} for key in component_rev_keys.keys()}

    # Unpack the dictionaries into individual variables using the variable names from component_rev_keys
    feedstock_rev_operational, labor_rev_operational, utility_rev_operational, maintenance_rev_operational, insurance_rev_operational = [
        rev_operational_dicts[key] for key in component_rev_keys.keys()
    ]

    interval_units_sold = {}
    total_units_sold = 0
    cumulative_length = 0
    cumulative_total_units_sold = 0
    up_to_year={}

    # Iterate through the config matrix
    for idx, row in config_matrix_df.iterrows():  # Loop through each row in the configuration matrix to process individual time periods
        start_year = int(row['start']) + construction_years
        end_year = int(row['end']) + construction_years
        length = int(row['end']) - int(row['start']) + 1
        cumulative_length += length
        cfa_logger.debug(f"cumulative_length: {cumulative_length}")
        config_module_file = os.path.join(results_folder, f"{version}_config_module_{row['start']}.json")
        if not os.path.exists(config_module_file):
            cfa_logger.warning(f"Config module file not found: {config_module_file}")
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

            # Add extended revenue calculation
            annual_revenue_extended, variable_rev, fixed_rev = calculate_annual_revenue_extended(
                config_module.get('use_direct_operating_expensesAmount19', True),  # Default to True if not present
                config_module['numberOfUnitsAmount12'],
                config_module['initialSellingPriceAmount13'],
                config_module.get('variable_RevAmount6', [0] * 10),  # Default to zeros if not present
                config_module.get('amounts_per_unitRevAmount7', [0] * 10),  # Default to zeros if not present
                config_module.get('MaterialInventory_Rev', 0),  # Default to 0 if not present
                config_module.get('Labor_Rev', 0),  # Default to 0 if not present
                config_module.get('utility_Rev', 0),  # Default to 0 if not present
                config_module.get('maintenance_amount_Rev', 0),  # Default to 0 if not present
                config_module.get('insurance_amount_Rev', 0),  # Default to 0 if not present
                annual_revenue,  # Pass the already calculated revenue
                config_module['generalInflationRateAmount23'],
                plant_lifetime + construction_years,
                construction_years,
                selected_r,
                selected_rf
            )
        else:
            # Use the calculated price if the period is before the target row
            annual_revenue = calculate_annual_revenue(
                config_module['numberOfUnitsAmount12'],
                price,  # Dynamic price
                config_module['generalInflationRateAmount23'],
                plant_lifetime + construction_years,
                construction_years
            )

            # Add extended revenue calculation with the dynamic price
            annual_revenue_extended, variable_rev, fixed_rev = calculate_annual_revenue_extended(
                config_module.get('use_direct_operating_expensesAmount19', True),
                config_module['numberOfUnitsAmount12'],
                price,  # Use the dynamic price
                config_module.get('variable_RevAmount6', [0] * 10),
                config_module.get('amounts_per_unitRevAmount7', [0] * 10),
                config_module.get('MaterialInventory_Rev', 0),
                config_module.get('Labor_Rev', 0),
                config_module.get('utility_Rev', 0),
                config_module.get('maintenance_amount_Rev', 0),
                config_module.get('insurance_amount_Rev', 0),
                annual_revenue,
                config_module['generalInflationRateAmount23'],
                plant_lifetime + construction_years,
                construction_years,
                selected_r,
                selected_rf
            )
        cfa_logger.debug(f"Annual Revenue calculated: {annual_revenue}")
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

        # Factory function to generate operational dictionaries
        def update_operational_dict(component_dict, values, idx, multiplier):
            component_names = get_component_names()
            for i, component_name in enumerate(component_names):
                if i < len(values):
                    key = f"{component_name}_{get_keyword('c')}_operational"
                    if key in component_dict:
                        component_dict[key][idx] = values[i] * multiplier
            return component_dict

        # Create dictionaries of operational cost and revenue dictionaries
        component_names = get_component_names()
        component_cost_keys = get_component_cost_keys()
        component_rev_keys = get_component_rev_keys()

        # Map component names to their respective dictionaries
        cost_operational_dicts_map = {
            component_cost_keys[f"{component_name}_{get_keyword('c')}_operational"]: 
                cost_operational_dicts[f"{component_name}_{get_keyword('c')}_operational"]
            for component_name in component_names
        }

        rev_operational_dicts_map = {
            component_rev_keys[f"{component_name}_{get_keyword('rv')}_operational"]: 
                rev_operational_dicts[f"{component_name}_{get_keyword('rv')}_operational"]
            for component_name in component_names
        }

        # Update cost and revenue operational dictionaries using the factory function
        update_operational_dict(cost_operational_dicts, fixed_costs, idx, adjusted_length_calculation)
        update_operational_dict(rev_operational_dicts, fixed_rev, idx, adjusted_length_calculation)

        if int(row['start'])+1> target_row:
        # Store module selling price for each row
            module_selling_price_operational[idx] = config_module['initialSellingPriceAmount13'] * adjusted_length_calculation
        else:
            module_selling_price_operational[idx] = price * adjusted_length_calculation

        # Helper function to store results in multiple dictionaries
        def store_results(key, values_dict):
            for dict_name, value in values_dict.items():
                globals()[dict_name][key] = value

        # Store for CFA and revenue components using the helper function
        cfa_key = (start_year, end_year)

        # Get the dictionary names from the helper functions
        revenue_results_key = get_result_dict_names()[0]
        expenses_results_key = get_result_dict_names()[1]
        fixed_costs_results_key = get_result_dict_names()[2]
        variable_costs_results_key = get_result_dict_names()[3]
        fixed_rev_results_key = get_result_dict_names()[4]
        variable_rev_results_key = get_result_dict_names()[5]

        # Store each result in its corresponding dictionary
        revenue_results[cfa_key] = annual_revenue
        expenses_results[cfa_key] = annual_operating_expenses
        fixed_costs_results[cfa_key] = fixed_costs
        variable_costs_results[cfa_key] = variable_costs
        fixed_rev_results[cfa_key] = fixed_rev
        variable_rev_results[cfa_key] = variable_rev

        # Store for OPEX and Revenue tables
        operational_start_year = int(row['start'])
        operational_end_year = int(row['end'])
        operational_key = (operational_start_year, operational_end_year)

        # Get the dictionary names from the helper functions
        revenue_operational_key = get_operational_dict_names()[0]
        expenses_operational_key = get_operational_dict_names()[1]
        fixed_costs_operational_key = get_operational_dict_names()[2]
        variable_costs_operational_key = get_operational_dict_names()[3]
        fixed_rev_operational_key = get_operational_dict_names()[4]
        variable_rev_operational_key = get_operational_dict_names()[5]

        # Store each operational value in its corresponding dictionary
        revenue_operational[operational_key] = annual_revenue[construction_years:]
        expenses_operational[operational_key] = annual_operating_expenses[construction_years:]
        fixed_costs_operational[operational_key] = fixed_costs
        variable_costs_operational[operational_key] = variable_costs
        fixed_rev_operational[operational_key] = fixed_rev
        variable_rev_operational[operational_key] = variable_rev

        # Factory function to calculate average values
        def calculate_averages(component_dicts, denominator):
            return {
                f"average_{name}": sum(component_dicts[name].values()) / denominator
                for name in component_dicts
            }

        # Calculate average values for each cost and revenue component using the factory function
        total_years = sum(up_to_year.values())

        # Create dictionaries to store average values
        average_cost_values = {}
        average_rev_values = {}

        # Calculate average values for cost components
        component_names = get_component_names()
        for name in component_names:
            component_name = f"{name}_{get_keyword('c')}_operational"
            average_cost_values[f"average_{name}_{get_keyword('c')}_operational"] = sum(locals()[component_cost_keys[component_name]].values()) / total_years

        # Calculate average values for revenue components
        for name in component_names:
            component_name = f"{name}_{get_keyword('rv')}_operational"
            average_rev_values[f"average_{name}_{get_keyword('rv')}_operational"] = sum(locals()[component_rev_keys[component_name]].values()) / total_years

        # Assign to individual variables for backward compatibility
        average_feedstock_cost_operational = average_cost_values[f"average_{get_keyword('fs')}_{get_keyword('c')}_operational"]
        average_labor_cost_operational = average_cost_values[f"average_{get_keyword('l')}_{get_keyword('c')}_operational"]
        average_utility_cost_operational = average_cost_values[f"average_{get_keyword('u')}_{get_keyword('c')}_operational"]
        average_maintenance_cost_operational = average_cost_values[f"average_{get_keyword('m')}_{get_keyword('c')}_operational"]
        average_insurance_cost_operational = average_cost_values[f"average_{get_keyword('i')}_{get_keyword('c')}_operational"]

        average_feedstock_rev_operational = average_rev_values[f"average_{get_keyword('fs')}_{get_keyword('rv')}_operational"]
        average_labor_rev_operational = average_rev_values[f"average_{get_keyword('l')}_{get_keyword('rv')}_operational"]
        average_utility_rev_operational = average_rev_values[f"average_{get_keyword('u')}_{get_keyword('rv')}_operational"]
        average_maintenance_rev_operational = average_rev_values[f"average_{get_keyword('m')}_{get_keyword('rv')}_operational"]
        average_insurance_rev_operational = average_rev_values[f"average_{get_keyword('i')}_{get_keyword('rv')}_operational"]

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

    # Save Revenue tables
    save_revenue_tables(fixed_rev_operational, variable_rev_operational, revenue_operational, plant_lifetime, results_folder, version)

    # Populate CFA matrix
    for idx, row in config_matrix_df.iterrows():  # Loop through each row in the configuration matrix to populate the CFA matrix
        start_year = int(row['start']) + construction_years
        end_year = int(row['end']) + construction_years

        annual_revenue = revenue_results.get((start_year, end_year), [])
        annual_operating_expenses = expenses_results.get((start_year, end_year), [])

        for year in range(start_year, end_year + 1):  # Loop through each year in the current time period to populate revenue and expenses
            cfa_year = year
            if year < len(annual_revenue):
                CFA_matrix.at[cfa_year, REVENUE_COL] = annual_revenue[year]
            if year < len(annual_operating_expenses):
                CFA_matrix.at[cfa_year, EXPENSES_COL] = annual_operating_expenses[year]

    # Save CFA matrix
    CFA_matrix_file = os.path.join(results_folder, f"CFA({version}).csv")
    remove_existing_file(CFA_matrix_file)
    CFA_matrix.to_csv(CFA_matrix_file, index=False)

    # Second loop to place results in the correct places in the CFA matrix
    for idx, row in config_matrix_df.iterrows():  # Loop through each row in the configuration matrix to update the CFA matrix with adjusted indices
        start_year = int(row['start']) + construction_years
        end_year = int(row['end']) + construction_years
        length = int(row['length'])

        # Get the results for the current interval
        annual_revenue = revenue_results.get((start_year, end_year), [])
        annual_operating_expenses = expenses_results.get((start_year, end_year), [])

        # Update the CFA matrix with annual revenue and expenses
        for year in range(start_year, end_year + 1):  # Loop through each year in the current time period with adjusted year index (cfa_year = year-1)
            cfa_year = year-1

            if year < len(annual_revenue):
                CFA_matrix.at[cfa_year, REVENUE_COL] = annual_revenue[year]

            if year < len(annual_operating_expenses):
                CFA_matrix.at[cfa_year, EXPENSES_COL] = annual_operating_expenses[year]

    # Populate the CFA matrix for construction years
    cumulative_cash_flow = 0
    for year in range(construction_years):  # Loop through each construction year to distribute the Total Overnight Cost (TOC)
        operating_expenses = -TOC / construction_years
        CFA_matrix.loc[year, EXPENSES_COL] = operating_expenses
        CFA_matrix.loc[year, CUMULATIVE_CASH_FLOW_COL] = cumulative_cash_flow + operating_expenses
        cumulative_cash_flow += operating_expenses

    # Create a matrix for distance from paying taxes
    distance_matrix = pd.DataFrame(0, index=range(len(CFA_matrix)), columns=['Potentially Taxable Income', 'Fraction of TOC'])

    # Calculate the difference (revenue - operating expenses) and (revenue - operating expenses)/TOC
    for i in range(construction_years, len(CFA_matrix)):  # Loop through each operational year to calculate potentially taxable income and fraction of TOC
        revenue = CFA_matrix.at[i, REVENUE_COL]
        operating_expenses = CFA_matrix.at[i, EXPENSES_COL]
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
    for i in range(construction_years, len(CFA_matrix)):  # Loop through each operational year to find when cumulative fraction exceeds 1 (full depreciation)
        cumulative_fraction += distance_matrix.at[i, 'Fraction of TOC']
        if cumulative_fraction > 1:
            depreciation_end_year = i
            break

    # Populate depreciation in the CFA matrix
    if depreciation_end_year:
        for year in range(construction_years, depreciation_end_year):
            depreciation_value = int(distance_matrix.at[year, 'Fraction of TOC'] * TOC)
            CFA_matrix.at[year, DEPRECIATION_COL] = depreciation_value
            cfa_logger.info("Finished CFA calculation")
        remaining_toc = int(TOC - CFA_matrix[DEPRECIATION_COL].sum())
        CFA_matrix.at[depreciation_end_year, DEPRECIATION_COL] = remaining_toc

    # Calculate and populate state and federal taxes in the CFA matrix
    for year in range(construction_years, plant_lifetime + construction_years):  # Loop through each operational year to calculate taxes, cash flows, and update the CFA matrix
        revenue = CFA_matrix.at[year, REVENUE_COL]
        operating_expenses = CFA_matrix.at[year, EXPENSES_COL]
        depreciation = CFA_matrix.at[year, DEPRECIATION_COL]

        state_tax = calculate_state_tax(revenue, config_received.stateTaxRateAmount32, operating_expenses, depreciation)
        federal_tax = calculate_federal_tax(revenue, config_received.federalTaxRateAmount33, operating_expenses, depreciation)

        CFA_matrix.at[year, STATE_TAXES_COL] = state_tax
        CFA_matrix.at[year, FEDERAL_TAXES_COL] = federal_tax

        after_tax_cash_flow = revenue - operating_expenses - state_tax - federal_tax
        CFA_matrix.at[year, AFTER_TAX_CASH_FLOW_COL] = after_tax_cash_flow
        Discounted_cash_flow = after_tax_cash_flow/(1 + config_received.iRRAmount30)
        CFA_matrix.at[year, DISCOUNTED_CASH_FLOW_COL] = Discounted_cash_flow

        cumulative_cash_flow += Discounted_cash_flow
        CFA_matrix.at[year, CUMULATIVE_CASH_FLOW_COL] = cumulative_cash_flow

    CFA_matrix = CFA_matrix.astype(int)

    # Save CFA matrix
    CFA_matrix_file = os.path.join(results_folder, f"CFA({version}).csv")
    remove_existing_file(CFA_matrix_file)
    CFA_matrix.to_csv(CFA_matrix_file, index=False)

    # Calculate economic summary
    operational_years = plant_lifetime

    total_revenue = CFA_matrix.loc[construction_years:, REVENUE_COL].sum()
    total_operating_expenses = CFA_matrix.loc[construction_years:, EXPENSES_COL].sum()
    total_depreciation = CFA_matrix.loc[construction_years:, DEPRECIATION_COL].sum()
    total_state_taxes = CFA_matrix.loc[construction_years:, STATE_TAXES_COL].sum()
    total_federal_taxes = CFA_matrix.loc[construction_years:, FEDERAL_TAXES_COL].sum()
    total_after_tax_cash_flow = CFA_matrix.loc[construction_years:, AFTER_TAX_CASH_FLOW_COL].sum()
    total_discounted_cash_flow = CFA_matrix.loc[construction_years:, DISCOUNTED_CASH_FLOW_COL].sum()
    average_selling_price_operational=total_revenue/ total_units_sold
    cumulative_npv = CFA_matrix.loc[construction_years:, CUMULATIVE_CASH_FLOW_COL].iloc[-1]
    cfa_logger.info(f"total_units_sold: {total_units_sold}")

    # Create economic summary
    create_economic_summary(
        config_received, TOC, total_revenue, total_operating_expenses,
        total_depreciation, total_state_taxes, total_federal_taxes,
        total_after_tax_cash_flow, total_discounted_cash_flow,
        average_selling_price_operational, cumulative_npv,
        operational_years, results_folder, version
    )

    # Get labels for pie charts
    operational_labels = get_operational_labels()
    operational_sizes = [
        average_feedstock_cost_operational,
        average_labor_cost_operational,
        average_utility_cost_operational,
        average_maintenance_cost_operational,
        average_insurance_cost_operational
    ]

    # Get labels for revenue pie charts
    revenue_labels = get_revenue_labels()
    revenue_sizes = [
        average_feedstock_rev_operational,
        average_labor_rev_operational,
        average_utility_rev_operational,
        average_maintenance_rev_operational,
        average_insurance_rev_operational
    ]

    # Create static plot directory
    static_plot=os.path.join(results_folder, f'{version}_PieStaticPlots')
    os.makedirs(static_plot, exist_ok=True)

    # Create operational cost pie chart
    create_operational_cost_pie_chart(operational_labels, operational_sizes, selected_f, static_plot, version)

    # Create operational revenue pie chart
    create_operational_revenue_pie_chart(revenue_labels, revenue_sizes, selected_rf, static_plot, version)

    # Price Finding Block
    NPV_year=target_row # Set the NPV year to the target row (user specified) plus construction years (cfa table compatibility)
    npv=CFA_matrix.at[NPV_year, CUMULATIVE_CASH_FLOW_COL]
    iteration+=1  # Increment the iteration counter

    price_logger.info(f"Calculated Current NPV: {npv:.2f} from row {NPV_year}")
    price_logger.info(f"'primary_result': {npv},'secondary_result': {iteration}")

    return {
        'primary_result': npv,
        'secondary_result': iteration,
    }  # Return the calculated NPV and iteration count

# Main function to load config matrix and run the update
def main(version, selected_v, selected_f, selected_r, selected_rf, target_row):
    # Set up paths for modules and results
    code_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Original")

    results_folder = os.path.join(code_files_path, f"Batch({version})", f"Results({version})")
    config_matrix_file = os.path.join(results_folder, f"General_Configuration_Matrix({version}).csv")

    # Load the config matrix
    config_matrix_df = pd.read_csv(config_matrix_file)

    # Load configuration file
    config_received = load_configuration(version, code_files_path)
    iteration = 0

    # Initial price and NPV calculation
    price = config_received.initialSellingPriceAmount13
    results = calculate_revenue_and_expenses_from_modules(config_received, config_matrix_df, results_folder, version, selected_v, selected_f, selected_r, selected_rf, price, target_row, iteration)
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
        results = calculate_revenue_and_expenses_from_modules(config_received, config_matrix_df, results_folder, version, selected_v, selected_f, selected_r, selected_rf, price, target_row, iteration)
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
    selected_v = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {f'V{i+1}': 'off' for i in range(10)}  # Loop to create a dictionary of variable cost selections with default 'off' state
    selected_f = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {f'F{i+1}': 'off' for i in range(5)}  # Loop to create a dictionary of fixed cost selections with default 'off' state
    selected_r = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {f'R{i+1}': 'off' for i in range(10)}  # Loop to create a dictionary of variable revenue selections with default 'off' state
    selected_rf = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {f'RF{i+1}': 'off' for i in range(5)}  # Loop to create a dictionary of fixed revenue selections with default 'off' state
    target_row = int(sys.argv[6]) if len(sys.argv) > 6 else 10
    selected_calculation_option = sys.argv[7] if len(sys.argv) > 7 else 'calculateforprice'
    senParameters = json.loads(sys.argv[8]) if len(sys.argv) > 8 else {}

    cfa_logger.info(f"Script started with version: {version}, V selections: {selected_v}, F selections: {selected_f}, R selections: {selected_r}, RF selections: {selected_rf}, Target row: {target_row}")
    main(version, selected_v, selected_f, selected_r, selected_rf, target_row)
    cfa_logger.info("Script finished execution.")
