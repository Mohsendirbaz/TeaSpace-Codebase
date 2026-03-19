"""
CFA.py - Cash Flow Analysis

This file has been refactored into separate modules in the CFA_operations directory.
The main functionality is now in consolidated_cfa_new.py, which uses a more efficient approach
with keywords used exactly once in their strictest form.
This file is kept for backward compatibility and has been enhanced to support the CalculationMonitor.
"""

import json
import os
import sys
import importlib.util
import time
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import from the refactored modules
from backend.Core_calculation_engines.CFA_operations.utility import price_logger, cfa_logger
from backend.Core_calculation_engines.consolidated_cfa_new import main

def create_status_file(version, calculation_step, calculation_details=None, payload_details=None, progress_percentage=0, price=None, npv=None, complete=False, success=False, error=None):
    """
    Creates or updates a status file for the calculation process.
    This file is used by the CalculationMonitor to display real-time updates.

    Args:
        version (str): The version number
        calculation_step (str): The current calculation step
        calculation_details (dict, optional): Details about the calculation
        payload_details (dict, optional): Details about the payload
        progress_percentage (int, optional): The progress percentage (0-100)
        price (float, optional): The current price
        npv (float, optional): The current NPV
        complete (bool, optional): Whether the calculation is complete
        success (bool, optional): Whether the calculation was successful
        error (str, optional): Any error message
    """
    # Construct path to the status file
    results_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        "Original", f"Batch({version})", f"Results({version})"
    )
    os.makedirs(results_folder, exist_ok=True)
    status_file = os.path.join(results_folder, f"price_optimization_status_{version}.json")

    # Prepare the status data
    status_data = {
        "version": version,
        "calculation_step": calculation_step,
        "calculation_details": calculation_details or {},
        "payload_details": payload_details or {},
        "progress_percentage": progress_percentage,
        "current_price": price,
        "current_npv": npv,
        "complete": complete,
        "success": success,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }

    # Write the status data to the file
    try:
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        cfa_logger.info(f"Updated status file for version {version}: {calculation_step}")
    except Exception as e:
        cfa_logger.error(f"Error updating status file for version {version}: {str(e)}")

def monitored_main(version, selected_v, selected_f, selected_r, selected_rf, target_row):
    """
    Wrapper around the main function that adds status file updates for monitoring.
    """
    try:
        # Initialize status file
        create_status_file(
            version=version,
            calculation_step="Initializing calculation",
            payload_details={
                "version": version,
                "selected_v": str(selected_v),
                "selected_f": str(selected_f),
                "selected_r": str(selected_r),
                "selected_rf": str(selected_rf),
                "target_row": target_row
            },
            progress_percentage=5
        )

        # Load configuration
        create_status_file(
            version=version,
            calculation_step="Loading configuration",
            progress_percentage=10
        )

        # Call the main function with progress updates
        start_time = time.time()
        price, npv = main(version, selected_v, selected_f, selected_r, selected_rf, target_row)
        end_time = time.time()

        # Final status update
        create_status_file(
            version=version,
            calculation_step="Calculation complete",
            calculation_details={
                "final_price": price,
                "final_npv": npv,
                "execution_time_seconds": round(end_time - start_time, 2)
            },
            payload_details={
                "version": version,
                "selected_v": str(selected_v),
                "selected_f": str(selected_f),
                "selected_r": str(selected_r),
                "selected_rf": str(selected_rf),
                "target_row": target_row
            },
            progress_percentage=100,
            price=price,
            npv=npv,
            complete=True,
            success=True
        )

        return price, npv
    except Exception as e:
        # Error status update
        create_status_file(
            version=version,
            calculation_step="Error in calculation",
            error=str(e),
            complete=True,
            success=False
        )
        cfa_logger.error(f"Error in monitored_main: {str(e)}")
        raise

# Ensure script runs as expected when invoked
if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else 1

    # Safely parse JSON arguments with error handling
    def safe_json_load(arg_index, default_value):
        if len(sys.argv) > arg_index:
            try:
                return json.loads(sys.argv[arg_index])
            except json.JSONDecodeError:
                cfa_logger.warning(f"Invalid JSON in argument {arg_index}. Using default value.")
                return default_value
        return default_value

    selected_v = safe_json_load(2, {f'V{i+1}': 'off' for i in range(10)})
    selected_f = safe_json_load(3, {f'F{i+1}': 'off' for i in range(5)})
    selected_r = safe_json_load(4, {f'R{i+1}': 'off' for i in range(10)})
    selected_rf = safe_json_load(5, {f'RF{i+1}': 'off' for i in range(5)})

    # Safely convert target_row to integer with error handling
    def safe_int_conversion(arg_index, default_value):
        if len(sys.argv) > arg_index:
            try:
                return int(sys.argv[arg_index])
            except ValueError:
                cfa_logger.warning(f"Invalid integer in argument {arg_index}. Using default value.")
                return default_value
        return default_value

    target_row = safe_int_conversion(6, 10)
    selected_calculation_option = sys.argv[7] if len(sys.argv) > 7 else 'calculateforprice'
    senParameters = safe_json_load(8, {})

    cfa_logger.info(f"Script started with version: {version}, V selections: {selected_v}, F selections: {selected_f}, R selections: {selected_r}, RF selections: {selected_rf}, Target row: {target_row}")

    # Use the monitored_main function instead of main directly
    # This enables real-time monitoring through the CalculationMonitor component
    try:
        price, npv = monitored_main(version, selected_v, selected_f, selected_r, selected_rf, target_row)
        cfa_logger.info(f"Script finished execution. Final price: ${price:.2f}, Final NPV: ${npv:.2f}")
    except Exception as e:
        cfa_logger.error(f"Script execution failed: {str(e)}")
        raise
