import os
import json
import pickle
import threading

import filelock
import tempfile
import subprocess
import requests
import time
from typing import Tuple, Dict, Any, Optional, List

# Import configuration and logging
from config import LOGS_DIR, COMMON_PYTHON_SCRIPTS, BASE_DIR, SENSITIVITY_CONFIG_STATUS_PATH, SENSITIVITY_CONFIG_DATA_PATH
from .logging_config import get_module_logger

logger = get_module_logger(__name__)

def atomic_read_json(filepath):
    """Thread-safe reading of JSON file"""
    tempdir = tempfile.gettempdir()
    temp_file = os.path.join(tempdir, f"temp_{os.path.basename(filepath)}")

    # Create a file lock for this specific file
    lock_file = f"{filepath}.lock"
    lock = filelock.FileLock(lock_file, timeout=60)

    logger.info(f"Reading JSON file: {filepath}")
    with lock:
        if os.path.exists(filepath):
            # Copy to temp location first
            with open(filepath, 'r') as src:
                content = src.read()

            with open(temp_file, 'w') as dst:
                dst.write(content)

            # Read from the temp file
            with open(temp_file, 'r') as f:
                data = json.load(f)

            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass

            return data
        return None

def atomic_write_json(filepath, data):
    """Thread-safe writing of JSON file"""
    tempdir = tempfile.gettempdir()
    temp_file = os.path.join(tempdir, f"temp_{os.path.basename(filepath)}")

    # Create a file lock for this specific file
    lock_file = f"{filepath}.lock"
    lock = filelock.FileLock(lock_file, timeout=60)

    logger.info(f"Writing JSON file: {filepath}")
    with lock:
        # Write to temp file first
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Move temp file to target (atomic operation)
        if os.path.exists(filepath):
            os.remove(filepath)

        os.rename(temp_file, filepath)

def atomic_read_pickle(filepath):
    """Thread-safe reading of pickle file"""
    tempdir = tempfile.gettempdir()
    temp_file = os.path.join(tempdir, f"temp_{os.path.basename(filepath)}")

    # Create a file lock for this specific file
    lock_file = f"{filepath}.lock"
    lock = filelock.FileLock(lock_file, timeout=60)

    with lock:
        if os.path.exists(filepath):
            # Copy to temp location first
            with open(filepath, 'rb') as src:
                content = src.read()

            with open(temp_file, 'wb') as dst:
                dst.write(content)

            # Read from the temp file
            with open(temp_file, 'rb') as f:
                data = pickle.load(f)

            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass

            return data
        return None

def atomic_write_pickle(filepath, data):
    """Thread-safe writing of pickle file"""
    tempdir = tempfile.gettempdir()
    temp_file = os.path.join(tempdir, f"temp_{os.path.basename(filepath)}")

    # Create a file lock for this specific file
    lock_file = f"{filepath}.lock"
    lock = filelock.FileLock(lock_file, timeout=60)

    with lock:
        # Write to temp file first
        with open(temp_file, 'wb') as f:
            pickle.dump(data, f)

        # Move temp file to target (atomic operation)
        if os.path.exists(filepath):
            os.remove(filepath)

        os.rename(temp_file, filepath)

from state import acquire_lock

def trigger_config_module_copy(version, sensitivity_dir, sen_parameters):
    """Thread-safe config module copying service trigger"""
    try:
        # Use a unique lock for this specific operation
        lock = threading.Lock()
        with acquire_lock(lock, "config_module_copy"):
            response = requests.post(
                "http://localhost:2600/copy-config-modules",
                json={
                    "version": version,
                    "sensitivity_dir": sensitivity_dir,
                    "parameters": sen_parameters
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Error triggering config copy service: {response.text}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Config copy service not available"}
    except Exception as e:
        return {"error": f"Error connecting to config copy service: {str(e)}"}

def run_script(script_name, *args, script_type="python"):
    """Thread-safe script execution with proper error handling"""
    # Create a unique temporary directory for this script execution
    temp_dir = tempfile.mkdtemp()
    temp_output = os.path.join(temp_dir, "output.txt")

    logger.info(f"Executing script: {os.path.basename(script_name)} with args: {args}")
    try:
        command = ['python' if script_type == "python" else 'Rscript', script_name]
        command.extend([str(arg) for arg in args])

        # Redirect output to a file in the temporary directory
        with open(temp_output, 'w') as output_file:
            result = subprocess.run(
                command,
                stdout=output_file,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode != 0:
            return False, f"Error running {os.path.basename(script_name)}: {result.stderr}"

        return True, None
    except Exception as e:
        return False, f"Exception running {os.path.basename(script_name)}: {str(e)}"
    finally:
        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

def process_version(version, calculation_script, selected_v, selected_f, target_row,
                    calculation_option, SenParameters):
    """Thread-safe version processing with proper locking"""
    # Create a unique lock for this version
    version_lock = threading.RLock()

    with acquire_lock(version_lock, f"version_processing_{version}"):
        try:
            # Run common configuration scripts
            for script in COMMON_PYTHON_SCRIPTS:
                success, error = run_script(script, version)
                if not success:
                    return error

            # Run calculation script
            success, error = run_script(
                calculation_script,
                version,
                json.dumps(selected_v),
                json.dumps(selected_f),
                json.dumps(target_row),
                calculation_option,
                json.dumps(SenParameters)
            )
            if not success:
                return error

            return None
        except Exception as e:
            return f"Error processing version {version}: {str(e)}"

def create_sensitivity_directories(version, SenParameters):
    """Thread-safe directory creation with proper locking"""
    # Create a lock specific to this version and operation
    dir_lock_file = os.path.join(LOGS_DIR, f"dir_creation_{version}.lock")
    lock = filelock.FileLock(dir_lock_file, timeout=60)

    logger.info(f"Creating sensitivity directories for version: {version}")
    with lock:
        # Define base paths
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        results_folder = os.path.join(base_dir, f'Batch({version})', f'Results({version})')
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        # Create main sensitivity directory
        os.makedirs(sensitivity_dir, exist_ok=True)

        # Create standard subdirectories
        for subdir in ["Reports", "Cache", "Configuration"]:
            path = os.path.join(sensitivity_dir, subdir)
            os.makedirs(path, exist_ok=True)

        reports_dir = os.path.join(sensitivity_dir, "Reports")

        # Create analysis mode directories
        for mode in ["Symmetrical", "Multipoint"]:
            mode_dir = os.path.join(sensitivity_dir, mode)
            os.makedirs(mode_dir, exist_ok=True)

            # Create plot type subdirectories
            for plot_type in ["waterfall", "bar", "point", "Configuration"]:
                plot_type_dir = os.path.join(mode_dir, plot_type)
                os.makedirs(plot_type_dir, exist_ok=True)

        # Process each parameter
        enabled_params = [(param_id, config) for param_id, config in SenParameters.items()
                          if config.get('enabled')]

        for param_id, param_config in enabled_params:
            # Skip disabled parameters
            if not param_config.get('enabled'):
                continue

            # Get parameter details
            mode = param_config.get('mode', 'symmetrical')
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

            # Create mode directory within parameter
            param_mode_dir = os.path.join(param_dir, mode)
            os.makedirs(param_mode_dir, exist_ok=True)

            # Determine variation values based on mode
            variation_list = []
            if mode.lower() == 'symmetrical':
                if values and len(values) > 0:
                    base_variation = values[0]
                    variation_list = [base_variation, -base_variation]
            else:  # 'multipoint' or other modes
                variation_list = values

            # Create variation directories
            for variation in variation_list:
                var_str = f"{variation:+.2f}"

                # 1. Create parameter variation directories
                var_dir = os.path.join(param_dir, mode, var_str)
                os.makedirs(var_dir, exist_ok=True)

                # 2. Create configuration variation directories
                mode_name = "Symmetrical" if mode.lower() == "symmetrical" else "Multipoint"
                config_var_dir = os.path.join(sensitivity_dir, mode_name, "Configuration", f"{param_id}_{var_str}")
                os.makedirs(config_var_dir, exist_ok=True)

            # Create plot type directories for this parameter
            mode_dir = os.path.join(sensitivity_dir,
                                    "Symmetrical" if mode.lower() == "symmetrical" else "Multipoint")

            for plot_type in plot_types:
                plot_dir = os.path.join(mode_dir, plot_type, f"{param_id}_{plot_type}")
                os.makedirs(plot_dir, exist_ok=True)

        return sensitivity_dir, reports_dir

def save_sensitivity_config_files(version, reports_dir, SenParameters):
    """Thread-safe configuration file saving with proper locking"""
    # Create a lock specific to this version and operation
    file_lock_file = os.path.join(LOGS_DIR, f"config_files_{version}.lock")
    lock = filelock.FileLock(file_lock_file, timeout=60)

    logger.info(f"Saving config files for version: {version}")
    with lock:
        saved_files = []

        # Get base directory
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        results_folder = os.path.join(base_dir, f'Batch({version})', f'Results({version})')
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        # Save main configuration file in reports directory
        config_file = os.path.join(reports_dir, "sensitivity_config.json")
        atomic_write_json(config_file, {
            'version': version,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'parameters': SenParameters
        })
        saved_files.append(config_file)

        # Save individual parameter configuration files in their respective directories
        for param_id, param_config in SenParameters.items():
            if not param_config.get('enabled'):
                continue

            # Get mode and values
            mode = param_config.get('mode', 'symmetrical')
            values = param_config.get('values', [])

            if not values:
                continue

            # Determine variation list based on mode
            if mode.lower() == 'symmetrical':
                # For symmetrical, use first value to create +/- variations
                base_variation = values[0]
                variation_list = [base_variation, -base_variation]
            else:  # 'multipoint' mode
                # For multipoint, use all values directly
                variation_list = values

            # Save configuration for each variation
            for variation in variation_list:
                # Format the variation string (e.g., "+10.00" or "-5.00")
                var_str = f"{variation:+.2f}"

                # Create path to variation directory
                var_dir = os.path.join(sensitivity_dir, param_id, mode, var_str)

                # Save configuration file
                param_file = os.path.join(var_dir, f"{param_id}_config.json")
                atomic_write_json(param_file, {
                    'parameter': param_id,
                    'config': param_config,
                    'variation': variation,
                    'variation_str': var_str,
                    'mode': mode,
                    'version': version,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                })
                saved_files.append(param_file)

        return saved_files

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
        logger = get_module_logger(__name__)
        logger.warning(f"Results file not found: {results_path}")
        return None

    # Load results data
    try:
        with open(results_path, 'r') as f:
            results_data = json.load(f)
        return results_data
    except Exception as e:
        logger = get_module_logger(__name__)
        logger.error(f"Error loading results data: {str(e)}")
        return None

def check_sensitivity_config_status():
    """Thread-safe configuration status check with proper locking"""
    status_lock_file = os.path.join(LOGS_DIR, "status_check.lock")
    lock = filelock.FileLock(status_lock_file, timeout=30)

    with lock:
        if not os.path.exists(SENSITIVITY_CONFIG_STATUS_PATH):
            return False, None

        try:
            # Use atomic read for thread safety
            status = atomic_read_json(SENSITIVITY_CONFIG_STATUS_PATH)

            if not status or not status.get('configured', False):
                return False, None

            if os.path.exists(SENSITIVITY_CONFIG_DATA_PATH):
                # Use atomic read for thread safety
                config_data = atomic_read_pickle(SENSITIVITY_CONFIG_DATA_PATH)
                return True, config_data

            return True, None

        except Exception:
            return False, None
