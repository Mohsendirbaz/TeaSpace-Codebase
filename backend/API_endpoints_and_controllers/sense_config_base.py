"""
Sensitivity Configuration Base Module

This module provides functionality to copy configuration modules for sensitivity analysis.
It is designed to work independently from the main calculation orchestration.

Key features:
1. Applies sensitivity variations to all configuration modules (1-100)
2. Implements a pause before execution to ensure files exist
3. Organized configuration copying for each sensitivity parameter
4. Complete logging and error handling
5. Generates SensitivityPlotDatapoints_{version}.json for plot visualization
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import logging
import json
import time
import sys
import shutil
import pickle
import copy
import importlib.util

# =====================================
# Configuration Constants
# =====================================

# Define base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_DIR = os.path.join(BASE_DIR, 'backend')
LOGS_DIR = os.path.join(SCRIPT_DIR, 'Logs')
ORIGINAL_BASE_DIR = os.path.join(BASE_DIR, 'Original')

# Create logs directory if it doesn't exist
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOGS_DIR, "CONFIG_COPY.log")
SENSITIVITY_LOG_PATH = os.path.join(LOGS_DIR, "SENSITIVITY.log")

# Sensitivity configuration status file
SENSITIVITY_CONFIG_STATUS_PATH = os.path.join(LOGS_DIR, "sensitivity_config_status.json")
SENSITIVITY_CONFIG_DATA_PATH = os.path.join(LOGS_DIR, "sensitivity_config_data.pkl")

# =====================================
# Logging Configuration
# =====================================

def setup_logging():
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Configure main application logger
    main_handler = logging.FileHandler(LOG_FILE_PATH)
    main_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

    main_logger = logging.getLogger()
    main_logger.setLevel(logging.DEBUG)
    main_logger.addHandler(main_handler)

    # Configure sensitivity logger as a separate logger
    sensitivity_logger = logging.getLogger('sensitivity')
    sensitivity_logger.setLevel(logging.DEBUG)
    sensitivity_logger.propagate = False  # Prevent propagation to root logger

    sensitivity_handler = logging.FileHandler(SENSITIVITY_LOG_PATH)
    sensitivity_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    sensitivity_logger.addHandler(sensitivity_handler)

    logging.info("Logging configured correctly - Config copy logs going to: " + LOG_FILE_PATH)
    sensitivity_logger.info("Sensitivity logging configured correctly - Logs going to: " + SENSITIVITY_LOG_PATH)

# =====================================
# Import Sen_Config Functions
# =====================================

def import_sensitivity_functions():
    """Import necessary functions from Sen_Config module."""
    sensitivity_logger = logging.getLogger('sensitivity')

    try:
        # Add the Configuration_managment directory to the path
        config_mgmt_path = os.path.join(SCRIPT_DIR, "Configuration_managment")
        if config_mgmt_path not in sys.path:
            sys.path.append(config_mgmt_path)

        # Try direct import
        try:
            from Sen_Config import apply_sensitivity_variation, find_parameter_by_id
            sensitivity_logger.info("Successfully imported sensitivity functions via direct import")
            return apply_sensitivity_variation, find_parameter_by_id
        except ImportError:
            sensitivity_logger.warning("Direct import failed, attempting spec import...")

        # Try spec import if direct import fails
        sen_config_path = os.path.join(config_mgmt_path, "Sen_Config.py")
        if os.path.exists(sen_config_path):
            spec = importlib.util.spec_from_file_location("Sen_Config", sen_config_path)
            sen_config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sen_config_module)

            apply_sensitivity_variation = getattr(sen_config_module, 'apply_sensitivity_variation')
            find_parameter_by_id = getattr(sen_config_module, 'find_parameter_by_id')

            sensitivity_logger.info("Successfully imported sensitivity functions via spec import")
            return apply_sensitivity_variation, find_parameter_by_id
        else:
            raise ImportError(f"Could not find Sen_Config.py at {sen_config_path}")

    except Exception as e:
        sensitivity_logger.error(f"Failed to import sensitivity functions: {str(e)}")
        raise ImportError(f"Failed to import required functions: {str(e)}")

# =====================================
# Configuration Copy Functions
# =====================================

def generate_sensitivity_datapoints(version, SenParameters):
    """
    Generate SensitivityPlotDatapoints_{version}.json file with baseline and variation points.
    Uses actual modified values from configuration modules.

    Args:
        version (int): Version number
        SenParameters (dict): Dictionary containing sensitivity parameters

    Returns:
        str: Path to the generated file
    """
    sensitivity_logger = logging.getLogger('sensitivity')

    # Import necessary functions if not already available
    try:
        apply_sensitivity_variation, find_parameter_by_id = import_sensitivity_functions()
    except Exception as e:
        sensitivity_logger.error(f"Failed to import sensitivity functions for datapoints generation: {str(e)}")
        return None

    # Define paths
    target_base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
    results_folder = os.path.join(target_base_dir, f'Batch({version})', f'Results({version})')
    source_dir = os.path.join(ORIGINAL_BASE_DIR, f'Batch({version})', f'Results({version})')

    sensitivity_logger.info(f"Generating SensitivityPlotDatapoints_{version}.json in {results_folder}")

    # Find a base configuration module to extract baseline values
    base_config = None
    base_config_path = None

    for module_num in range(1, 101):
        potential_path = os.path.join(source_dir, f"{version}_config_module_{module_num}.json")
        if os.path.exists(potential_path):
            base_config_path = potential_path
            try:
                with open(base_config_path, 'r') as f:
                    base_config = json.load(f)
                sensitivity_logger.info(f"Loaded base configuration from {base_config_path}")
                break
            except Exception as e:
                sensitivity_logger.warning(f"Failed to load {potential_path}: {str(e)}")
                continue

    if not base_config:
        sensitivity_logger.warning("No base configuration module found. Using fallback values.")

    # Initialize the datapoints structure
    datapoints = {
        "metadata": {
            "structure_explanation": {
                "S35,S13": "Key format: 'enabledParam,compareToKey' where S35 is enabled parameter and S13 is comparison key",
                "baseline": "Reference point measurement",
                "baseline:key": "Numerical measurement point for baseline (e.g., 10000)",
                "baseline:value": "Reference measurement value to compare against",
                "info": "Position indicator: '+' (all above), '-' (all below), or 'b#' (# variations below baseline)",
                "data": "Collection of variation measurements",
                "data:keys": "Numerical measurement points using actual modified values",
                "data:values": "Actual measurements. Must be initially null/empty when created by sense_config_base.py"
            }
        }
    }

    # Process each enabled parameter
    for param_id, param_config in SenParameters.items():
        if not param_config.get('enabled'):
            continue

        # Get comparison key from parameter configuration
        compare_to_key = param_config.get('compareToKey', 'S13')
        combined_key = f"{param_id},{compare_to_key}"

        # Get mode and values from parameter configuration
        # Normalize mode terminology to match Sen_Config.py
        mode = param_config.get('mode', 'percentage')
        normalized_mode = mode.lower()  # Use lowercase for consistency

        values = param_config.get('values', [])

        if not values:
            continue

        # Get baseline value from base configuration if available
        baseline_value = None
        if base_config:
            try:
                # Find parameter key in base configuration
                param_key = find_parameter_by_id(base_config, param_id)

                # Extract the value using that key
                baseline_value = base_config[param_key]
                sensitivity_logger.info(f"Found base value {baseline_value} for {param_id} via key {param_key}")
            except Exception as e:
                sensitivity_logger.error(f"Error finding parameter {param_id} in base config: {str(e)}")

        # If no baseline value found, use parameter number as fallback
        if baseline_value is None:
            param_num = int(param_id[1:]) if param_id[1:].isdigit() else 0
            baseline_value = 10000 + (param_num * 100)
            sensitivity_logger.warning(f"Using fallback baseline value {baseline_value} for {param_id}")

        # Convert baseline value to numeric if it's not already
        try:
            if isinstance(baseline_value, str):
                if '.' in baseline_value:
                    baseline_value = float(baseline_value)
                else:
                    baseline_value = int(baseline_value)
        except (ValueError, TypeError):
            sensitivity_logger.warning(f"Could not convert baseline value to numeric: {baseline_value}")
            baseline_value = 10000 + (int(param_id[1:]) if param_id[1:].isdigit() else 0) * 100

        # Ensure baseline_key is an integer for the datapoints structure
        baseline_key = int(baseline_value)

        # Create data points dictionary excluding baseline
        data_points = {}

        # Analyze variation positions
        variations_below_baseline = 0
        all_below = True
        all_above = True

        # Create a temporary config copy for calculating modified values
        temp_config = copy.deepcopy(base_config) if base_config else {}

        # Process each variation
        for variation in sorted(values):
            # Skip baseline variation (typically 0) if present
            if variation == 0:
                continue

            # Determine position relative to baseline
            if variation < 0:
                variations_below_baseline += 1
                all_above = False
            elif variation > 0:
                all_below = False

            # Calculate the actual modified value
            modified_value = None

            # Try to calculate the actual modified value using apply_sensitivity_variation
            if base_config and param_key:
                try:
                    # Create a fresh copy to avoid cumulative modifications
                    var_config = copy.deepcopy(base_config)

                    # Apply the variation to get modified config
                    var_config = apply_sensitivity_variation(
                        var_config,
                        param_id,
                        variation,
                        normalized_mode
                    )

                    # Extract the modified value
                    modified_value = var_config[param_key]
                    sensitivity_logger.info(f"Calculated modified value {modified_value} for {param_id} with variation {variation}")
                except Exception as e:
                    sensitivity_logger.warning(f"Error calculating modified value: {str(e)}")

            # Fallback calculation if the above method failed
            if modified_value is None:
                if normalized_mode == 'percentage':
                    # For percentage mode, apply percentage change
                    modified_value = baseline_value * (1 + variation/100)
                elif normalized_mode == 'directvalue':
                    # For direct value mode, use variation value directly
                    modified_value = variation
                elif normalized_mode == 'absolutedeparture':
                    # For absolute departure mode, add variation to the baseline
                    modified_value = baseline_value + variation
                else:
                    # Default to percentage mode for unknown modes
                    modified_value = baseline_value * (1 + variation/100)
                sensitivity_logger.info(f"Using fallback calculation for modified value: {modified_value}")

            # Ensure modified_value is numeric
            if isinstance(modified_value, str):
                try:
                    if '.' in modified_value:
                        modified_value = float(modified_value)
                    else:
                        modified_value = int(modified_value)
                except (ValueError, TypeError):
                    sensitivity_logger.warning(f"Could not convert modified value to numeric: {modified_value}")
                    # Use variation as fallback
                    modified_value = variation

            # Use the modified value as the point key (ensure it's an integer)
            point_key = int(modified_value)
            data_points[str(point_key)] = None

            sensitivity_logger.info(
                f"Added point for {param_id}: variation={variation}, modified_value={modified_value}, point_key={point_key}"
            )

        # Determine info indicator
        if all_below:
            info_indicator = "-"
        elif all_above:
            info_indicator = "+"
        else:
            info_indicator = f"b{variations_below_baseline}"

        # Add to datapoints structure
        datapoints[combined_key] = {
            "baseline": {str(baseline_key): None},
            "info": info_indicator,
            "data": data_points
        }

        sensitivity_logger.info(
            f"Added datapoints for {combined_key}: baseline={baseline_key}, "
            f"mode={normalized_mode}, variations={len(data_points)}, info={info_indicator}"
        )

    # Write to file in Results folder (not in Sensitivity subfolder)
    output_file = os.path.join(results_folder, f"SensitivityPlotDatapoints_{version}.json")

    try:
        with open(output_file, 'w') as f:
            json.dump(datapoints, f, indent=2)
        sensitivity_logger.info(
            f"Successfully saved SensitivityPlotDatapoints_{version}.json with "
            f"{len(datapoints) - 1} parameter entries"
        )
    except Exception as e:
        error_msg = f"Failed to write SensitivityPlotDatapoints_{version}.json: {str(e)}"
        sensitivity_logger.error(error_msg)

    return output_file

def process_config_modules(version, SenParameters):
    """
    Process all configuration modules (1-100) for all parameter variations.
    Apply sensitivity variations and save modified configurations.

    Args:
        version (int): Version number
        SenParameters (dict): Dictionary containing sensitivity parameters

    Returns:
        dict: Summary of processed modules and their status
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    processing_summary = {
        'total_found': 0,
        'total_modified': 0,
        'errors': [],
        'processed_modules': {},
        'csv_files_copied': 0,
        'py_files_copied': 0
    }


    try:
        # Import sensitivity functions from Sen_Config
        apply_sensitivity_variation, find_parameter_by_id = import_sensitivity_functions()

        # Source directory in ORIGINAL_BASE_DIR (root level)
        source_dir = os.path.join(ORIGINAL_BASE_DIR, f'Batch({version})', f'Results({version})')

        # Target directory in backend/Original
        target_base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        results_folder = os.path.join(target_base_dir, f'Batch({version})', f'Results({version})')
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        # Create ConfigurationPlotSpec directory at the same level as Results
        config_plot_spec_dir = os.path.join(target_base_dir, f'Batch({version})', f'ConfigurationPlotSpec({version})')
        os.makedirs(config_plot_spec_dir, exist_ok=True)
        sensitivity_logger.info(f"Created/ensured ConfigurationPlotSpec directory: {config_plot_spec_dir}")

        # 5-minute pause before looking for CSV files to ensure they exist
        sensitivity_logger.info("Starting 5-minute pause to ensure CSV files exist...")
        time.sleep(3)  # 5-minute pause to ensure files exist
        sensitivity_logger.info("Resuming after 5-minute pause, checking for CSV files...")

        # Define the specific CSV files we want to copy
        target_csv_files = [
            f"Configuration_Matrix({version}).csv",
            f"General_Configuration_Matrix({version}).csv"
        ]

        # Get the Python configuration file path
        code_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Original")
        config_file = os.path.join(code_files_path, f"Batch({version})", f"ConfigurationPlotSpec({version})", f"configurations({version}).py")

        # Filter to only existing files
        existing_csv_files = [
            f for f in target_csv_files
            if os.path.exists(os.path.join(source_dir, f))
        ]

        py_file_exists = os.path.exists(config_file)

        if len(existing_csv_files) < len(target_csv_files):
            missing_files = set(target_csv_files) - set(existing_csv_files)
            sensitivity_logger.warning(f"Some target CSV files not found even after pause: {missing_files}")
        if not py_file_exists:
            sensitivity_logger.warning(f"Python configuration file not found: {config_file}")

        # Process each parameter's variation directory
        for param_id, param_config in SenParameters.items():
            if not param_config.get('enabled'):
                continue

            # Get mode and values
            mode = param_config.get('mode', 'symmetrical')
            # Normalize mode terminology
            if mode in ['symmetrical', 'multiple']:
                normalized_mode = 'symmetrical'
            elif mode in ['discrete']:
                normalized_mode = 'multipoint'
            else:
                normalized_mode = mode.lower()

            values = param_config.get('values', [])

            if not values:
                continue

            sensitivity_logger.info(f"Processing parameter {param_id} with mode {normalized_mode}")

            # Determine variation list based on normalized mode
            if normalized_mode == 'symmetrical':
                base_variation = values[0]
                variation_list = [base_variation]
            else:  # 'multipoint'
                variation_list = values

            # Process each variation
            for variation in variation_list:
                var_str = f"{variation:+.2f}"
                param_var_dir = os.path.join(sensitivity_dir, param_id, normalized_mode, var_str)

                # Create directory if it doesn't exist
                os.makedirs(param_var_dir, exist_ok=True)
                sensitivity_logger.info(f"Processing variation {var_str} in directory: {param_var_dir}")

                # Copy only the specific CSV files we want
                for csv_file in existing_csv_files:
                    source_csv_path = os.path.join(source_dir, csv_file)
                    target_csv_path = os.path.join(param_var_dir, csv_file)
                    try:
                        shutil.copy2(source_csv_path, target_csv_path)
                        processing_summary['csv_files_copied'] += 1
                        sensitivity_logger.info(f"Copied specific CSV file: {csv_file}")
                    except Exception as e:
                        error_msg = f"Failed to copy CSV file {csv_file}: {str(e)}"
                        sensitivity_logger.error(error_msg)
                        processing_summary['errors'].append(error_msg)

                # Copy the Python configuration file if it exists
                # Now copying to the new ConfigurationPlotSpec directory
                if py_file_exists:
                    # Copy to parameter variation directory
                    target_py_path = os.path.join(param_var_dir, os.path.basename(config_file))
                    try:
                        shutil.copy2(config_file, target_py_path)
                        processing_summary['py_files_copied'] += 1
                        sensitivity_logger.info(f"Copied Python configuration file to variation dir: {os.path.basename(config_file)}")
                    except Exception as e:
                        error_msg = f"Failed to copy Python configuration file to variation dir: {str(e)}"
                        sensitivity_logger.error(error_msg)
                        processing_summary['errors'].append(error_msg)

                    # Also copy to the main ConfigurationPlotSpec directory
                    config_plot_spec_py_path = os.path.join(config_plot_spec_dir, os.path.basename(config_file))
                    try:
                        shutil.copy2(config_file, config_plot_spec_py_path)
                        sensitivity_logger.info(f"Copied Python configuration file to main ConfigurationPlotSpec dir: {config_plot_spec_py_path}")
                    except Exception as e:
                        error_msg = f"Failed to copy Python configuration file to ConfigurationPlotSpec dir: {str(e)}"
                        sensitivity_logger.error(error_msg)
                        processing_summary['errors'].append(error_msg)

                # Track modules for this parameter variation
                param_key = f"{param_id}_{var_str}"
                if param_key not in processing_summary['processed_modules']:
                    processing_summary['processed_modules'][param_key] = []

                # Process all possible module files (1-100)
                for module_num in range(1, 101):
                    source_config_path = os.path.join(source_dir, f"{version}_config_module_{module_num}.json")
                    target_config_path = os.path.join(param_var_dir, f"{version}_config_module_{module_num}.json")

                    # Skip if source JSON file doesn't exist
                    if not os.path.exists(source_config_path):
                        continue

                    processing_summary['total_found'] += 1

                    try:
                        # Load the source config module
                        with open(source_config_path, 'r') as f:
                            config_module = json.load(f)

                        # Apply sensitivity variation to the config
                        modified_config = apply_sensitivity_variation(
                            copy.deepcopy(config_module),
                            param_id,
                            variation,
                            normalized_mode
                        )

                        # Save the modified config
                        with open(target_config_path, 'w') as f:
                            json.dump(modified_config, f, indent=4)

                        processing_summary['total_modified'] += 1
                        processing_summary['processed_modules'][param_key].append(module_num)
                        sensitivity_logger.info(
                            f"Applied {variation}{'%' if normalized_mode == 'symmetrical' else ''} "
                            f"variation to config module {module_num} for {param_id}"
                        )

                    except Exception as e:
                        error_msg = f"Failed to process config module {module_num} for {param_id}, variation {var_str}: {str(e)}"
                        sensitivity_logger.error(error_msg)
                        processing_summary['errors'].append(error_msg)

        sensitivity_logger.info(
            f"Config module processing completed: "
            f"found {processing_summary['total_found']} JSON files, "
            f"modified {processing_summary['total_modified']} JSON files, "
            f"copied {processing_summary['csv_files_copied']} specific CSV files, "
            f"copied {processing_summary['py_files_copied']} Python configuration files"
        )

        if processing_summary['errors']:
            sensitivity_logger.warning(f"Encountered {len(processing_summary['errors'])} errors during processing")

        # Generate the SensitivityPlotDatapoints_{version}.json file
        sensitivity_logger.info("Generating SensitivityPlotDatapoints_{version}.json file with actual base values...")
        datapoints_file = generate_sensitivity_datapoints(version, SenParameters)
        sensitivity_logger.info(f"SensitivityPlotDatapoints generation completed: {datapoints_file}")

        return processing_summary

    except Exception as e:
        error_msg = f"Error in config module processing: {str(e)}"
        sensitivity_logger.exception(error_msg)
        processing_summary['errors'].append(error_msg)
        return processing_summary


def check_sensitivity_config_status():
    """
    Check if sensitivity configurations have been generated and saved.

    Returns:
        tuple: (is_configured, config_data) - Boolean indicating if configurations are ready and the configuration data
    """
    if not os.path.exists(SENSITIVITY_CONFIG_STATUS_PATH):
        return False, None

    try:
        with open(SENSITIVITY_CONFIG_STATUS_PATH, 'r') as f:
            status = json.load(f)

        if not status.get('configured', False):
            return False, None

        if os.path.exists(SENSITIVITY_CONFIG_DATA_PATH):
            with open(SENSITIVITY_CONFIG_DATA_PATH, 'rb') as f:
                config_data = pickle.load(f)
            return True, config_data

        return True, None

    except Exception as e:
        logging.error(f"Error checking sensitivity configuration status: {str(e)}")
        return False, None

# =====================================
# Flask Application Initialization
# =====================================

def initialize_app():
    app = Flask(__name__)
    CORS(app)
    setup_logging()
    return app

app = initialize_app()

# =====================================
# Route Handlers
# =====================================

@app.route('/copy-config-modules', methods=['POST'])
def copy_config_modules():
    """Endpoint to process all configuration modules with sensitivity variations."""
    sensitivity_logger = logging.getLogger('sensitivity')
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        # Check if sensitivity configurations exist
        is_configured, saved_config = check_sensitivity_config_status()

        if not is_configured:
            return jsonify({
                "error": "Sensitivity configurations must be generated first",
                "nextStep": "Call /sensitivity/configure endpoint first"
            }), 400

        # Get version from the saved configuration or request body
        request_data = request.get_json() or {}
        version = request_data.get('version') or saved_config['versions'][0]

        # Get sensitivity parameters
        sen_parameters = request_data.get('parameters') or saved_config['SenParameters']

        # Execute the processing operation
        processing_summary = process_config_modules(
            version,
            sen_parameters
        )

        return jsonify({
            "status": "success",
            "message": "Config module processing completed successfully",
            "runId": run_id,
            "summary": processing_summary
        })

    except Exception as e:
        error_msg = f"Error during config module processing: {str(e)}"
        sensitivity_logger.error(error_msg)
        return jsonify({
            "error": error_msg,
            "runId": run_id
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for server detection.
    Returns a 200 OK response with basic server information.
    """
    return jsonify({
        "status": "ok",
        "server": "sensitivity-config-processor",
        "version": "1.1.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

# =====================================
# Application Entry Point
# =====================================

if __name__ == '__main__':
    app.run(debug=True, port=2600)