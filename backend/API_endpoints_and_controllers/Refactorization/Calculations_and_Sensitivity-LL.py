from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import subprocess
import os
import json
import time
import sys
import pickle
import requests
import glob
import pandas as pd
import threading
import filelock
import tempfile
import functools

# =====================================
# Base Configuration
# =====================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_DIR = os.path.join(BASE_DIR, 'backend')
LOGS_DIR = os.path.join(SCRIPT_DIR, 'Logs')
ORIGINAL_BASE_DIR = os.path.join(BASE_DIR, 'backend', 'Original')

# Create logs directory
os.makedirs(LOGS_DIR, exist_ok=True)

# Status file paths
SENSITIVITY_CONFIG_STATUS_PATH = os.path.join(LOGS_DIR, "sensitivity_config_status.json")
SENSITIVITY_CONFIG_DATA_PATH = os.path.join(LOGS_DIR, "sensitivity_config_data.pkl")
CONFIG_LOCK_FILE = os.path.join(LOGS_DIR, "sensitivity_config.lock")
RUN_LOCK_FILE = os.path.join(LOGS_DIR, "runs.lock")
VISUALIZATION_LOCK_FILE = os.path.join(LOGS_DIR, "visualization.lock")
PAYLOAD_LOCK_FILE = os.path.join(LOGS_DIR, "payload.lock")
BASELINE_LOCK_FILE = os.path.join(LOGS_DIR, "baseline.lock")

# Global locks for synchronization
GLOBAL_CONFIG_LOCK = threading.Lock()
GLOBAL_RUN_LOCK = threading.Lock()
GLOBAL_PRICE_LOCK = threading.Lock()
GLOBAL_VISUALIZE_LOCK = threading.Lock()
GLOBAL_PAYLOAD_LOCK = threading.Lock()
GLOBAL_BASELINE_LOCK = threading.Lock()

# Event flags for pipeline execution control
PAYLOAD_REGISTERED = threading.Event()
BASELINE_COMPLETED = threading.Event()
CONFIG_COMPLETED = threading.Event()
RUNS_COMPLETED = threading.Event()

# Timeout for waiting (in seconds)
WAIT_TIMEOUT = 600  # 10 minutes

# Pipeline active flag (holds all routes except the active one)
PIPELINE_ACTIVE = threading.Event()

# Script configurations
COMMON_PYTHON_SCRIPTS = [
    os.path.join(SCRIPT_DIR, "Configuration_management", 'formatter.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'module1.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'config_modules.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'Table.py')
]

def get_calculation_script(version):
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
    'freeFlowNPV': get_calculation_script
}

# =====================================
# Pipeline Control Functions
# =====================================
def reset_execution_pipeline():
    """Reset all execution pipeline events to initial state"""
    PAYLOAD_REGISTERED.clear()
    BASELINE_COMPLETED.clear()
    CONFIG_COMPLETED.clear()
    RUNS_COMPLETED.clear()
    PIPELINE_ACTIVE.clear()

def initialize_pipeline():
    """Initialize the pipeline and set it to active"""
    reset_execution_pipeline()
    PIPELINE_ACTIVE.set()
    return time.strftime("%Y%m%d_%H%M%S")

def cancel_pipeline_after_timeout(timeout_seconds=1800):
    """Cancel the pipeline after a timeout"""
    def timeout_handler():
        # Wait for timeout
        time.sleep(timeout_seconds)
        # If pipeline is still active, reset it
        if PIPELINE_ACTIVE.is_set():
            reset_execution_pipeline()
            print(f"Pipeline automatically reset after {timeout_seconds}s timeout")

    # Start timeout thread
    timer_thread = threading.Thread(target=timeout_handler)
    timer_thread.daemon = True
    timer_thread.start()
    return timer_thread

# =====================================
# Helper Functions
# =====================================
def with_file_lock(lock_file_path, operation_name="operation"):
    """Decorator to create a file lock for the decorated function"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock = filelock.FileLock(lock_file_path, timeout=180)  # 3 minute timeout
            try:
                with lock:
                    return func(*args, **kwargs)
            except filelock.Timeout:
                raise Exception(f"Timeout waiting for {operation_name} lock")
        return wrapper
    return decorator

def with_memory_lock(lock_obj, operation_name="operation"):
    """Decorator to apply a threading lock for the decorated function"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not lock_obj.acquire(timeout=180):  # 3 minute timeout
                raise Exception(f"Timeout waiting for in-memory {operation_name} lock")
            try:
                return func(*args, **kwargs)
            finally:
                lock_obj.release()
        return wrapper
    return decorator

def with_pipeline_check(required_event=None, next_event=None, operation_name="operation"):
    """Decorator to check pipeline status and validate required events"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if pipeline is active
            if not PIPELINE_ACTIVE.is_set():
                return jsonify({
                    "error": "Pipeline is not active",
                    "status": "inactive",
                    "message": "Initialize pipeline first with /register_payload"
                }), 409

            # Check if required event is set
            if required_event is not None and not required_event.is_set():
                return jsonify({
                    "error": f"Cannot execute {operation_name} - prerequisite step not completed",
                    "status": "blocked",
                    "message": f"This endpoint requires a prior step to complete first"
                }), 409

            # Execute the function
            result = func(*args, **kwargs)

            # Set next event if successful and provided
            if next_event is not None and isinstance(result, tuple) and result[1] == 200:
                next_event.set()

            return result
        return wrapper
    return decorator

def atomic_read_json(filepath):
    """Thread-safe reading of JSON file"""
    tempdir = tempfile.gettempdir()
    temp_file = os.path.join(tempdir, f"temp_{os.path.basename(filepath)}")

    # Create a file lock for this specific file
    lock_file = f"{filepath}.lock"
    lock = filelock.FileLock(lock_file, timeout=60)

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

def trigger_config_module_copy(version, sensitivity_dir, sen_parameters):
    """Thread-safe config module copying service trigger"""
    try:
        # Use a unique lock for this specific operation
        lock = threading.Lock()
        with lock:
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

    with version_lock:
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
        print(f"Results file not found: {results_path}")
        return None

    # Load results data
    try:
        with open(results_path, 'r') as f:
            results_data = json.load(f)
        return results_data
    except Exception as e:
        print(f"Error loading results data: {str(e)}")
        return None

# =====================================
# Flask Application Initialization
# =====================================
app = Flask(__name__)
CORS(app)

# Middleware to check if endpoint is allowed
@app.before_request
def check_endpoint_availability():
    # List of endpoints that should always be accessible
    always_accessible = [
        '/health',
        '/register_payload',
        '/status'
    ]

    # Get the current path
    path = request.path

    # Check if we're in active pipeline mode but not on an always accessible endpoint
    if PIPELINE_ACTIVE.is_set() and path not in always_accessible:
        # Allow baseline_calculation only if payload is registered but baseline not completed
        if path == '/baseline_calculation':
            if PAYLOAD_REGISTERED.is_set() and not BASELINE_COMPLETED.is_set():
                return None  # Allow request to proceed
            return jsonify({
                "error": "Baseline calculation cannot be executed at this time",
                "status": "incorrect_sequence",
                "message": "Register payload first or baseline already completed"
            }), 409

        # Allow sensitivity/configure only if baseline is completed but config not completed
        elif path == '/sensitivity/configure':
            if BASELINE_COMPLETED.is_set() and not CONFIG_COMPLETED.is_set():
                return None  # Allow request to proceed
            return jsonify({
                "error": "Sensitivity configuration cannot be executed at this time",
                "status": "incorrect_sequence",
                "message": "Complete baseline calculation first"
            }), 409

        # Allow runs only if config is completed but runs not completed
        elif path == '/runs':
            if CONFIG_COMPLETED.is_set() and not RUNS_COMPLETED.is_set():
                return None  # Allow request to proceed
            return jsonify({
                "error": "Runs cannot be executed at this time",
                "status": "incorrect_sequence",
                "message": "Complete sensitivity configuration first"
            }), 409

        # Block all other endpoints during active pipeline
        else:
            return jsonify({
                "error": "Endpoint temporarily unavailable",
                "status": "pipeline_active",
                "message": "Pipeline is active and only specific endpoints are available"
            }), 503

    # Allow access to always accessible endpoints or when pipeline is not active
    return None

# =====================================
# Pipeline Status Endpoint
# =====================================
@app.route('/status', methods=['GET'])
def get_pipeline_status():
    """Get current pipeline execution status"""
    status = {
        "pipeline_active": PIPELINE_ACTIVE.is_set(),
        "steps": {
            "payload_registered": PAYLOAD_REGISTERED.is_set(),
            "baseline_completed": BASELINE_COMPLETED.is_set(),
            "config_completed": CONFIG_COMPLETED.is_set(),
            "runs_completed": RUNS_COMPLETED.is_set()
        },
        "current_step": "none",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Determine current step
    if PIPELINE_ACTIVE.is_set():
        if not PAYLOAD_REGISTERED.is_set():
            status["current_step"] = "register_payload"
        elif not BASELINE_COMPLETED.is_set():
            status["current_step"] = "baseline_calculation"
        elif not CONFIG_COMPLETED.is_set():
            status["current_step"] = "sensitivity_configure"
        elif not RUNS_COMPLETED.is_set():
            status["current_step"] = "runs"
        else:
            status["current_step"] = "complete"

    return jsonify(status)

# =====================================
# Register Payload Endpoint
# =====================================
@app.route('/register_payload', methods=['POST'])
@with_file_lock(PAYLOAD_LOCK_FILE, "payload registration")
@with_memory_lock(GLOBAL_PAYLOAD_LOCK, "payload registration")
def register_payload():
    """Register payload and initialize pipeline"""
    try:
        # Initialize new pipeline (resets all events)
        run_id = initialize_pipeline()

        # Start timeout timer to automatically reset pipeline after 30 minutes
        cancel_pipeline_after_timeout(1800)

        data = request.get_json()
        if not data:
            PIPELINE_ACTIVE.clear()  # Reset pipeline active flag
            return jsonify({"error": "No data provided"}), 400

        # Store payload data
        payload_path = os.path.join(LOGS_DIR, f"payload_{run_id}.json")
        atomic_write_json(payload_path, data)

        # Set payload registered event
        PAYLOAD_REGISTERED.set()

        return jsonify({
            "status": "success",
            "message": "Payload registered successfully and pipeline initialized",
            "runId": run_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "next_step": "/baseline_calculation"
        }), 200
    except Exception as e:
        # Reset pipeline on error
        reset_execution_pipeline()
        return jsonify({
            "error": f"Error registering payload: {str(e)}",
            "status": "failed"
        }), 500
    # =====================================
# Baseline Calculation Endpoint
# =====================================
@app.route('/baseline_calculation', methods=['POST'], endpoint='baseline_calc_endpoint')
@with_file_lock(BASELINE_LOCK_FILE, "baseline calculation")
@with_memory_lock(GLOBAL_BASELINE_LOCK, "baseline calculation")
@with_pipeline_check(required_event=PAYLOAD_REGISTERED, next_event=BASELINE_COMPLETED, operation_name="baseline calculation")
def baseline_calculation():
    """Perform baseline calculation without sensitivity variations"""
    try:
        data = request.get_json()
        run_id = data.get('runId')

        # If no runtime data provided but runId is present, try to load from stored payload
        if run_id and (not data.get('selectedVersions') or not data.get('selectedCalculationOption')):
            payload_path = os.path.join(LOGS_DIR, f"payload_{run_id}.json")
            if os.path.exists(payload_path):
                stored_data = atomic_read_json(payload_path)
                if stored_data:
                    data.update(stored_data)

        # Extract configuration
        version = data.get('selectedVersions', [1])[0]
        selectedV = data.get('selectedV', {f'V{i+1}': 'off' for i in range(10)})
        selectedF = data.get('selectedF', {f'F{i+1}': 'off' for i in range(5)})
        calculation_option = data.get('selectedCalculationOption', 'freeFlowNPV')
        target_row = int(data.get('targetRow', 20))

        # Get calculation script
        calculation_script_func = CALCULATION_SCRIPTS.get(calculation_option)
        if not calculation_script_func:
            BASELINE_COMPLETED.clear()  # Reset baseline completion flag
            return jsonify({
                "error": f"No script found for calculation mode: {calculation_option}",
                "status": "error"
            }), 400

        calculation_script = calculation_script_func(version)

        # Execute configuration management scripts first
        for script in COMMON_PYTHON_SCRIPTS:
            script_name = os.path.basename(script)

            result = subprocess.run(
                ['python', script, str(version)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = f"Script execution failed: {script_name}\nError: {result.stderr}"
                BASELINE_COMPLETED.clear()  # Reset baseline completion flag
                return jsonify({
                    "error": error_msg,
                    "status": "error"
                }), 500

            time.sleep(0.5)  # Ensure proper sequencing

        # Run baseline calculation
        start_time = time.time()
        result = subprocess.run(
            [
                'python',
                calculation_script,
                str(version),
                json.dumps(selectedV),
                json.dumps(selectedF),
                str(target_row),
                calculation_option,
                '{}'  # Empty SenParameters for baseline
            ],
            capture_output=True,
            text=True
        )

        execution_time = time.time() - start_time

        if result.returncode != 0:
            error_msg = f"Baseline calculation failed: {result.stderr}"
            BASELINE_COMPLETED.clear()  # Reset baseline completion flag
            return jsonify({
                "error": error_msg,
                "status": "error"
            }), 500

        # Store calculation result
        result_path = os.path.join(LOGS_DIR, f"baseline_result_{run_id}.json")
        atomic_write_json(result_path, {
            "version": version,
            "calculationOption": calculation_option,
            "targetRow": target_row,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "executionTime": execution_time,
            "stdout": result.stdout,
            "returnCode": result.returncode
        })

        # BASELINE_COMPLETED event is set by the decorator

        return jsonify({
            "status": "success",
            "message": "Baseline calculation completed successfully",
            "runId": run_id,
            "version": version,
            "executionTime": f"{execution_time:.2f}s",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "next_step": "/sensitivity/configure"
        }), 200
    except Exception as e:
        # Don't clear event flag here - let the decorator handle it
        return jsonify({
            "error": f"Error during baseline calculation: {str(e)}",
            "status": "error"
        }), 500

# =====================================
# Sensitivity Configuration Endpoint
# =====================================
@app.route('/sensitivity/configure', methods=['POST'], endpoint='sensitivity_configure_endpoint')
@with_file_lock(CONFIG_LOCK_FILE, "sensitivity configuration")
@with_memory_lock(GLOBAL_CONFIG_LOCK, "sensitivity configuration")
@with_pipeline_check(required_event=BASELINE_COMPLETED, next_event=CONFIG_COMPLETED, operation_name="sensitivity configuration")
def configure_sensitivity():
    """Generate and save sensitivity configurations"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        run_id = data.get('runId')

        # If no runtime data provided but runId is present, try to load from stored payload
        if run_id and (not data.get('selectedVersions') or not data.get('SenParameters')):
            payload_path = os.path.join(LOGS_DIR, f"payload_{run_id}.json")
            if os.path.exists(payload_path):
                stored_data = atomic_read_json(payload_path)
                if stored_data:
                    data.update(stored_data)

        # Extract configuration
        config = {
            'versions': data.get('selectedVersions', [1]),
            'selectedV': data.get('selectedV', {f'V{i+1}': 'off' for i in range(10)}),
            'selectedF': data.get('selectedF', {f'F{i+1}': 'off' for i in range(5)}),
            'calculationOption': data.get('selectedCalculationOption', 'freeFlowNPV'),
            'targetRow': int(data.get('targetRow', 20)),
            'SenParameters': data.get('SenParameters', {})
        }

        version = config['versions'][0]

        # Create sensitivity directories with thread-safe function
        start_time = time.time()
        sensitivity_dir, config_dir = create_sensitivity_directories(version, config['SenParameters'])

        # Save configuration files with thread-safe function
        saved_files = save_sensitivity_config_files(version, config_dir, config['SenParameters'])

        # Save configuration status using atomic write
        atomic_write_json(SENSITIVITY_CONFIG_STATUS_PATH, {
            'configured': True,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'runId': run_id,
            'version': version,
            'configDir': config_dir,
            'sensitivityDir': sensitivity_dir
        })

        # Save configuration data using atomic write
        atomic_write_pickle(SENSITIVITY_CONFIG_DATA_PATH, config)

        # CONFIG_COMPLETED event is set by the decorator

        execution_time = time.time() - start_time

        return jsonify({
            "status": "success",
            "message": "Sensitivity configurations generated and saved successfully",
            "runId": run_id,
            "configDir": config_dir,
            "sensitivityDir": sensitivity_dir,
            "savedFiles": len(saved_files),
            "executionTime": f"{execution_time:.2f}s",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "next_step": "/runs"
        }), 200

    except Exception as e:
        # Don't clear event flag here - let the decorator handle it

        # Update configuration status to indicate failure using atomic write
        atomic_write_json(SENSITIVITY_CONFIG_STATUS_PATH, {
            'configured': False,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'runId': run_id if 'run_id' in locals() else time.strftime("%Y%m%d_%H%M%S"),
            'error': str(e)
        })

        return jsonify({
            "error": f"Error generating sensitivity configurations: {str(e)}",
            "status": "error"
        }), 500

# =====================================
# Run Calculations Endpoint
# =====================================
@app.route('/runs', methods=['POST'], endpoint='runs_endpoint')
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

# =====================================
# Calculate Sensitivity Endpoint
# =====================================
@app.route('/calculate-sensitivity', methods=['POST'])
@with_file_lock(RUN_LOCK_FILE, "sensitivity calculations")
@with_memory_lock(GLOBAL_RUN_LOCK, "sensitivity calculations")
def calculate_sensitivity():
    """
    Execute specific sensitivity calculations using CFA-b.py with paths from CalSen service.
    This endpoint runs after the general sensitivity configurations and runs have completed.
    It leverages the CalSen service for path resolution to ensure consistent file locations.
    """
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        # Check if sensitivity configurations have been generated using thread-safe function
        is_configured, saved_config = check_sensitivity_config_status()

        if not is_configured:
            return jsonify({
                "error": "Sensitivity configurations have not been generated yet",
                "message": "Please complete the /sensitivity/configure and /runs endpoints before calculating specific sensitivities",
                "nextStep": "Call /sensitivity/configure endpoint first"
            }), 400

        # Use the saved configuration data if available, otherwise use the request data
        data = request.get_json()
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

        # Get version and base paths
        version = config['versions'][0]
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        results_folder = os.path.join(base_dir, f'Batch({version})', f'Results({version})')
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')

        # Get CFA-b.py script path
        cfa_b_script = get_sensitivity_calculation_script()

        # Process enabled sensitivity parameters
        enabled_params = [(param_id, param_config) for param_id, param_config
                          in config['SenParameters'].items() if param_config.get('enabled')]

        if not enabled_params:
            return jsonify({
                "status": "warning",
                "message": "No enabled sensitivity parameters found for calculation",
                "runId": run_id
            })

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

        # Process each parameter with thread-safe approach
        for param_id, param_config in enabled_params:
            mode = param_config.get('mode', 'percentage')
            values = param_config.get('values', [])
            compare_to_key = param_config.get('compareToKey', 'S13')

            if not values:
                continue

            # Determine variations based on mode
            variations = []
            for value in values:
                if value is not None:
                    try:
                        variations.append(float(value))
                    except (ValueError, TypeError):
                        pass

            if not variations:
                continue

            param_results = {"variations": {}, "success": True}

            # Process each variation with thread-safe approach
            param_lock = threading.Lock()
            with param_lock:
                for variation in variations:
                    var_str = f"{variation:+.2f}"

                    # Create mode directory if it doesn't exist
                    mode_dir = mode_dir_mapping.get(mode.lower(), 'Percentage')
                    mode_path = os.path.join(sensitivity_dir, mode_dir)
                    os.makedirs(mode_path, exist_ok=True)

                    # Create parameter directory if it doesn't exist
                    param_path = os.path.join(mode_path, param_id)
                    os.makedirs(param_path, exist_ok=True)

                    # Create variation directory if it doesn't exist
                    var_path = os.path.join(param_path, var_str)
                    os.makedirs(var_path, exist_ok=True)

                    # Run CFA-b.py for this variation
                    try:
                        # Use atomic operations for thread safety
                        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_file:
                            # Create a temporary config file for this run
                            temp_config = {
                                "version": version,
                                "param_id": param_id,
                                "variation": variation,
                                "compare_to_key": compare_to_key,
                                "mode": mode,
                                "output_dir": var_path
                            }
                            json.dump(temp_config, temp_file)
                            temp_file_path = temp_file.name

                        # Run the calculation script with the temporary config file
                        result = subprocess.run(
                            [sys.executable, cfa_b_script, 
                             '--config', temp_file_path,
                             '--version', str(version),
                             '--param', param_id,
                             '--variation', str(variation),
                             '--compare', compare_to_key,
                             '--mode', mode],
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minute timeout
                        )

                        # Clean up the temporary file
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass

                        # Check if calculation was successful
                        if result.returncode == 0:
                            # Save results to a JSON file
                            results_file = os.path.join(
                                mode_path,
                                f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
                            )

                            # Create or update results file
                            try:
                                if os.path.exists(results_file):
                                    with open(results_file, 'r') as f:
                                        existing_results = json.load(f)

                                    # Update existing results
                                    if 'variations' in existing_results:
                                        existing_results['variations'][var_str] = {
                                            'value': variation,
                                            'success': True
                                        }
                                    else:
                                        existing_results['variations'] = {
                                            var_str: {
                                                'value': variation,
                                                'success': True
                                            }
                                        }

                                    # Write updated results
                                    with open(results_file, 'w') as f:
                                        json.dump(existing_results, f, indent=2)
                                else:
                                    # Create new results file
                                    new_results = {
                                        'param_id': param_id,
                                        'compare_to_key': compare_to_key,
                                        'mode': mode,
                                        'variations': {
                                            var_str: {
                                                'value': variation,
                                                'success': True
                                            }
                                        }
                                    }
                                    with open(results_file, 'w') as f:
                                        json.dump(new_results, f, indent=2)
                            except Exception as e:
                                # Log error but continue processing
                                print(f"Error saving results for {param_id} variation {var_str}: {str(e)}")

                            # Update param_results
                            param_results['variations'][var_str] = {
                                'value': variation,
                                'success': True
                            }
                        else:
                            # Update param_results with error
                            param_results['variations'][var_str] = {
                                'value': variation,
                                'success': False,
                                'error': result.stderr
                            }
                            param_results['success'] = False
                            overall_success = False

                    except subprocess.TimeoutExpired:
                        # Update param_results with timeout error
                        param_results['variations'][var_str] = {
                            'value': variation,
                            'success': False,
                            'error': 'Calculation timed out after 5 minutes'
                        }
                        param_results['success'] = False
                        overall_success = False

                    except Exception as e:
                        # Update param_results with general error
                        param_results['variations'][var_str] = {
                            'value': variation,
                            'success': False,
                            'error': str(e)
                        }
                        param_results['success'] = False
                        overall_success = False

            # Add param_results to calculation_results
            calculation_results[param_id] = param_results

        # Return results
        return jsonify({
            "status": "success" if overall_success else "partial_success",
            "message": "Sensitivity calculations completed",
            "runId": run_id,
            "results": calculation_results
        })

    except Exception as e:
        return jsonify({
            "error": f"Error during sensitivity calculations: {str(e)}",
            "runId": run_id
        }), 500

# =====================================
# Sensitivity Visualization Endpoint
# =====================================
@app.route('/api/sensitivity/visualize', methods=['POST'])
@with_file_lock(VISUALIZATION_LOCK_FILE, "sensitivity visualization")
@with_memory_lock(GLOBAL_VISUALIZE_LOCK, "sensitivity visualization")
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
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract parameters
        version = data.get('version', 1)
        param_id = data.get('param_id')
        mode = data.get('mode', 'percentage')
        compare_to_key = data.get('compareToKey', 'S13')
        plot_types = data.get('plotTypes', ['waterfall', 'bar', 'point'])

        if not param_id:
            return jsonify({"error": "Parameter ID is required"}), 400

        # Get sensitivity data using thread-safe approach
        sensitivity_data = get_sensitivity_data(version, param_id, mode, compare_to_key)
        if not sensitivity_data:
            error_msg = f"No data available for {param_id} in {mode} mode"
            return jsonify({
                "error": "Sensitivity data not found",
                "message": error_msg
            }), 404

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

        for plot_type in plot_types:
            plot_name = f"{plot_type}_{param_id}_{compare_to_key}_primary.png"
            plot_path = os.path.join(sensitivity_dir, plot_type, plot_name)

            if os.path.exists(plot_path):
                plots_info[plot_type] = {
                    "status": "available",
                    "path": os.path.relpath(plot_path, base_dir)
                }
            else:
                # Create plot directory if it doesn't exist
                plot_dir = os.path.join(sensitivity_dir, plot_type)
                os.makedirs(plot_dir, exist_ok=True)

                try:
                    # Generate plot using thread-safe approach
                    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_file:
                        # Create a temporary config file for plot generation
                        temp_config = {
                            "version": version,
                            "param_id": param_id,
                            "compare_to_key": compare_to_key,
                            "plot_type": plot_type,
                            "mode": mode,
                            "output_dir": plot_dir
                        }
                        json.dump(temp_config, temp_file)
                        temp_file_path = temp_file.name

                    # Run plot generation script
                    plot_script = os.path.join(SCRIPT_DIR, "API_endpoints_and_controllers", "generate_sensitivity_plot.py")
                    if os.path.exists(plot_script):
                        result = subprocess.run(
                            [sys.executable, plot_script, 
                             '--config', temp_file_path],
                            capture_output=True,
                            text=True,
                            timeout=60  # 1 minute timeout
                        )

                        # Clean up the temporary file
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass

                        # Check if plot generation was successful
                        if result.returncode == 0 and os.path.exists(plot_path):
                            plots_info[plot_type] = {
                                "status": "generated",
                                "path": os.path.relpath(plot_path, base_dir)
                            }
                        else:
                            plots_info[plot_type] = {
                                "status": "error",
                                "message": f"Failed to generate {plot_type} plot: {result.stderr}"
                            }
                    else:
                        plots_info[plot_type] = {
                            "status": "error",
                            "message": "Plot generation script not found"
                        }
                except Exception as e:
                    plots_info[plot_type] = {
                        "status": "error",
                        "message": f"Error generating {plot_type} plot: {str(e)}"
                    }

        # Prepare visualization data
        visualization_data = {
            "status": "success",
            "param_id": param_id,
            "compare_to_key": compare_to_key,
            "mode": mode,
            "data": sensitivity_data,
            "plots": plots_info,
            "runId": run_id
        }

        return jsonify(visualization_data)

    except Exception as e:
        return jsonify({
            "error": f"Error generating visualization: {str(e)}"
        }), 500

# =====================================
# Get Sensitivity Parameters Endpoint
# =====================================
@app.route('/api/sensitivity/parameters', methods=['GET'])
def get_sensitivity_parameters():
    """Get all available sensitivity parameters for visualization."""
    run_id = time.strftime("%Y%m%d_%H%M%S")

    try:
        version = request.args.get('version', '1')

        # Try to get parameters from CalSen service first
        try:
            response = requests.post(
                "http://localhost:2750/list_parameters",
                json={"version": int(version)},
                timeout=5
            )

            if response.status_code == 200:
                return jsonify(response.json())
        except Exception:
            # Continue with fallback
            pass

        # Fallback: scan directories with thread-safe approach
        base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
        sensitivity_dir = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity'
        )

        if not os.path.exists(sensitivity_dir):
            error_msg = f"No sensitivity data found for version {version}"
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 404

        # Look for parameter directories (starting with S)
        parameters = []

        # Use a lock for thread safety when scanning directories
        scan_lock = threading.Lock()
        with scan_lock:
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

        return jsonify({
            "status": "success",
            "version": version,
            "parameters": parameters,
            "source": "directory"
        })

    except Exception as e:
        return jsonify({
            "error": f"Error retrieving sensitivity parameters: {str(e)}"
        }), 500

# =====================================
# Run All Sensitivity Endpoint
# =====================================
@app.route('/run-all-sensitivity', methods=['POST'])
def run_all_sensitivity():
    """
    Unified wrapper to execute all sensitivity endpoints sequentially.
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
            return r.json()

        def get(path):
            r = requests.get(f"{base_url}{path}")
            return r.json()

        # Execute the full pipeline in sequence
        result = {
            "configure": post('/sensitivity/configure'),
            "runs": post('/runs')
        }

        # If specific parameters are enabled, run calculations for each
        if enabled_params:
            param_results = {}
            for param_id in enabled_params:
                param_payload = {
                    "version": version,
                    "param_id": param_id,
                    "SenParameters": {
                        param_id: {"enabled": True}
                    }
                }
                param_results[param_id] = post('/calculate-sensitivity', param_payload)
            result["calculate_sensitivity"] = param_results

        # Check if calsen_paths.json exists
        result["check_calsen_paths"] = get(f'/check-calsen-paths?version={version}')

        # Run script_econ.py
        if result["check_calsen_paths"].get("exists", False):
            result["run_script_econ"] = post('/run-script-econ', {"version": version})

        return jsonify({
            "status": "success",
            "message": "All sensitivity routes triggered via unified endpoint.",
            "results": result
        })

    except Exception as e:
        return jsonify({
            "error": f"Error executing unified sensitivity runner: {str(e)}"
        }), 500

# =====================================
# Check CalSen Paths Endpoint
# =====================================
@app.route('/check-calsen-paths', methods=['GET'])
def check_calsen_paths():
    """
    Check if calsen_paths.json exists for the specified version.
    """
    version = request.args.get('version', '1')

    # Calculate path to calsen_paths.json
    base_dir = os.path.join(BASE_DIR, 'backend', 'Original')
    sensitivity_dir = os.path.join(base_dir, f'Batch({version})', f'Results({version})', 'Sensitivity')
    reports_dir = os.path.join(sensitivity_dir, 'Reports')
    calsen_paths_file = os.path.join(reports_dir, 'calsen_paths.json')

    # Check if file exists with thread-safe approach
    file_check_lock = threading.Lock()
    with file_check_lock:
        file_exists = os.path.exists(calsen_paths_file)

    # Include payload details for monitoring
    payload_details = {
        "operation": "check_calsen_paths",
        "version": version,
        "path": calsen_paths_file,
        "exists": file_exists
    }

    return jsonify({
        'exists': file_exists,
        'path': calsen_paths_file
    })

# =====================================
# Run Script Econ Endpoint
# =====================================
@app.route('/run-script-econ', methods=['POST'])
def run_script_econ():
    """
    Execute script_econ.py to extract metrics from Economic Summary CSV files
    and append them to calsen_paths.json.
    """
    data = request.get_json()
    version = data.get('version', '1')

    try:
        # Get path to script_econ.py
        script_path = os.path.join(BASE_DIR, 'backend', 'API_endpoints_and_controllers', 'script_econ.py')

        # Execute script_econ.py with the version argument
        result = run_script(
            script_path,
            '--version', version,
            script_type="python"
        )

        return jsonify({
            'status': 'success',
            'message': 'script_econ.py executed successfully',
            'stdout': result.get('stdout', ''),
            'stderr': result.get('stderr', '')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error executing script_econ.py: {str(e)}'
        }), 500

# =====================================
# Run Add Axis Labels Endpoint
# =====================================
@app.route('/run-add-axis-labels', methods=['POST'])
def run_add_axis_labels():
    """
    Execute add_axis_labels.py to add axis labels to sensitivity plots.
    """
    data = request.get_json()
    version = data.get('version', '1')
    param_id = data.get('param_id')
    compare_to_key = data.get('compareToKey', 'S13')

    if not param_id:
        return jsonify({"error": "Parameter ID is required"}), 400

    try:
        # Get path to add_axis_labels.py
        script_path = os.path.join(BASE_DIR, 'backend', 'API_endpoints_and_controllers', 'add_axis_labels.py')

        # Execute add_axis_labels.py with the arguments
        result = run_script(
            script_path,
            '--version', version,
            '--param', param_id,
            '--compare', compare_to_key,
            script_type="python"
        )

        return jsonify({
            'status': 'success',
            'message': 'add_axis_labels.py executed successfully',
            'stdout': result.get('stdout', ''),
            'stderr': result.get('stderr', '')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error executing add_axis_labels.py: {str(e)}'
        }), 500

# =====================================
# Run Generate Plots Endpoint
# =====================================
@app.route('/run-generate-plots', methods=['POST'])
def run_generate_plots():
    """
    Execute generate_plots.py to generate sensitivity plots.
    """
    data = request.get_json()
    version = data.get('version', '1')
    param_id = data.get('param_id')
    compare_to_key = data.get('compareToKey', 'S13')
    plot_type = data.get('plotType', 'waterfall')

    if not param_id:
        return jsonify({"error": "Parameter ID is required"}), 400

    try:
        # Get path to generate_plots.py
        script_path = os.path.join(BASE_DIR, 'backend', 'API_endpoints_and_controllers', 'generate_plots.py')

        # Execute generate_plots.py with the arguments
        result = run_script(
            script_path,
            '--version', version,
            '--param', param_id,
            '--compare', compare_to_key,
            '--type', plot_type,
            script_type="python"
        )

        return jsonify({
            'status': 'success',
            'message': 'generate_plots.py executed successfully',
            'stdout': result.get('stdout', ''),
            'stderr': result.get('stderr', '')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error executing generate_plots.py: {str(e)}'
        }), 500

# =====================================
# Pipeline Reset Endpoint
# =====================================
@app.route('/reset_pipeline', methods=['POST'])
def reset_pipeline():
    """Reset the execution pipeline and clear all event flags"""
    reset_execution_pipeline()
    return jsonify({
        "status": "success",
        "message": "Pipeline reset successfully",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

# =====================================
# Health Check Endpoint
# =====================================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint that's always accessible"""
    # Check if the 2600 service is running
    config_copy_service_status = "available"
    try:
        response = requests.get("http://localhost:2600/health", timeout=2)
        if not response.ok:
            config_copy_service_status = "unavailable"
    except requests.exceptions.RequestException:
        config_copy_service_status = "unavailable"

    return jsonify({
        "status": "ok",
        "server": "sensitivity-analysis-server-with-pipeline-control",
        "version": "2.0.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pipeline": {
            "active": PIPELINE_ACTIVE.is_set(),
            "payload_registered": PAYLOAD_REGISTERED.is_set(),
            "baseline_completed": BASELINE_COMPLETED.is_set(),
            "config_completed": CONFIG_COMPLETED.is_set(),
            "runs_completed": RUNS_COMPLETED.is_set()
        },
        "services": {
            "config_copy_service": config_copy_service_status
        }
    })

# =====================================
# Application Entry Point
# =====================================
if __name__ == '__main__':
    # Ensure all lock files are cleaned up on startup
    for lock_file in [CONFIG_LOCK_FILE, RUN_LOCK_FILE, VISUALIZATION_LOCK_FILE,
                      PAYLOAD_LOCK_FILE, BASELINE_LOCK_FILE]:
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except:
                pass

    # Initialize event flags
    reset_execution_pipeline()

    app.run(debug=True, host='127.0.0.1', port=2500)
