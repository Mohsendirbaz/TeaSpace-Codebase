import logging
import numpy as np
import os
import pandas as pd
from .utility import remove_existing_file, pad_or_trim

# Function to calculate annual revenue
def calculate_annual_revenue(numberOfUnitsAmount12, initialSellingPriceAmount13, generalInflationRateAmount23, years, construction_years):
    revenue = [0] * construction_years + [
        int(numberOfUnitsAmount12 * initialSellingPriceAmount13 * (1 + generalInflationRateAmount23) )
        for year in range(construction_years, years)
    ]
    logging.debug(f"Annual Revenue: {revenue}")
    return revenue

# Extended function to calculate annual revenue (mirroring calculate_annual_operating_expenses)
def calculate_annual_revenue_extended(
    use_direct_operating_expensesAmount19,
    numberOfUnitsAmount12,
    initialSellingPriceAmount13,
    variable_RevAmount6,
    amounts_per_unitRevAmount7,
    MaterialInventory_Rev,
    Labor_Rev,
    utility_Rev,
    maintenance_amount_Rev,
    insurance_amount_Rev,
    annual_revenue,
    generalInflationRateAmount23,
    years,
    construction_years,
    selected_r,
    selected_rf
    ):

    # List of fixed revenue components (corresponding to selected_rf)
    fixed_revenue = [MaterialInventory_Rev, Labor_Rev, utility_Rev, maintenance_amount_Rev, insurance_amount_Rev]

    # Check if selected_r is a dictionary, if not convert it to a dictionary with all values set to 'on'
    if not isinstance(selected_r, dict):
        logging.warning(f"selected_r is not a dictionary, it is a {type(selected_r)}. Converting to dictionary with all values 'on'.")
        selected_r = {f'R{i+1}': 'on' for i in range(10)}

    # Filter variable revenue and amounts per unit based on selected_r
    # If 'off', set corresponding value to 0
    variable_rev_filtered = [
        round(rev * (1 + generalInflationRateAmount23)) if selected_r.get(f'R{i+1}') == 'on' else 0
        for i, rev in enumerate(variable_RevAmount6)
    ]

    amounts_per_unit_filtered = [
        amount if selected_r.get(f'R{i+1}') == 'on' else 0 for i, amount in enumerate(amounts_per_unitRevAmount7)
    ]

    logging.info(f"Filtered variable revenue: {variable_rev_filtered}")
    logging.info(f"Filtered amounts per unit: {amounts_per_unit_filtered}")

    # Check if selected_rf is a dictionary, if not convert it to a dictionary with all values set to 'on'
    if not isinstance(selected_rf, dict):
        logging.warning(f"selected_rf is not a dictionary, it is a {type(selected_rf)}. Converting to dictionary with all values 'on'.")
        selected_rf = {f'RF{i+1}': 'on' for i in range(5)}

    # Filter fixed revenue based on selected_rf
    # If 'off', set corresponding value to 0
    fixed_rev_filtered = [
        round(rev * (1 + generalInflationRateAmount23)) if selected_rf.get(f'RF{i+1}') == 'on' else 0
        for i, rev in enumerate(fixed_revenue)
    ]

    logging.info(f"Filtered fixed revenue: {fixed_rev_filtered}")

    # Calculate total fixed revenue
    total_fixed_revenue = sum(fixed_rev_filtered)
    logging.info(f"Total fixed revenue: {total_fixed_revenue}")

    # If direct revenue calculation is used, use the standard calculation
    if use_direct_operating_expensesAmount19:
        revenues = [0] * construction_years + [
            int(numberOfUnitsAmount12 * initialSellingPriceAmount13 * (1 + generalInflationRateAmount23))
            for year in range(construction_years, years)
        ]
        logging.info(f"Revenue (direct method): {revenues}")
    else:
        logging.info("Using indirect calculation for revenue.")
        # Calculate total variable revenue (filtered based on selected_r)
        annual_variable_revenue = np.sum([
            rev * amount for rev, amount in zip(variable_rev_filtered, amounts_per_unit_filtered)
        ])
        logging.info(f"Annual variable revenue: {annual_variable_revenue}")

        # Calculate the total revenue over the years, applying inflation after construction years
        revenues = [0] * construction_years + [
            int((annual_variable_revenue + total_fixed_revenue))
            for year in range(construction_years, years)
        ]
        logging.info(f"Revenue (indirect method): {revenues}")

        # Log the final result
        logging.info(f"Final revenue: {revenues}")
        logging.info(f"Filtered variable revenue returned: {variable_rev_filtered}")
        logging.info(f"Filtered fixed revenue returned: {fixed_rev_filtered}")

    return revenues, variable_rev_filtered, fixed_rev_filtered

# Generate fixed revenue table
def generate_fixed_revenue_table(fixed_rev_results, plant_lifetime):
    columns = ['Year', 'RF1', 'RF2', 'RF3', 'RF4', 'RF5']
    fixed_revenue_table = pd.DataFrame(0, index=range(plant_lifetime), columns=columns)
    fixed_revenue_table['Year'] = range(1, plant_lifetime + 1)

    for (start_year, end_year), fixed_rev in fixed_rev_results.items():
        fixed_rev = pad_or_trim(fixed_rev, 5)
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                fixed_revenue_table.loc[year_idx, 'RF1':'RF5'] = fixed_rev

    return fixed_revenue_table

# Generate variable revenue table
def generate_variable_revenue_table(variable_rev_results, plant_lifetime):
    columns = ['Year', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10']
    variable_revenue_table = pd.DataFrame(0, index=range(plant_lifetime), columns=columns)
    variable_revenue_table['Year'] = range(1, plant_lifetime + 1)

    for (start_year, end_year), variable_rev in variable_rev_results.items():
        variable_rev = pad_or_trim(variable_rev, 10)
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                variable_revenue_table.loc[year_idx, 'R1':'R10'] = variable_rev

    return variable_revenue_table

# Generate cumulative revenue table
def generate_cumulative_revenue_table(fixed_rev_results, variable_rev_results, revenue_results, plant_lifetime):
    columns = ['Year', 'RF1', 'RF2', 'RF3', 'RF4', 'RF5', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 'Revenue']
    cumulative_revenue_table = pd.DataFrame(0, index=range(plant_lifetime), columns=columns)
    cumulative_revenue_table['Year'] = range(1, plant_lifetime + 1)

    for (start_year, end_year), fixed_rev in fixed_rev_results.items():
        fixed_rev = pad_or_trim(fixed_rev, 5)
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                cumulative_revenue_table.loc[year_idx, 'RF1':'RF5'] = fixed_rev

    for (start_year, end_year), variable_rev in variable_rev_results.items():
        variable_rev = pad_or_trim(variable_rev, 10)
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                cumulative_revenue_table.loc[year_idx, 'R1':'R10'] = variable_rev

    for (start_year, end_year), revenues in revenue_results.items():
        for year in range(start_year, end_year + 1):
            year_idx = year - 1
            if 0 <= year_idx < plant_lifetime:
                cumulative_revenue_table.loc[year_idx, 'Revenue'] = revenues[year - start_year]

    return cumulative_revenue_table

# Save revenue tables
def save_revenue_tables(fixed_rev_results, variable_rev_results, revenue_results, plant_lifetime, results_folder, version):
    # Generate the tables
    fixed_revenue_table = generate_fixed_revenue_table(fixed_rev_results, plant_lifetime)
    variable_revenue_table = generate_variable_revenue_table(variable_rev_results, plant_lifetime)
    cumulative_revenue_table = generate_cumulative_revenue_table(fixed_rev_results, variable_rev_results, 
                                                           revenue_results, plant_lifetime)

    # Define the file paths
    fixed_revenue_path = os.path.join(results_folder, f"Fixed_Revenue_Table_({version}).csv")
    variable_revenue_path = os.path.join(results_folder, f"Variable_Revenue_Table_({version}).csv")
    cumulative_revenue_path = os.path.join(results_folder, f"Cumulative_Revenue_Table_({version}).csv")

    # Remove existing files if they exist
    remove_existing_file(fixed_revenue_path)
    remove_existing_file(variable_revenue_path)
    remove_existing_file(cumulative_revenue_path)

    # Save the new tables
    fixed_revenue_table.to_csv(fixed_revenue_path, index=False)
    variable_revenue_table.to_csv(variable_revenue_path, index=False)
    cumulative_revenue_table.to_csv(cumulative_revenue_path, index=False)
