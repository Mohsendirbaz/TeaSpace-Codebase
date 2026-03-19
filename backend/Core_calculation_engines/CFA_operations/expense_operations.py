import logging
import numpy as np
import os
import pandas as pd
from .utility import remove_existing_file, pad_or_trim

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