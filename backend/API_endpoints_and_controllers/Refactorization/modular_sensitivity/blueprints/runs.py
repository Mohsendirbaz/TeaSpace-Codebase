from flask import Blueprint, jsonify, request
import time
import os
import glob
import subprocess
import requests
from config import LOGS_DIR, RUN_LOCK_FILE, SENSITIVITY_CONFIG_STATUS_PATH, SENSITIVITY_CONFIG_DATA_PATH, BASE_DIR, SCRIPT_DIR
from state import GLOBAL_RUN_LOCK, RUNS_COMPLETED, CONFIG_COMPLETED
from decorators import with_file_lock, with_memory_lock, with_pipeline_check
from utils import trigger_config_module_copy, atomic_read_json, atomic_read_pickle, atomic_write_pickle
from pipeline import reset_execution_pipeline

runs_bp = Blueprint('runs', __name__)

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

@runs_bp.route('/runs', methods=['POST'])
@with_file_lock(RUN_LOCK_FILE, "calculation runs")
@with_memory_lock(GLOBAL_RUN_LOCK, "calculation runs")
@with_pipeline_check(required_event=CONFIG_COMPLETED, next_event=RUNS_COMPLETED, operation_name="calculation runs")
def run_calculations():
    """Execute sensitivity calculations based on configured parameters"""
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        data = request.get_json()
        provided_run_id = data.get('runId')
        if provided_run_id:
            run_id = provided_run_id

        # Check if sensitivity configurations have been generated using thread-safe function
        is_configured, saved_config = check_sensitivity_config_status()

        # If sensitivity configurations haven't been generated, return an error
        if not is_configured:
            return jsonify({
                "error": "Sensitivity configurations must be generated first",
                "message": "Please call /sensitivity/configure endpoint to generate and save sensitivity configurations before running calculations",
                "status": "error"
            }), 400

        # Use the saved configuration data if available, otherwise use the request data
        if saved_config:
            config = saved_config
        elif data:
            config = {
                'versions': data.get('selectedVersions', [1]),
                'selectedV': data.get('selectedV', {f'V{i+1}': 'off' for i in range(10)}),
                'selectedF': data.get('selectedF', {f'F{i+1}': 'off' for i in range(5)}),
                'calculationOption': data.get('selectedCalculationOption', 'freeFlowNPV'),
                'targetRow': int(data.get('targetRow', 20)),
                'SenParameters': data.get('SenParameters', {})
            }
        else:
            return jsonify({"error": "No configuration data available"}), 400

        # Get version and paths
        version = config['versions'][0]
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        results_folder = os.path.join(base_dir, f'Batch({version})', f'Results({version})')
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        # Verify that sensitivity directories exist
        if not os.path.exists(sensitivity_dir):
            error_msg = f"Sensitivity directory not found: {sensitivity_dir}"
            return jsonify({
                "error": error_msg,
                "message": "Please call /sensitivity/configure endpoint to generate and save sensitivity configurations",
                "status": "error"
            }), 400

        # Start timing
        start_time = time.time()

        # Step 1: Trigger the config module copy service BEFORE sensitivity calculations
        copy_service_result = trigger_config_module_copy(
            version,
            sensitivity_dir,
            config['SenParameters']
        )

        # Wait for config copy service to complete (or timeout after 5 minutes)
        max_wait_time = 300  # 5 minutes in seconds
        start_wait = time.time()

        # First check if service is available
        while time.time() - start_wait < max_wait_time:
            try:
                response = requests.get("http://localhost:2600/health", timeout=2)
                if response.ok:
                    break
            except requests.exceptions.RequestException:
                pass

            # Wait and check again
            time.sleep(15)  # Check every 15 seconds

        # Update configuration pickle file for subsequent steps
        try:
            # Save configuration data with explicit version using thread-safe function
            if isinstance(config['versions'], list) and version not in config['versions']:
                config['versions'].append(version)
            atomic_write_pickle(SENSITIVITY_CONFIG_DATA_PATH, config)
        except Exception:
            pass

        # Step 2: Process sensitivity parameters if enabled
        enabled_params = [k for k, v in config['SenParameters'].items() if v.get('enabled')]
        if enabled_params:
            try:
                process_script = os.path.join(
                    SCRIPT_DIR,
                    "API_endpoints_and_controllers",
                    "process_sensitivity_results.py"
                )

                if os.path.exists(process_script):
                    process_result = subprocess.run(
                        ['python', process_script, str(version), '0.5'],  # 30 second wait time
                        capture_output=True,
                        text=True
                    )

                    if process_result.returncode != 0:
                        # Try running with backup approach if the first attempt failed
                        for param_id, param_config in config['SenParameters'].items():
                            if not param_config.get('enabled'):
                                continue

                            # Get calculation script
                            calculation_script_func = CALCULATION_SCRIPTS.get(config['calculationOption'])
                            if not calculation_script_func:
                                continue

                            calculation_script = calculation_script_func(version)

                            # Run CFA on each modified configuration with thread-safe approach
                            param_lock = threading.Lock()
                            with param_lock:
                                mode = param_config.get('mode', 'symmetrical')
                                values = param_config.get('values', [])

                                if mode.lower() == 'symmetrical':
                                    base_variation = values[0]
                                    variations = [base_variation, -base_variation]
                                else:
                                    variations = values

                                for variation in variations:
                                    var_str = f"{variation:+.2f}"

                                    # Find modified config files
                                    mode_dir = 'symmetrical' if mode.lower() == 'symmetrical' else 'multiple'
                                    config_pattern = os.path.join(
                                        sensitivity_dir,
                                        param_id,
                                        mode_dir,
                                        var_str,
                                        f"{version}_config_module_*.json"
                                    )

                                    config_files = glob.glob(config_pattern)
                                    if config_files:
                                        for config_file in config_files:
                                            try:
                                                subprocess.run(
                                                    [
                                                        'python',
                                                        calculation_script,
                                                        str(version),
                                                        '-c', config_file,
                                                        '--sensitivity',
                                                        param_id,
                                                        str(variation),
                                                        param_config.get('compareToKey', 'S13')
                                                    ],
                                                    capture_output=True,
                                                    text=True,
                                                    timeout=300  # 5 minute timeout
                                                )
                                            except subprocess.TimeoutExpired:
                                                continue
            except Exception:
                pass

        # Calculate total execution time
        total_time = time.time() - start_time

        # RUNS_COMPLETED event is set by the decorator

        # Return success response with timing information
        return jsonify({
            "status": "success",
            "message": "Sensitivity calculations completed successfully",
            "runId": run_id,
            "version": version,
            "timing": {
                "total": f"{total_time:.2f}s",
                "parameters_processed": len(enabled_params)
            },
            "configCopy": copy_service_result,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "next_step": "Pipeline complete"
        }), 200

    except Exception as e:
        # Don't clear event flag here - let the decorator handle it
        return jsonify({
            "error": f"Error during sensitivity calculations: {str(e)}",
            "status": "error",
            "runId": run_id
        }), 500
