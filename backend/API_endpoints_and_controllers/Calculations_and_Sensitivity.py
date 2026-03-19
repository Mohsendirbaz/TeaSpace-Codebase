"""
Sensitivity Visualization Flask API
Provides endpoints for sensitivity analysis configuration, execution, and visualization.
Integrates with the PlotsTabs and SensitivityPlotsTabs frontend components.
"""
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import subprocess
import os
import logging
import json
import time
import sys
import shutil
import pickle
import requests
import glob
import re
import pandas as pd
from Sensitivity_monitor import create_sensitivity_stream_endpoint

# Base directories setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_DIR = os.path.join(BASE_DIR, 'backend')
LOGS_DIR = os.path.join(SCRIPT_DIR, 'Logs')
ORIGINAL_BASE_DIR = os.path.join(BASE_DIR, 'backend', 'Original')

# Create logs directory if it doesn't exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Log file paths
LOG_FILE_PATH = os.path.join(LOGS_DIR, "RUN.log")
SENSITIVITY_LOG_PATH = os.path.join(LOGS_DIR, "SENSITIVITY.log")

# Sensitivity configuration status file paths
SENSITIVITY_CONFIG_STATUS_PATH = os.path.join(LOGS_DIR, "sensitivity_config_status.json")
SENSITIVITY_CONFIG_DATA_PATH = os.path.join(LOGS_DIR, "sensitivity_config_data.pkl")
# Configure logger
logger = logging.getLogger('sensitivity')
# Import needed modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import sensitivity logging functions if available
try:
    from sensitivity_logging import (
        log_plot_generation_start, log_plot_generation_complete, log_plot_generation_error,
        log_plot_data_loading, log_plot_data_processing, log_plot_rendering, log_plot_saving,
        plot_generation_operation, log_execution_flow
    )
except ImportError:
    # Create dummy logging functions if module not available
    def log_execution_flow(stage, message): logging.info(f"{stage}: {message}")
    def log_plot_generation_start(*args): logging.info(f"Plot generation start: {args}")
    def log_plot_generation_complete(*args): logging.info(f"Plot generation complete: {args}")
    def log_plot_generation_error(*args): logging.info(f"Plot generation error: {args}")
    def log_plot_data_loading(*args, **kwargs): logging.info(f"Plot data loading: {args}")
    def log_plot_data_processing(*args): logging.info(f"Plot data processing: {args}")
    def log_plot_rendering(*args, **kwargs): logging.info(f"Plot rendering: {args}")
    def log_plot_saving(*args): logging.info(f"Plot saving: {args}")
    def plot_generation_operation(*args, **kwargs): return lambda x: x

# Script configurations
COMMON_PYTHON_SCRIPTS = [
    os.path.join(SCRIPT_DIR, "Configuration_management", 'formatter.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'module1.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'config_modules.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'Table.py')
]

def get_calculation_script(version):
    """Get the appropriate calculation script based on version number"""
    script_name = f'CFA.py'
    script_path = os.path.join(SCRIPT_DIR, "Core_calculation_engines", script_name)
    if os.path.exists(script_path):
        return script_path
    raise Exception(f"Calculation script not found for version {version}")

def get_sensitivity_calculation_script():
    """Get the CFA-b.py script for sensitivity analysis"""
    script_path = os.path.join(SCRIPT_DIR, "Core_calculation_engines", "CFA-b.py")
    if os.path.exists(script_path):
        return script_path
    raise Exception("CFA-b.py script not found for sensitivity calculations")

CALCULATION_SCRIPTS = {
    'calculateForPrice': get_calculation_script,
    'calculateForPrice': get_calculation_script
}

# =====================================
# Logging Configuration
# =====================================

def setup_logging():
    """Configure application logging with separate handlers for main and sensitivity logs"""
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Clear any existing handlers
    logging.getLogger().handlers = []
    logging.getLogger('sensitivity').handlers = []

    # Configure main application logger (root logger)
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

    # Only log the configuration messages once
    if not main_logger.handlers or not sensitivity_logger.handlers:
        main_logger.info("Logging configured correctly - Main logs going to: " + LOG_FILE_PATH)
        sensitivity_logger.info("Sensitivity logging configured correctly - Logs going to: " + SENSITIVITY_LOG_PATH)

# =====================================
# Helper Functions
# =====================================

def trigger_config_module_copy(version, sensitivity_dir, sen_parameters):
    """
    Triggers the independent config module copy service.

    Args:
        version (int): Version number
        sensitivity_dir (str): Path to sensitivity directory
        sen_parameters (dict): Sensitivity parameters

    Returns:
        dict: Response from the config copy service
    """
    sensitivity_logger = logging.getLogger('sensitivity')

    try:
        sensitivity_logger.info("Triggering config module copy service on port 2600...")
        response = requests.post(
            "http://localhost:2600/copy-config-modules",
            json={
                "version": version,
                "sensitivity_dir": sensitivity_dir,
                "parameters": sen_parameters
            },
            timeout=10  # Initial connection timeout
        )

        if response.status_code == 200:
            result = response.json()
            sensitivity_logger.info(f"Config copy service triggered successfully: {result.get('message')}")
            return result
        else:
            error_msg = f"Error triggering config copy service: {response.text}"
            sensitivity_logger.error(error_msg)
            return {"error": error_msg}

    except requests.exceptions.ConnectionError:
        sensitivity_logger.warning("Config copy service not running or unreachable")
        return {"error": "Config copy service not available"}
    except Exception as e:
        error_msg = f"Error connecting to config copy service: {str(e)}"
        sensitivity_logger.error(error_msg)
        return {"error": error_msg}

def log_run_configuration(logger, config):
    """Log run configuration in a structured format"""
    logger.info("\n" + "="*80)
    logger.info("CFA Run Configuration")
    logger.info("="*80)

    # Basic Configuration
    logger.info("\nBasic Configuration:")
    logger.info(f"Version(s): {', '.join(map(str, config['versions']))}")
    logger.info(f"Calculation Mode: {config['calculationOption']}")
    if config['calculationOption'] == 'calculateForPrice':
        logger.info(f"Target Row: {config['targetRow']}")

    # Parameter States
    logger.info("\nParameter States:")
    v_enabled = [k for k, v in config['selectedV'].items() if v == 'on']
    f_enabled = [k for k, v in config['selectedF'].items() if v == 'on']
    logger.info(f"Enabled V Parameters: {', '.join(v_enabled) if v_enabled else 'None'}")
    logger.info(f"Enabled F Parameters: {', '.join(f_enabled) if f_enabled else 'None'}")

    # Sensitivity Configuration (if enabled)
    enabled_params = [k for k, v in config['SenParameters'].items() if v.get('enabled')]
    if enabled_params:
        logger.info("\nSensitivity Analysis Configuration:")
        logger.info(f"Enabled Parameters: {', '.join(enabled_params)}")
        for param_id in enabled_params:
            param_config = config['SenParameters'][param_id]
            logger.info(f"\n{param_id} Configuration:")
            logger.info(f"  Mode: {param_config.get('mode')}")
            logger.info(f"  Values: {param_config.get('values')}")
            if param_config.get('compareToKey'):
                logger.info(f"  Comparison:")
                logger.info(f"    Target: {param_config['compareToKey']}")
                logger.info(f"    Type: {param_config.get('comparisonType', 'primary')}")
                plot_types = []
                if param_config.get('waterfall'): plot_types.append('waterfall')
                if param_config.get('bar'): plot_types.append('bar')
                if param_config.get('point'): plot_types.append('point')
                logger.info(f"    Plot Types: {', '.join(plot_types)}")

    logger.info("\n" + "="*80 + "\n")

def create_sensitivity_directories(version, SenParameters):
    """
    Create comprehensive directory structure for sensitivity analysis.

    Args:
        version (int): Version number
        SenParameters (dict): Dictionary containing sensitivity parameters

    Returns:
        tuple: (sensitivity_dir, reports_dir) - Paths to directories
    """
    sensitivity_logger = logging.getLogger('sensitivity')

    # Define base paths
    base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
    results_folder = os.path.join(base_dir, f'Batch({version})', f'Results({version})')
    sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

    # Create main sensitivity directory
    os.makedirs(sensitivity_dir, exist_ok=True)
    sensitivity_logger.info(f"Created main sensitivity directory: {sensitivity_dir}")

    # Create standard subdirectories
    for subdir in ["Reports", "Cache", "Configuration"]:
        path = os.path.join(sensitivity_dir, subdir)
        os.makedirs(path, exist_ok=True)
        sensitivity_logger.info(f"Created {subdir} directory: {path}")

    reports_dir = os.path.join(sensitivity_dir, "Reports")

    # Create mode directories for all supported modes
    mode_dir_mapping = {
        'percentage': 'Percentage',
        'directvalue': 'DirectValue',
        'absolutedeparture': 'AbsoluteDeparture',
        'montecarlo': 'MonteCarlo'
    }

    # Create standard directories for each mode
    for mode_name in mode_dir_mapping.values():
        mode_dir = os.path.join(sensitivity_dir, mode_name)
        os.makedirs(mode_dir, exist_ok=True)
        sensitivity_logger.info(f"Created mode directory: {mode_dir}")

        # Create plot type subdirectories
        for plot_type in ["waterfall", "bar", "point", "Configuration"]:
            plot_type_dir = os.path.join(mode_dir, plot_type)
            os.makedirs(plot_type_dir, exist_ok=True)
            sensitivity_logger.info(f"Created plot type directory: {plot_type_dir}")

    # Process each parameter
    enabled_params = [(param_id, config) for param_id, config in SenParameters.items()
                      if config.get('enabled')]

    for param_id, param_config in enabled_params:
        # Skip disabled parameters
        if not param_config.get('enabled'):
            continue

        # Get parameter details
        mode = param_config.get('mode', 'percentage')
        values = param_config.get('values', [])
        plot_types = []

        if param_config.get('waterfall'): plot_types.append('waterfall')
        if param_config.get('bar'): plot_types.append('bar')
        if param_config.get('point'): plot_types.append('point')

        if not values:
            continue

        # Create parameter base directory
        param_dir = os.path.join(sensitivity_dir, param_id)
        os.makedirs(param_dir, exist_ok=True)

        # Create mode directory within parameter (lowercase mode)
        param_mode_dir = os.path.join(param_dir, mode.lower())
        os.makedirs(param_mode_dir, exist_ok=True)

        # Use values directly from configuration without special handling
        variation_list = values

        # Create variation directories
        for variation in variation_list:
            var_str = f"{variation:+.2f}"

            # 1. Create parameter variation directories
            var_dir = os.path.join(param_dir, mode.lower(), var_str)
            os.makedirs(var_dir, exist_ok=True)
            sensitivity_logger.info(f"Created parameter variation directory: {var_dir}")

            # 2. Create configuration variation directories
            # Map to the proper capitalized mode directory
            mode_cap = mode_dir_mapping.get(mode.lower(), 'Percentage')
            config_var_dir = os.path.join(sensitivity_dir, mode_cap, "Configuration", f"{param_id}_{var_str}")
            os.makedirs(config_var_dir, exist_ok=True)
            sensitivity_logger.info(f"Created configuration directory: {config_var_dir}")

        # Create plot type directories for this parameter
        # Map to the proper capitalized mode directory
        mode_cap = mode_dir_mapping.get(mode.lower(), 'Percentage')

        for plot_type in plot_types:
            plot_dir = os.path.join(sensitivity_dir, mode_cap, plot_type, f"{param_id}_{plot_type}")
            os.makedirs(plot_dir, exist_ok=True)
            sensitivity_logger.info(f"Created plot directory: {plot_dir}")

    return sensitivity_dir, reports_dir

def save_sensitivity_config_files(version, reports_dir, SenParameters):
    """
    Save sensitivity configuration files to the appropriate directories.

    Args:
        version (int): Version number
        reports_dir (str): Path to the reports directory
        SenParameters (dict): Dictionary containing sensitivity parameters

    Returns:
        list: List of saved configuration file paths
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    saved_files = []

    try:
        # Get base directory
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        results_folder = os.path.join(base_dir, f'Batch({version})', f'Results({version})')
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        # Save main configuration file in reports directory
        config_file = os.path.join(reports_dir, "sensitivity_config.json")
        with open(config_file, 'w') as f:
            json.dump({
                'version': version,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'parameters': SenParameters
            }, f, indent=2)
        saved_files.append(config_file)
        sensitivity_logger.info(f"Saved main configuration file: {config_file}")

        # Save individual parameter configuration files in their respective directories
        for param_id, param_config in SenParameters.items():
            if not param_config.get('enabled'):
                continue

            # Get mode and values
            mode = param_config.get('mode', 'percentage')
            values = param_config.get('values', [])

            if not values:
                continue

            # Use the values directly based on the mode
            variation_list = values

            # Save configuration for each variation
            for variation in variation_list:
                # Format the variation string (e.g., "+10.00" or "-5.00")
                var_str = f"{variation:+.2f}"

                # Create path to variation directory
                var_dir = os.path.join(sensitivity_dir, param_id, mode.lower(), var_str)

                # Save configuration file
                param_file = os.path.join(var_dir, f"{param_id}_config.json")
                with open(param_file, 'w') as f:
                    json.dump({
                        'parameter': param_id,
                        'config': param_config,
                        'variation': variation,
                        'variation_str': var_str,
                        'mode': mode,
                        'version': version,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    }, f, indent=2)
                saved_files.append(param_file)
                sensitivity_logger.info(f"Saved parameter configuration file: {param_file}")
                # Configuration variation directories are created with 2 minutes pause via flask at 2600

        return saved_files

    except Exception as e:
        error_msg = f"Error saving configuration files: {str(e)}"
        sensitivity_logger.exception(error_msg)
        raise

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

def get_sensitivity_data(version, param_id, mode, compare_to_key):
    """
    Retrieve sensitivity analysis data for visualization.

    Args:
        version (int): Version number
        param_id (str): Parameter ID
        mode (str): Sensitivity mode (percentage, directvalue, absolutedeparture, montecarlo)
        compare_to_key (str): Comparison parameter

    Returns:
        dict: Sensitivity data including variations and values
    """
    # Map mode to directory name
    mode_dir_mapping = {
        'percentage': 'Percentage',
        'directvalue': 'DirectValue',
        'absolutedeparture': 'AbsoluteDeparture',
        'montecarlo': 'MonteCarlo'
    }
    mode_dir = mode_dir_mapping.get(mode.lower(), 'Percentage')

    # Build path to results file
    base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
    results_path = os.path.join(
        base_dir,
        f'Batch({version})',
        f'Results({version})',
        'Sensitivity',
        mode_dir,
        f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
    )

    # Check if results file exists
    if not os.path.exists(results_path):
        logger.warning(f"Results file not found: {results_path}")
        return None

    # Load results data
    try:
        with open(results_path, 'r') as f:
            results_data = json.load(f)
        return results_data
    except Exception as e:
        logger.error(f"Error loading results data: {str(e)}")
        return None
app = Flask(__name__)
CORS(app)

# Register the sensitivity stream endpoint
create_sensitivity_stream_endpoint(app)
setup_logging()

# =====================================
# Sensitivity Configuration Endpoint
# =====================================

@app.route('/sensitivity/configure', methods=['POST'])
def configure_sensitivity():
    """
    Generate and save sensitivity configurations with their applied variations.
    This must be called before running sensitivity calculations.
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract configuration
        config = {
            'versions': data.get('selectedVersions', [1]),
            'selectedV': data.get('selectedV', {f'V{i+1}': 'off' for i in range(10)}),
            'selectedF': data.get('selectedF', {f'F{i+1}': 'off' for i in range(5)}),
            'calculationOption': data.get('selectedCalculationOption', 'calculateForPrice'),
            'targetRow': int(data.get('targetRow', 20)),
            'SenParameters': data.get('SenParameters', {})
        }

        version = config['versions'][0]

        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Sensitivity Configuration Generation - Run ID: {run_id}")
        sensitivity_logger.info(f"{'='*80}")
        sensitivity_logger.info(f"Version: {version}")
        sensitivity_logger.info(f"Calculation Mode: {config['calculationOption']}")
        sensitivity_logger.info(f"Target Row: {config['targetRow']}")

        # Create sensitivity directories
        sensitivity_dir, config_dir = create_sensitivity_directories(version, config['SenParameters'])

        # Log run configuration
        log_run_configuration(sensitivity_logger, config)

        # Save configuration files
        saved_files = save_sensitivity_config_files(version, config_dir, config['SenParameters'])

        # Trigger config module copy service - MOVED FROM /runs to here
        sensitivity_logger.info("\nTriggering configuration module copying:")
        copy_service_result = trigger_config_module_copy(
            version,
            sensitivity_dir,
            config['SenParameters']
        )

        # If CalSen service is available, prepare paths
        calsen_result = None
        try:
            sensitivity_logger.info("Preparing path configurations with CalSen service...")
            cal_sen_response = requests.post(
                "http://localhost:2750/get_config_paths",
                json={
                    "version": version,
                    "payload": config
                },
                timeout=5
            )

            if cal_sen_response.status_code == 200:
                calsen_result = cal_sen_response.json()
                sensitivity_logger.info(f"CalSen paths prepared: {len(calsen_result.get('path_sets', {}))} configurations")

                # Save path sets for later use
                calsen_paths_file = os.path.join(config_dir, "calsen_paths.json")
                with open(calsen_paths_file, 'w') as f:
                    json.dump(calsen_result, f, indent=2)
            else:
                sensitivity_logger.warning("CalSen service did not return valid path sets")

        except requests.exceptions.RequestException:
            sensitivity_logger.warning("CalSen service not available")

        # Save configuration status
        with open(SENSITIVITY_CONFIG_STATUS_PATH, 'w') as f:
            json.dump({
                'configured': True,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'runId': run_id,
                'version': version,
                'configDir': config_dir,
                'sensitivityDir': sensitivity_dir,
                'configCopyInitiated': True,
                'configCopyResult': copy_service_result,
                'calsenResult': calsen_result is not None
            }, f, indent=2)

        # Save configuration data for later use
        with open(SENSITIVITY_CONFIG_DATA_PATH, 'wb') as f:
            pickle.dump(config, f)

        sensitivity_logger.info(f"\nSensitivity configuration completed successfully")
        sensitivity_logger.info(f"Configuration files saved: {len(saved_files)}")
        sensitivity_logger.info(f"Configuration status saved to: {SENSITIVITY_CONFIG_STATUS_PATH}")
        sensitivity_logger.info(f"{'='*80}\n")

        return jsonify({
            "status": "success",
            "message": "Sensitivity configurations generated and saved successfully",
            "runId": run_id,
            "configDir": config_dir,
            "sensitivityDir": sensitivity_dir,
            "savedFiles": len(saved_files),
            "configCopy": copy_service_result,
            "calsen": calsen_result is not None,
            "nextStep": "Visit /runs to execute sensitivity calculations"
        })

    except Exception as e:
        error_msg = f"Error generating sensitivity configurations: {str(e)}"
        sensitivity_logger.error(error_msg)

        # Update configuration status to indicate failure
        with open(SENSITIVITY_CONFIG_STATUS_PATH, 'w') as f:
            json.dump({
                'configured': False,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'runId': run_id,
                'error': error_msg
            }, f, indent=2)

        return jsonify({
            "error": error_msg,
            "runId": run_id
        }), 500

# =====================================
# Run Calculations Endpoint
# =====================================

@app.route('/runs', methods=['POST'])
def run_calculations():
    """Orchestrates the execution sequence of configuration updates and calculations."""
    sensitivity_logger = logging.getLogger('sensitivity')
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        # Check if sensitivity configurations have been generated
        is_configured, saved_config = check_sensitivity_config_status()

        # If sensitivity configurations haven't been generated, return an error
        if not is_configured:
            sensitivity_logger.warning("Sensitivity configurations have not been generated yet")
            return jsonify({
                "error": "Sensitivity configurations must be generated first",
                "message": "Please call /sensitivity/configure endpoint to generate and save sensitivity configurations before running calculations",
                "nextStep": "Call /sensitivity/configure endpoint first"
            }), 400

        # Use the saved configuration data if available, otherwise use the request data
        data = request.get_json()
        if saved_config:
            config = saved_config
            sensitivity_logger.info("Using saved sensitivity configuration data")
        elif data:
            config = {
                'versions': data.get('selectedVersions', [1]),
                'selectedV': data.get('selectedV', {f'V{i+1}': 'off' for i in range(10)}),
                'selectedF': data.get('selectedF', {f'F{i+1}': 'off' for i in range(5)}),
                'calculationOption': data.get('selectedCalculationOption', 'calculateForPrice'),
                'targetRow': int(data.get('targetRow', 20)),
                'SenParameters': data.get('SenParameters', {})
            }
            sensitivity_logger.info("Using request data for configuration")
        else:
            return jsonify({"error": "No configuration data available"}), 400

        # Extract year columns config from form values
        year_columns_config = {}
        form_values = data.get('formValues', {})
        amount10_keys = [k for k in form_values if isinstance(k, str) and 'Amount10' in k]
        if amount10_keys and form_values.get(amount10_keys[0]):
            try:
                value = form_values[amount10_keys[0]].get('value')
                if value:
                    year_columns = int(value)
                    for version in config['versions']:
                        year_columns_config[str(version)] = year_columns
                    sensitivity_logger.info(f"Year columns configuration set to {year_columns} for all versions")
            except (ValueError, TypeError, AttributeError) as e:
                sensitivity_logger.warning(f"Error extracting year columns config: {e}")

        # Get version and paths
        version = config['versions'][0]
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        results_folder = os.path.join(base_dir, f'Batch({version})', f'Results({version})')
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        # Verify that sensitivity directories exist
        if not os.path.exists(sensitivity_dir):
            error_msg = f"Sensitivity directory not found: {sensitivity_dir}"
            sensitivity_logger.error(error_msg)
            return jsonify({
                "error": error_msg,
                "message": "Please call /sensitivity/configure endpoint to generate and save sensitivity configurations",
                "nextStep": "Call /sensitivity/configure endpoint first"
            }), 400

        sensitivity_logger.info(f"Using sensitivity directory: {sensitivity_dir}")

        # Log run configuration
        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Sensitivity Calculation Run - ID: {run_id}")
        sensitivity_logger.info(f"{'='*80}")
        log_run_configuration(sensitivity_logger, config)

        # Execute configuration management scripts
        sensitivity_logger.info("\nExecuting Configuration Management Scripts:")
        start_time = time.time()

        for script in COMMON_PYTHON_SCRIPTS:
            script_name = os.path.basename(script)
            script_start = time.time()
            sensitivity_logger.info(f"\nExecuting: {script_name}")

            result = subprocess.run(
                ['python', script, str(version)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = f"Script execution failed: {script_name}\nError: {result.stderr}"
                sensitivity_logger.error(error_msg)
                raise Exception(error_msg)

            script_duration = time.time() - script_start
            sensitivity_logger.info(f"Completed {script_name} in {script_duration:.2f}s")
            time.sleep(0.5)  # Ensure proper sequencing

        config_time = time.time() - start_time
        sensitivity_logger.info(f"\nConfiguration scripts completed in {config_time:.2f}s")

        # Step 2: Process baseline calculation
        sensitivity_logger.info("\nProcessing Baseline Calculation:")
        calc_start = time.time()

        # Get calculation script
        calculation_script_func = CALCULATION_SCRIPTS.get(config['calculationOption'])
        if not calculation_script_func:
            raise Exception(f"No script found for calculation mode: {config['calculationOption']}")

        calculation_script = calculation_script_func(config['versions'][0])
        sensitivity_logger.info(f"Using calculation script: {os.path.basename(calculation_script)}")

        # Run baseline calculation first
        sensitivity_logger.info("\nExecuting baseline calculation:")
        result = subprocess.run(
            [
                'python',
                calculation_script,
                str(config['versions'][0]),
                json.dumps(config['selectedV']),
                json.dumps(config['selectedF']),
                str(config['targetRow']),
                config['calculationOption'],
                '{}'  # Empty SenParameters for baseline
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            error_msg = f"Baseline calculation failed: {result.stderr}"
            sensitivity_logger.error(error_msg)
            raise Exception(error_msg)

        sensitivity_logger.info("Baseline calculation completed successfully")

        # Step 3: Check if config files are already being copied
        sensitivity_logger.info("\nChecking configuration module copy status:")
        status_data = {}

        if os.path.exists(SENSITIVITY_CONFIG_STATUS_PATH):
            with open(SENSITIVITY_CONFIG_STATUS_PATH, 'r') as f:
                status_data = json.load(f)

        if status_data.get('configCopyInitiated'):
            sensitivity_logger.info("Configuration copying was already initiated during configuration step")
            copy_service_result = status_data.get('configCopyResult', {})
        else:
            # Fallback: trigger the config copy if not done during configure step
            sensitivity_logger.info("Configuration copying was not initiated - triggering now")
            copy_service_result = trigger_config_module_copy(
                version,
                sensitivity_dir,
                config['SenParameters']
            )

        # Verify that actual configuration files have been created
        sensitivity_logger.info("Verifying configuration files existence...")
        config_files_verified = False
        wait_duration = 180  # 3 minutes
        start_wait = time.time()

        while time.time() - start_wait < wait_duration:
            # Check for actual configuration files for each enabled parameter
            all_found = True
            for param_id, param_config in config['SenParameters'].items():
                if not param_config.get('enabled'):
                    continue

                mode = param_config.get('mode', 'percentage')
                values = param_config.get('values', [])

                # Use the values directly based on mode
                variation_list = values

                # Check if configuration files exist for each variation
                for variation in variation_list:
                    var_str = f"{variation:+.2f}"
                    config_path_pattern = os.path.join(
                        sensitivity_dir,
                        param_id,
                        mode.lower(),
                        var_str,
                        f"{version}_config_module_*.json"
                    )

                    if not glob.glob(config_path_pattern):
                        all_found = False
                        sensitivity_logger.info(f"Still waiting for config files for {param_id} variation {var_str}...")
                        break

                if not all_found:
                    break

            if all_found:
                config_files_verified = True
                sensitivity_logger.info("All required configuration files verified!")
                break

            # Log progress and wait
            elapsed = time.time() - start_wait
            sensitivity_logger.info(f"Still waiting for configuration files... ({elapsed:.0f}s elapsed)")
            time.sleep(15)  # Check every 15 seconds

        if not config_files_verified:
            sensitivity_logger.warning("Timed out waiting for all configuration files, proceeding anyway")

        # Update configuration pickle file to ensure version matching for subsequent steps
        sensitivity_logger.info("Updating configuration data with current version...")
        try:
            # Save configuration data with explicit version for process_sensitivity_results.py to use
            with open(SENSITIVITY_CONFIG_DATA_PATH, 'wb') as f:
                # Ensure version is correctly saved in the configuration
                if isinstance(config['versions'], list) and version not in config['versions']:
                    config['versions'].append(version)
                pickle.dump(config, f)
            sensitivity_logger.info(f"Updated configuration data with version {version}")
        except Exception as e:
            sensitivity_logger.error(f"Error updating configuration data: {str(e)}")

        # Step 4: Process sensitivity parameters with the updated process_sensitivity_calculations function
        enabled_params = [k for k, v in config['SenParameters'].items() if v.get('enabled')]
        if enabled_params:
            sensitivity_logger.info(f"\nProcessing {len(enabled_params)} enabled sensitivity parameters...")

            # Note: Actual sensitivity calculations will be performed separately by the /calculate-sensitivity endpoint
            sensitivity_logger.info("Initial run completed. For detailed parameter calculations, use the /calculate-sensitivity endpoint.")

        total_time = time.time() - start_time
        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Run Summary - ID: {run_id}")
        sensitivity_logger.info(f"Total execution time: {total_time:.2f}s")
        sensitivity_logger.info(f"Configuration scripts: {config_time:.2f}s")
        sensitivity_logger.info(f"Configurations processed: {len(enabled_params)}")
        sensitivity_logger.info(f"{'='*80}\n")

        # Return success response with timing information and year columns
        return jsonify({
            "status": "success",
            "message": "Calculations completed successfully",
            "runId": run_id,
            "timing": {
                "total": f"{total_time:.2f}s",
                "configuration": f"{config_time:.2f}s",
                "calculations": len(enabled_params) + 1
            },
            "configCopy": copy_service_result,
            "yearColumns": year_columns_config
        })

    except Exception as e:
        error_msg = f"Error during orchestrated calculations: {str(e)}"
        sensitivity_logger.error(error_msg)
        return jsonify({
            "error": error_msg,
            "runId": run_id
        }), 500

# =====================================
# Baseline Calculation Endpoint
# =====================================

@app.route('/run-baseline', methods=['POST'])
def run_baseline():
    """Endpoint dedicated to baseline calculations only"""
    sensitivity_logger = logging.getLogger('sensitivity')
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract configuration matching the /runs endpoint pattern
        config = {
            'versions': data.get('selectedVersions', [1]),
            'selectedV': data.get('selectedV', {f'V{i+1}': 'off' for i in range(10)}),
            'selectedF': data.get('selectedF', {f'F{i+1}': 'off' for i in range(5)}),
            'calculationOption': data.get('selectedCalculationOption', 'calculateForPrice'),
            'targetRow': int(data.get('targetRow', 20)),
            'SenParameters': {}  # Empty SenParameters for baseline
        }

        version = config['versions'][0]
        calculation_option = config['calculationOption']
        target_row = config['targetRow']

        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Baseline Calculation - Run ID: {run_id}")
        sensitivity_logger.info(f"{'='*80}")
        sensitivity_logger.info(f"Version: {version}")
        sensitivity_logger.info(f"Calculation Mode: {calculation_option}")
        sensitivity_logger.info(f"Target Row: {target_row}")

        # Execute configuration management scripts (same as /runs endpoint)
        sensitivity_logger.info("\nExecuting Configuration Management Scripts:")
        start_time = time.time()

        for script in COMMON_PYTHON_SCRIPTS:
            script_name = os.path.basename(script)
            script_start = time.time()
            sensitivity_logger.info(f"\nExecuting: {script_name}")

            result = subprocess.run(
                ['python', script, str(version)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = f"Script execution failed: {script_name}\nError: {result.stderr}"
                sensitivity_logger.error(error_msg)
                raise Exception(error_msg)

            script_duration = time.time() - script_start
            sensitivity_logger.info(f"Completed {script_name} in {script_duration:.2f}s")
            time.sleep(0.5)  # Ensure proper sequencing

        config_time = time.time() - start_time
        sensitivity_logger.info(f"\nConfiguration scripts completed in {config_time:.2f}s")

        # Get calculation script (same as /runs endpoint)
        calculation_script_func = CALCULATION_SCRIPTS.get(calculation_option)
        if not calculation_script_func:
            raise Exception(f"No script found for calculation mode: {calculation_option}")

        calculation_script = calculation_script_func(version)
        sensitivity_logger.info(f"Using calculation script: {os.path.basename(calculation_script)}")

        # Run baseline calculation with the same pattern as /runs endpoint
        sensitivity_logger.info("\nExecuting baseline calculation:")
        result = subprocess.run(
            [
                'python',
                calculation_script,
                str(version),
                json.dumps(config['selectedV']),
                json.dumps(config['selectedF']),
                str(target_row),
                calculation_option,
                '{}'  # Empty SenParameters for baseline
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            error_msg = f"Baseline calculation failed: {result.stderr}"
            sensitivity_logger.error(error_msg)
            raise Exception(error_msg)

        sensitivity_logger.info("Baseline calculation completed successfully")

        total_time = time.time() - start_time
        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Run Summary - ID: {run_id}")
        sensitivity_logger.info(f"Total execution time: {total_time:.2f}s")
        sensitivity_logger.info(f"Configuration scripts: {config_time:.2f}s")
        sensitivity_logger.info(f"{'='*80}\n")

        return jsonify({
            "status": "success",
            "message": "Baseline calculation completed",
            "runId": run_id,
            "version": version,
            "timing": {
                "total": f"{total_time:.2f}s",
                "configuration": f"{config_time:.2f}s"
            }
        })

    except Exception as e:
        error_msg = f"Error during baseline calculation: {str(e)}"
        sensitivity_logger.error(error_msg)
        return jsonify({
            "error": error_msg,
            "runId": run_id
        }), 500

@app.route('/calculate-sensitivity', methods=['POST'])
def calculate_sensitivity():
    """
    Execute specific sensitivity calculations using CFA-b.py with paths from CalSen service (calsen_paths.json that will always be in Reports directory).
    This endpoint runs after the general sensitivity configurations and runs have completed.
    It leverages the CalSen service for path resolution to ensure consistent file locations.
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        # Check if sensitivity configurations have been generated
        is_configured, saved_config = check_sensitivity_config_status()

        if not is_configured:
            sensitivity_logger.warning("Sensitivity configurations have not been generated yet")
            return jsonify({
                "error": "Sensitivity configurations must be generated first",
                "message": "Please complete the /sensitivity/configure and /runs endpoints before calculating specific sensitivities",
                "nextStep": "Call /sensitivity/configure endpoint first"
            }), 400

        # Use the saved configuration data if available, otherwise use the request data
        data = request.get_json()
        if saved_config:
            config = saved_config
            sensitivity_logger.info("Using saved sensitivity configuration data")
        elif data:
            config = {
                'versions': data.get('selectedVersions', [1]),
                'selectedV': data.get('selectedV', {f'V{i+1}': 'off' for i in range(10)}),
                'selectedF': data.get('selectedF', {f'F{i+1}': 'off' for i in range(5)}),
                'calculationOption': data.get('selectedCalculationOption', 'calculateForPrice'),
                'targetRow': int(data.get('targetRow', 20)),
                'SenParameters': data.get('SenParameters', {})
            }
            sensitivity_logger.info("Using request data for configuration")
        else:
            return jsonify({"error": "No configuration data available"}), 400

        # Get version and base paths
        version = config['versions'][0]
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        results_folder = os.path.join(base_dir, f'Batch({version})', f'Results({version})')
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Parameter-Specific Sensitivity Calculations - Run ID: {run_id}")
        sensitivity_logger.info(f"{'='*80}")
        sensitivity_logger.info(f"Version: {version}")
        sensitivity_logger.info(f"Calculation Mode: {config['calculationOption']}")
        sensitivity_logger.info(f"Target Row: {config['targetRow']}")

        # Get CFA-b.py script path
        cfa_b_script = get_sensitivity_calculation_script()
        sensitivity_logger.info(f"Using calculation script: {os.path.basename(cfa_b_script)}")

        # Process enabled sensitivity parameters
        enabled_params = [(param_id, param_config) for param_id, param_config
                          in config['SenParameters'].items() if param_config.get('enabled')]

        if not enabled_params:
            sensitivity_logger.warning("No enabled sensitivity parameters found")
            return jsonify({
                "status": "warning",
                "message": "No enabled sensitivity parameters found for calculation",
                "runId": run_id
            })

        sensitivity_logger.info(f"Processing {len(enabled_params)} enabled parameters")

        # Results collection
        calculation_results = {}
        overall_success = True

        # Mode mapping for standardized directory names
        mode_dir_mapping = {
            'percentage': 'Percentage',
            'directvalue': 'DirectValue',
            'absolutedeparture': 'AbsoluteDeparture',
            'montecarlo': 'MonteCarlo'
        }

        # Process each parameter
        for param_id, param_config in enabled_params:
            mode = param_config.get('mode', 'percentage')
            values = param_config.get('values', [])
            compare_to_key = param_config.get('compareToKey', 'S13')

            if not values:
                sensitivity_logger.warning(f"No values specified for {param_id}, skipping")
                continue

            # Determine variations based on mode
            variations = []
            for value in values:
                if value is not None:
                    try:
                        variations.append(float(value))
                    except (ValueError, TypeError):
                        sensitivity_logger.warning(f"Invalid variation value in {param_id}: {value}")

            if not variations:
                sensitivity_logger.warning(f"No valid variation values for {param_id}, skipping")
                continue

            param_results = {"variations": {}, "success": True}

            # Process each variation
            for variation in variations:
                var_str = f"{variation:+.2f}"
                sensitivity_logger.info(f"Processing {param_id} variation {var_str}")

                try:
                    # Call CFA-b.py with CalSen paths
                    sensitivity_logger.info(f"Executing CFA-b.py for {param_id} variation {var_str}...")

                    # Prepare the environment variables to avoid division by zero errors
                    env = os.environ.copy()
                    env["PYTHONPATH"] = SCRIPT_DIR + os.pathsep + env.get("PYTHONPATH", "")

                    # Log the full command for debugging
                    command = [
                        'python',
                        cfa_b_script,
                        str(version),
                        json.dumps(config['selectedV']),
                        json.dumps(config['selectedF']),
                        str(config['targetRow']),
                        config['calculationOption'],
                        json.dumps({param_id: param_config}),
                        "--param_id", param_id,
                        "--variation", str(variation),
                        "--compare_to_key", compare_to_key,
                        "--mode", mode
                    ]
                    sensitivity_logger.info(f"Command: {' '.join(command)}")

                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        env=env,
                        cwd=SCRIPT_DIR  # Set working directory to script directory
                    )

                    # Log the output for debugging
                    if result.stdout:
                        sensitivity_logger.info(f"Command stdout: {result.stdout}")
                    if result.stderr:
                        sensitivity_logger.error(f"Command stderr: {result.stderr}")

                    if result.returncode == 0:
                        sensitivity_logger.info(f"Successfully calculated {param_id} variation {var_str}")
                        param_results["variations"][var_str] = {
                            "status": "success",
                            "message": "Calculation completed successfully"
                        }

                        # Try to extract economic summary for this variation
                        try:
                            # Map the mode to the standardized directory name
                            mode_cap = mode_dir_mapping.get(mode.lower(), 'Percentage')

                            # Check both possible locations for the economic summary
                            param_var_dir = os.path.join(
                                sensitivity_dir, param_id, mode.lower(), var_str
                            )
                            econ_summary_file = os.path.join(
                                param_var_dir, f"Economic_Summary({version}).csv"
                            )

                            # If not found, try the mode directory
                            if not os.path.exists(econ_summary_file):
                                econ_summary_file = os.path.join(
                                    sensitivity_dir, mode_cap, "Configuration",
                                    f"{param_id}_{var_str}", f"Economic_Summary({version}).csv"
                                )

                            if os.path.exists(econ_summary_file):
                                # Read economic summary and extract relevant information
                                econ_df = pd.read_csv(econ_summary_file)
                                sensitivity_logger.info(f"Found economic summary at {econ_summary_file}")

                                # Extract average selling price and NPV
                                price_row = econ_df[econ_df['Metric'] == 'Average Selling Price (Project Life Cycle)']
                                npv_row = econ_df[econ_df['Metric'] == 'Cumulative NPV']

                                if not price_row.empty and not npv_row.empty:
                                    # Extract values (removing $ and commas)
                                    price_str = price_row.iloc[0]['Value'].replace('$', '').replace(',', '')
                                    npv_str = npv_row.iloc[0]['Value'].replace('$', '').replace(',', '')

                                    try:
                                        price = float(price_str)
                                        npv = float(npv_str)

                                        param_results["variations"][var_str]["price"] = price
                                        param_results["variations"][var_str]["npv"] = npv
                                        sensitivity_logger.info(f"Extracted price: ${price:,.2f}, NPV: ${npv:,.2f}")
                                    except ValueError as ve:
                                        sensitivity_logger.warning(f"Could not parse price or NPV values: {ve}")
                            else:
                                sensitivity_logger.warning(f"Economic summary not found at: {econ_summary_file}")
                                sensitivity_logger.info(f"Checked locations: {param_var_dir} and {sensitivity_dir}/{mode_cap}/Configuration/{param_id}_{var_str}")

                        except Exception as e:
                            sensitivity_logger.error(f"Error extracting economic summary: {str(e)}")

                    else:
                        error_msg = f"Calculation failed for {param_id} variation {var_str}: {result.stderr}"
                        sensitivity_logger.error(error_msg)
                        param_results["variations"][var_str] = {
                            "status": "error",
                            "message": error_msg
                        }
                        param_results["success"] = False
                        overall_success = False

                except subprocess.TimeoutExpired:
                    error_msg = f"Calculation timed out for {param_id} variation {var_str}"
                    sensitivity_logger.error(error_msg)
                    param_results["variations"][var_str] = {
                        "status": "error",
                        "message": error_msg
                    }
                    param_results["success"] = False
                    overall_success = False

                except Exception as e:
                    error_msg = f"Error processing {param_id} variation {var_str}: {str(e)}"
                    sensitivity_logger.error(error_msg)
                    param_results["variations"][var_str] = {
                        "status": "error",
                        "message": error_msg
                    }
                    param_results["success"] = False
                    overall_success = False

            # Add results for this parameter
            calculation_results[param_id] = param_results

        # Log summary and return results
        sensitivity_logger.info("\nSensitivity Calculation Summary:")
        for param_id, result in calculation_results.items():
            success_count = sum(1 for var in result["variations"].values() if var.get("status") == "success")
            total_count = len(result["variations"])
            sensitivity_logger.info(f"{param_id}: {success_count}/{total_count} variations successful")

        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Run completed - ID: {run_id}")
        sensitivity_logger.info(f"Overall success: {overall_success}")
        sensitivity_logger.info(f"{'='*80}\n")

        # Return results
        return jsonify({
            "status": "success" if overall_success else "partial",
            "message": "Sensitivity calculations completed" + (" with some errors" if not overall_success else ""),
            "runId": run_id,
            "results": calculation_results
        })

    except Exception as e:
        error_msg = f"Error during sensitivity calculations: {str(e)}"
        sensitivity_logger.error(error_msg)
        return jsonify({
            "error": error_msg,
            "runId": run_id
        }), 500

@app.route('/api/sensitivity/visualize', methods=['POST'])
def sensitivity_visualize():
    """
    Generate visualization data for sensitivity analysis.

    Expected JSON payload:
    {
        "version": 1,
        "param_id": "S10",
        "mode": "percentage",
        "compareToKey": "S13",
        "plotTypes": ["waterfall", "bar", "point"]
    }
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Sensitivity Visualization Request - Run ID: {run_id}")
        sensitivity_logger.info(f"{'='*80}")

        data = request.json
        if not data:
            sensitivity_logger.error("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        # Extract parameters
        version = data.get('version', 1)
        param_id = data.get('param_id')
        mode = data.get('mode', 'percentage')
        compare_to_key = data.get('compareToKey', 'S13')
        plot_types = data.get('plotTypes', ['waterfall', 'bar', 'point'])

        sensitivity_logger.info(f"Visualization request for:")
        sensitivity_logger.info(f"Version: {version}")
        sensitivity_logger.info(f"Parameter: {param_id}")
        sensitivity_logger.info(f"Mode: {mode}")
        sensitivity_logger.info(f"Comparison key: {compare_to_key}")
        sensitivity_logger.info(f"Plot types: {', '.join(plot_types)}")

        if not param_id:
            sensitivity_logger.error("Parameter ID is required but not provided")
            return jsonify({"error": "Parameter ID is required"}), 400

        # Get sensitivity data
        sensitivity_logger.info(f"Retrieving sensitivity data for {param_id}...")
        sensitivity_data = get_sensitivity_data(version, param_id, mode, compare_to_key)
        if not sensitivity_data:
            error_msg = f"No data available for {param_id} in {mode} mode"
            sensitivity_logger.error(error_msg)
            return jsonify({
                "error": "Sensitivity data not found",
                "message": error_msg
            }), 404

        sensitivity_logger.info("Successfully retrieved sensitivity data")

        # Check if plots exist or need to be generated
        plots_info = {}
        mode_dir_mapping = {
            'percentage': 'Percentage',
            'directvalue': 'DirectValue',
            'absolutedeparture': 'AbsoluteDeparture',
            'montecarlo': 'MonteCarlo'
        }
        mode_dir = mode_dir_mapping.get(mode.lower(), 'Percentage')

        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        sensitivity_dir = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity',
            mode_dir
        )

        sensitivity_logger.info(f"Checking for plots in directory: {sensitivity_dir}")

        for plot_type in plot_types:
            plot_name = f"{plot_type}_{param_id}_{compare_to_key}_primary.png"
            plot_path = os.path.join(sensitivity_dir, plot_type, plot_name)

            if os.path.exists(plot_path):
                sensitivity_logger.info(f"Found existing {plot_type} plot at: {plot_path}")
                plots_info[plot_type] = {
                    "status": "available",
                    "path": os.path.relpath(plot_path, base_dir)
                }
            else:
                sensitivity_logger.info(f"Need to generate {plot_type} plot...")
                try:
                    # Import plot generation function
                    from sensitivity_Routes import generate_plot_from_results

                    # Get path to results file
                    results_path = os.path.join(
                        sensitivity_dir,
                        f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
                    )

                    sensitivity_logger.info(f"Generating {plot_type} plot from results at: {results_path}")

                    # Generate plot
                    success = generate_plot_from_results(
                        version=version,
                        param_id=param_id,
                        compare_to_key=compare_to_key,
                        plot_type=plot_type,
                        mode=mode,
                        result_path=results_path
                    )

                    if success and os.path.exists(plot_path):
                        sensitivity_logger.info(f"Successfully generated {plot_type} plot at: {plot_path}")
                        plots_info[plot_type] = {
                            "status": "generated",
                            "path": os.path.relpath(plot_path, base_dir)
                        }
                    else:
                        error_msg = f"Failed to generate {plot_type} plot"
                        sensitivity_logger.error(error_msg)
                        plots_info[plot_type] = {
                            "status": "error",
                            "error": error_msg
                        }
                except Exception as e:
                    error_msg = f"Error generating {plot_type} plot: {str(e)}"
                    sensitivity_logger.error(error_msg)
                    plots_info[plot_type] = {
                        "status": "error",
                        "error": error_msg
                    }

        # Prepare visualization data
        visualization_data = {
            "parameter": param_id,
            "compareToKey": compare_to_key,
            "mode": mode,
            "data": sensitivity_data,
            "plots": plots_info
        }

        sensitivity_logger.info(f"Visualization request completed successfully for run ID: {run_id}")
        sensitivity_logger.info(f"{'='*80}\n")

        return jsonify(visualization_data)

    except Exception as e:
        error_msg = f"Error in visualization endpoint: {str(e)}"
        sensitivity_logger.error(error_msg)
        sensitivity_logger.info(f"{'='*80}\n")
        return jsonify({
            "error": f"Error generating visualization: {str(e)}"
        }), 500

@app.route('/api/sensitivity/parameters', methods=['GET'])
def get_sensitivity_parameters():
    """Get all available sensitivity parameters for visualization."""
    sensitivity_logger = logging.getLogger('sensitivity')
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        sensitivity_logger.info(f"\n{'='*80}")
        sensitivity_logger.info(f"Get Sensitivity Parameters Request - Run ID: {run_id}")
        sensitivity_logger.info(f"{'='*80}")

        version = request.args.get('version', '1')
        sensitivity_logger.info(f"Requested parameters for version: {version}")

        # Try to get parameters from CalSen service first
        try:
            sensitivity_logger.info("Attempting to get parameters from CalSen service...")
            response = requests.post(
                "http://localhost:2750/list_parameters",
                json={"version": int(version)},
                timeout=5
            )

            if response.status_code == 200:
                sensitivity_logger.info("Successfully retrieved parameters from CalSen service")
                sensitivity_logger.info(f"{'='*80}\n")
                return jsonify(response.json())
        except Exception as e:
            sensitivity_logger.warning(f"CalSen service not available: {str(e)}")
            # Continue with fallback

        # Fallback: scan directories
        sensitivity_logger.info("Falling back to directory scanning method")
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        sensitivity_dir = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity'
        )

        if not os.path.exists(sensitivity_dir):
            error_msg = f"No sensitivity data found for version {version}"
            sensitivity_logger.error(error_msg)
            sensitivity_logger.info(f"{'='*80}\n")
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 404

        # Look for parameter directories (starting with S)
        parameters = []
        sensitivity_logger.info(f"Scanning directory for parameters: {sensitivity_dir}")

        for item in os.listdir(sensitivity_dir):
            item_path = os.path.join(sensitivity_dir, item)

            if os.path.isdir(item_path) and item.startswith('S'):
                param_id = item

                # Find mode directories inside parameter directory
                modes = []
                for subdir in os.listdir(item_path):
                    subdir_path = os.path.join(item_path, subdir)
                    if os.path.isdir(subdir_path):
                        modes.append(subdir)

                # Add parameter info
                parameters.append({
                    "id": param_id,
                    "modes": modes
                })
                sensitivity_logger.info(f"Found parameter: {param_id} with modes: {', '.join(modes)}")

        sensitivity_logger.info(f"Found {len(parameters)} parameters total")
        sensitivity_logger.info(f"{'='*80}\n")

        return jsonify({
            "status": "success",
            "version": version,
            "parameters": parameters,
            "source": "directory"
        })

    except Exception as e:
        error_msg = f"Error retrieving sensitivity parameters: {str(e)}"
        sensitivity_logger.error(error_msg)
        sensitivity_logger.info(f"{'='*80}\n")
        return jsonify({
            "error": f"Error retrieving sensitivity parameters: {str(e)}"
        }), 500

@app.route('/run-all-sensitivity', methods=['POST'])
def run_all_sensitivity():
    """
    Unified wrapper to execute all sensitivity_Routes endpoints sequentially.
    Meant to replicate frontend's full analysis process with a single call.
    """
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Missing input payload"}), 400

        headers = {'Content-Type': 'application/json'}
        version = payload.get('selectedVersions', [1])[0]
        base_url = 'http://127.0.0.1:2500'

        enabled_params = payload.get('enabledParams', [])

        def post(path, body=None):
            r = requests.post(f"{base_url}{path}", headers=headers, json=body or payload)
            return r.status_code, r.json() if r.ok else {"error": r.text}

        def get(path):
            r = requests.get(f"{base_url}{path}", headers=headers)
            return r.status_code, r.json() if r.ok else {"error": r.text}

        result = {}

        result['summary'] = get(f"//sensitivity/plots/<mode>/<plot_type>")
        result['summary'] = get(f"/sensitivity/percentage")
        result['summary'] = get(f"/sensitivity/analysis")

        # 5. /sensitivity/analysis for each param
        result['analysis'] = []
        for param in enabled_params:
            param_payload = {
                "param_id": param['paramId'],
                "mode": param['mode'],
                "values": param['values'],
                "compareToKey": param.get('compareToKey', 'S13'),
                "version": version,
                "waterfall": True,
                "bar": True,
                "point": True
            }
            result['analysis'].append({
                "param_id": param['paramId'],
                "result": post('/sensitivity/analysis', param_payload)
            })

        # 6. /api/sensitivity/parameters
        result['parameters'] = get(f"/api/sensitivity/parameters?version={version}")

        # 7. /generate-report
        result['report'] = post('/generate-report', {"version": version})

        # 8. /api/sensitivity-summary/<version>
        result['summary'] = get(f"/api/sensitivity-summary/{version}")

        # 9. /api/sensitivity/visualize for first parameter (if available)
        if result['parameters'][0] == 200 and result['parameters'][1]:
            first_param = result['parameters'][1][0]
            viz_payload = {
                "version": version,
                "param_id": first_param['id'],
                "mode": first_param['modes'][0] if first_param['modes'] else 'percentage',
                "compareToKey": first_param.get('compareToKey', 'S13'),
                "plotTypes": ['waterfall', 'bar', 'point']
            }
            result['visualize'] = post('/api/sensitivity/visualize', viz_payload)

        # 10. /runs route
        result['runs'] = post('/runs', payload)

        return jsonify({
            "status": "success",
            "message": "All sensitivity routes triggered via unified endpoint.",
            "results": result
        })

    except Exception as e:
        return jsonify({
            "error": f"Error executing unified sensitivity runner: {str(e)}"
        }), 500


@app.route('/check-calsen-paths', methods=['GET'])
def check_calsen_paths():
    """
    Check if calsen_paths.json exists for the specified version.
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    version = request.args.get('version', '1')

    sensitivity_logger.info(f"Checking if calsen_paths.json exists for version {version}")

    # Calculate path to calsen_paths.json
    base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
    sensitivity_dir = os.path.join(base_dir, f'Batch({version})', f'Results({version})', 'Sensitivity')
    reports_dir = os.path.join(sensitivity_dir, 'Reports')
    calsen_paths_file = os.path.join(reports_dir, 'calsen_paths.json')

    # Check if file exists
    file_exists = os.path.exists(calsen_paths_file)

    # Log the result
    if file_exists:
        sensitivity_logger.info(f"calsen_paths.json found at {calsen_paths_file}")
    else:
        sensitivity_logger.warning(f"calsen_paths.json not found at {calsen_paths_file}")

    # Include payload details for monitoring
    payload_details = {
        "operation": "check_calsen_paths",
        "version": version,
        "path": calsen_paths_file,
        "exists": file_exists
    }

    # Log payload details for monitoring
    sensitivity_logger.info(f"Payload details: {json.dumps(payload_details)}")

    return jsonify({
        'exists': file_exists,
        'path': calsen_paths_file
    })

@app.route('/run-script-econ', methods=['POST'])
def run_script_econ():
    """
    Execute script_econ.py to extract metrics from Economic Summary CSV files
    and append them to calsen_paths.json.
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    data = request.get_json()
    version = data.get('version', '1')

    # Log the start of the operation
    sensitivity_logger.info(f"Starting script_econ.py execution for version {version}")

    # Include payload details for monitoring
    payload_details = {
        "operation": "run_script_econ",
        "version": version,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Log payload details for monitoring
    sensitivity_logger.info(f"Payload details: {json.dumps(payload_details)}")

    try:
        # Get path to script_econ.py
        script_path = os.path.join(BASE_DIR, 'backend', 'API_endpoints_and_controllers', 'script_econ.py')
        sensitivity_logger.info(f"Script path: {script_path}")

        # Log calculation step
        calculation_step = "Extracting metrics from Economic Summary CSV files"
        sensitivity_logger.info(f"Calculation step: {calculation_step}")

        # Execute script_econ.py with the version argument
        sensitivity_logger.info(f"Executing: {sys.executable} {script_path} --version {version}")
        result = subprocess.run(
            [sys.executable, script_path, '--version', version],
            capture_output=True,
            text=True,
            check=True
        )

        # Log the output
        sensitivity_logger.info(f"script_econ.py stdout: {result.stdout}")
        if result.stderr:
            sensitivity_logger.warning(f"script_econ.py stderr: {result.stderr}")

        # Log success
        sensitivity_logger.info(f"script_econ.py executed successfully for version {version}")

        return jsonify({
            'status': 'success',
            'message': 'script_econ.py executed successfully',
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except subprocess.CalledProcessError as e:
        # Log error
        sensitivity_logger.error(f"Error executing script_econ.py: {str(e)}")
        sensitivity_logger.error(f"stdout: {e.stdout}")
        sensitivity_logger.error(f"stderr: {e.stderr}")

        return jsonify({
            'status': 'error',
            'message': f'Error executing script_econ.py: {str(e)}',
            'stdout': e.stdout,
            'stderr': e.stderr
        }), 500
    except Exception as e:
        # Log error
        sensitivity_logger.error(f"Unexpected error executing script_econ.py: {str(e)}")

        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/run-add-axis-labels', methods=['POST'])
def run_add_axis_labels():
    """
    Execute add_axis_labels.py to add axis labels to the JSON file
    based on parameter names and modified values.
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    data = request.get_json()
    version = data.get('version', '1')

    # Log the start of the operation
    sensitivity_logger.info(f"Starting add_axis_labels.py execution for version {version}")

    # Include payload details for monitoring
    payload_details = {
        "operation": "run_add_axis_labels",
        "version": version,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Log payload details for monitoring
    sensitivity_logger.info(f"Payload details: {json.dumps(payload_details)}")

    try:
        # Get path to add_axis_labels.py
        script_path = os.path.join(BASE_DIR, 'backend', 'API_endpoints_and_controllers', 'add_axis_labels.py')
        sensitivity_logger.info(f"Script path: {script_path}")

        # Log calculation step
        calculation_step = "Adding axis labels to JSON file based on parameter names and modified values"
        sensitivity_logger.info(f"Calculation step: {calculation_step}")

        # Execute add_axis_labels.py with the version argument
        sensitivity_logger.info(f"Executing: {sys.executable} {script_path} {version}")
        result = subprocess.run(
            [sys.executable, script_path, version],
            capture_output=True,
            text=True,
            check=True
        )

        # Log the output
        sensitivity_logger.info(f"add_axis_labels.py stdout: {result.stdout}")
        if result.stderr:
            sensitivity_logger.warning(f"add_axis_labels.py stderr: {result.stderr}")

        # Log success
        sensitivity_logger.info(f"add_axis_labels.py executed successfully for version {version}")

        return jsonify({
            'status': 'success',
            'message': 'add_axis_labels.py executed successfully',
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except subprocess.CalledProcessError as e:
        # Log error
        sensitivity_logger.error(f"Error executing add_axis_labels.py: {str(e)}")
        sensitivity_logger.error(f"stdout: {e.stdout}")
        sensitivity_logger.error(f"stderr: {e.stderr}")

        return jsonify({
            'status': 'error',
            'message': f'Error executing add_axis_labels.py: {str(e)}',
            'stdout': e.stdout,
            'stderr': e.stderr
        }), 500
    except Exception as e:
        # Log error
        sensitivity_logger.error(f"Unexpected error executing add_axis_labels.py: {str(e)}")

        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/run-generate-plots', methods=['POST'])
def run_generate_plots():
    """
    Execute generate_plots.py to generate plot files for sensitivity analysis.
    """
    sensitivity_logger = logging.getLogger('sensitivity')
    data = request.get_json()
    version = data.get('version', '1')

    # Log the start of the operation
    sensitivity_logger.info(f"Starting generate_plots.py execution for version {version}")

    # Include payload details for monitoring
    payload_details = {
        "operation": "run_generate_plots",
        "version": version,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Log payload details for monitoring
    sensitivity_logger.info(f"Payload details: {json.dumps(payload_details)}")

    try:
        # Get path to generate_plots.py
        script_path = os.path.join(BASE_DIR, 'backend', 'API_endpoints_and_controllers', 'generate_plots.py')
        sensitivity_logger.info(f"Script path: {script_path}")

        # Log calculation step
        calculation_step = "Generating plot files for sensitivity analysis"
        sensitivity_logger.info(f"Calculation step: {calculation_step}")

        # Execute generate_plots.py with the version argument
        sensitivity_logger.info(f"Executing: {sys.executable} {script_path} {version}")
        result = subprocess.run(
            [sys.executable, script_path, version],
            capture_output=True,
            text=True,
            check=True
        )

        # Log the output
        sensitivity_logger.info(f"generate_plots.py stdout: {result.stdout}")
        if result.stderr:
            sensitivity_logger.warning(f"generate_plots.py stderr: {result.stderr}")

        # Log success
        sensitivity_logger.info(f"generate_plots.py executed successfully for version {version}")

        return jsonify({
            'status': 'success',
            'message': 'generate_plots.py executed successfully',
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except subprocess.CalledProcessError as e:
        # Log error
        sensitivity_logger.error(f"Error executing generate_plots.py: {str(e)}")
        sensitivity_logger.error(f"stdout: {e.stdout}")
        sensitivity_logger.error(f"stderr: {e.stderr}")

        return jsonify({
            'status': 'error',
            'message': f'Error executing generate_plots.py: {str(e)}',
            'stdout': e.stdout,
            'stderr': e.stderr
        }), 500
    except Exception as e:
        # Log error
        sensitivity_logger.error(f"Unexpected error executing generate_plots.py: {str(e)}")

        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=2500)
