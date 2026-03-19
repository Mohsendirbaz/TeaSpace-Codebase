from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import subprocess
import os
import logging
import json
import time
import sys
import threading
from queue import Queue
from tabulate import tabulate
from datetime import datetime

# Define script directory (relative to this file)
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base_dir = SCRIPT_DIR  # Keep for backward compatibility
sys.path.append(base_dir)

# =====================================
# Configuration Constants
# =====================================

# Default state configurations
DEFAULT_V_STATES = {f'V{i+1}': 'off' for i in range(10)}
DEFAULT_F_STATES = {f'F{i+1}': 'off' for i in range(5)}
DEFAULT_TARGET_ROW = 20
DEFAULT_CALCULATION_OPTION = 'calculateForPrice'

# Default optimization parameters
DEFAULT_TOLERANCE_LOWER = -1000
DEFAULT_TOLERANCE_UPPER = 1000
DEFAULT_INCREASE_RATE = 1.02
DEFAULT_DECREASE_RATE = 0.985

# =====================================
# Script Configurations
# =====================================

COMMON_PYTHON_SCRIPTS = [
    os.path.join(SCRIPT_DIR, "Configuration_management", 'formatter.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'module1.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'config_modules.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'Table.py')
]

CALCULATION_SCRIPTS = {
    'calculateForPrice': os.path.join(SCRIPT_DIR, "Core_calculation_engines", 'CFA.py')
}

# =====================================
# Logging Configuration
# =====================================

# Configure logger
log_file = os.path.join(SCRIPT_DIR, "Logs", "CFA_CALC.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logger = logging.getLogger("CalculationsLogger")
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

# =====================================
# Helper Functions
# =====================================

def log_state_parameters(versions, v_states, f_states,r_states, rf_states, calculation_option, target_row,
                        tolerance_lower, tolerance_upper, increase_rate, decrease_rate, sen_parameters):
    """Log state parameters in a structured, tabulated format"""

    # Log versions
    logger.info(f"Processing versions: {versions}")

    # Log V states (enabled/disabled)
    v_enabled = [k for k, v in v_states.items() if v == 'on']
    v_disabled = [k for k, v in v_states.items() if v == 'off']
    logger.info(f"V states - Enabled: {v_enabled}, Disabled: {v_disabled}")

    # Log F states (enabled/disabled)
    f_enabled = [k for k, v in f_states.items() if v == 'on']
    f_disabled = [k for k, v in f_states.items() if v == 'off']
    logger.info(f"F states - Enabled: {f_enabled}, Disabled: {f_disabled}")

    # Log R states (enabled/disabled)
    r_enabled = [k for k, v in r_states.items() if v == 'on']
    r_disabled = [k for k, v in r_states.items() if v == 'off']

    logger.info(f"R states - Enabled: {r_enabled}, Disabled: {r_disabled}")

    # Log RF states
    rf_enabled = [k for k, v in rf_states.items() if v == 'on']
    rf_disabled = [k for k, v in rf_states.items() if v == 'off']

    logger.info(f"RF states - Enabled: {rf_enabled}, Disabled: {rf_disabled}")
    # Log calculation options
    logger.info(f"Calculation option: {calculation_option}, Target row: {target_row}")

    # Log optimization parameters
    if calculation_option == 'calculateForPrice':
        logger.info(f"Price optimization parameters:")
        logger.info(f"  - Tolerance bounds: Lower={tolerance_lower}, Upper={tolerance_upper}")
        logger.info(f"  - Adjustment rates: Increase={increase_rate}, Decrease={decrease_rate}")

    # Log sensitivity parameters in tabular format if they exist
    if sen_parameters:
        # Extract relevant sensitivity parameters
        sen_table_data = []
        headers = ["Parameter", "Enabled", "Mode", "Compare To", "Comparison Type", "Visualization"]

        for param, config in sen_parameters.items():
            if isinstance(config, dict):
                visualization = []
                if config.get('waterfall'):
                    visualization.append('Waterfall')
                if config.get('bar'):
                    visualization.append('Bar')
                if config.get('point'):
                    visualization.append('Point')

                sen_table_data.append([
                    param,
                    "Yes" if config.get('enabled') else "No",
                    config.get('mode', 'N/A'),
                    config.get('compareToKey', 'N/A'),
                    config.get('comparisonType', 'N/A'),
                    ", ".join(visualization) if visualization else "None"
                ])

        if sen_table_data:
            table = tabulate(sen_table_data, headers=headers, tablefmt="grid")
            logger.info(f"Sensitivity Parameters:\n{table}")

# =====================================
# Script Execution Functions
# =====================================

def run_script(script_name, *args, script_type="python"):
    try:
        command = ['python' if script_type == "python" else 'Rscript', script_name]
        command.extend([str(arg) for arg in args])

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            error_msg = f"Error running {os.path.basename(script_name)}: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg

        logger.info(f"Successfully ran {os.path.basename(script_name)}" + 
                    (f" for version {args[0]}" if args else ""))
        return True, None

    except Exception as e:
        error_msg = f"Exception running {os.path.basename(script_name)}: {str(e)}"
        logger.exception(error_msg)
        return False, error_msg

def process_version(version, calculation_script, selected_v, selected_f, selected_r, selected_rf, target_row,
                   calculation_option, tolerance_lower, tolerance_upper, increase_rate, decrease_rate, sen_parameters):
    try:
        # Log the start of processing for this version
        logger.info(f"Starting processing for version {version}")

        # Run common scripts first
        for script in COMMON_PYTHON_SCRIPTS:
            success, error = run_script(script, version)
            if not success:
                logger.error(f"Failed to run common script for version {version}: {error}")
                return error

        # Run the calculation script with all parameters
        success, error = run_script(
            calculation_script,
            version,
            json.dumps(selected_v),
            json.dumps(selected_f),
            json.dumps(selected_r),
            json.dumps(selected_rf),
            target_row,
            calculation_option,
            tolerance_lower,
            tolerance_upper,
            increase_rate,
            decrease_rate,
            json.dumps(sen_parameters)
        )
        if not success:
            logger.error(f"Failed to run calculation script for version {version}: {error}")
            return error

        logger.info(f"Successfully completed processing for version {version}")
        return None
    except Exception as e:
        error_msg = f"Error processing version {version}: {str(e)}"
        logger.exception(error_msg)
        return error_msg
# =====================================
# Price Optimization Streaming
# =====================================

# Import queue for thread-safe communication
import queue
from queue import Queue

# Dictionary to store active monitoring threads
active_monitors = {}

class PriceOptimizationMonitor:
    """
    Class to monitor price optimization status files and emit SSE events.
    """
    def __init__(self, version):
        """Initialize the monitor for a specific version."""
        self.version = version
        self.status_file_path = self._get_status_file_path()
        self.running = False
        self.clients = []
        self.last_data = None
        self.last_modified_time = 0
        logger.info(f"Initialized monitor for version {version}, status file: {self.status_file_path}")

    def _get_status_file_path(self):
        """Get the path to the status file for this version."""
        # Construct path to the status file
        results_folder = os.path.join(SCRIPT_DIR, "..", "..", "Original", 
            f"Batch({self.version})", f"Results({self.version})"
        )
        return os.path.join(results_folder, f"price_optimization_status_{self.version}.json")

    def _get_fallback_price_file(self):
        """Get the path to the optimal price file as a fallback."""
        results_folder = os.path.join(SCRIPT_DIR, "..", "..", "Original", 
            f"Batch({self.version})", f"Results({self.version})"
        )
        return os.path.join(results_folder, f"optimal_price_{self.version}.json")

    def add_client(self, client_queue):
        """Add a client to the monitor."""
        self.clients.append(client_queue)
        logger.info(f"Client added to monitor for version {self.version}. Total clients: {len(self.clients)}")

        # If we already have data, send it to the new client immediately
        if self.last_data:
            client_queue.put(self.last_data)

        # Start the monitoring thread if not already running
        if not self.running:
            self.start()

    def remove_client(self, client_queue):
        """Remove a client from the monitor."""
        if client_queue in self.clients:
            self.clients.remove(client_queue)
            logger.info(f"Client removed from monitor for version {self.version}. Remaining clients: {len(self.clients)}")

        # Stop the monitoring thread if no clients remain
        if not self.clients and self.running:
            self.stop()

    def start(self):
        """Start the monitoring thread."""
        self.running = True
        thread = threading.Thread(target=self._monitor_loop)
        thread.daemon = True
        thread.start()
        logger.info(f"Monitoring thread started for version {self.version}")

    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        logger.info(f"Monitoring stopped for version {self.version}")

        # Remove this monitor from the global active monitors
        if self.version in active_monitors:
            del active_monitors[self.version]

    def _monitor_loop(self):
        """Main monitoring loop to check for file changes and notify clients."""
        check_interval = 0.5  # Check every half second
        consecutive_errors = 0
        max_errors = 20  # Stop monitoring after this many consecutive errors

        while self.running and consecutive_errors < max_errors:
            try:
                # Check if the status file exists
                if os.path.exists(self.status_file_path):
                    # Get the last modified time
                    current_modified_time = os.path.getmtime(self.status_file_path)

                    # If the file has been modified since our last check
                    if current_modified_time > self.last_modified_time:
                        self.last_modified_time = current_modified_time

                        # Read the file and parse the JSON
                        with open(self.status_file_path, 'r') as f:
                            status_data = json.load(f)

                        # Prepare the event data with enhanced information
                        event_data = {
                            'version': self.version,
                            'price': status_data.get('current_price'),
                            'npv': status_data.get('current_npv'),
                            'iteration': status_data.get('iteration', 0),
                            'complete': status_data.get('complete', False),
                            'success': status_data.get('success', False),
                            'error': status_data.get('error'),
                            'timestamp': datetime.now().isoformat(),
                            # Enhanced information for calculation steps
                            'calculationStep': status_data.get('calculation_step', ''),
                            'calculationDetails': status_data.get('calculation_details', {}),
                            # Enhanced information for payload details
                            'payloadDetails': status_data.get('payload_details', {}),
                            # Additional information that might be useful
                            'progressPercentage': status_data.get('progress_percentage', 0)
                        }

                        # Store the last data for new clients
                        self.last_data = event_data

                        # Notify all clients
                        for client in list(self.clients):
                            try:
                                client.put(event_data)
                            except Exception as e:
                                logger.error(f"Error sending to client: {str(e)}")
                                self.clients.remove(client)

                        # If calculation is complete, send one more message then stop
                        if status_data.get('complete', False):
                            logger.info(f"Calculation complete for version {self.version}")
                            time.sleep(1)  # Give clients time to process the last message
                            for client in list(self.clients):
                                try:
                                    client.put({
                                        'version': self.version,
                                        'complete': True,
                                        'message': "Calculation complete",
                                        'timestamp': datetime.now().isoformat()
                                    })
                                except Exception:
                                    pass
                            # Stop monitoring
                            self.stop()
                            break

                        consecutive_errors = 0

                # If status file doesn't exist, check for optimal price file
                elif os.path.exists(self._get_fallback_price_file()):
                    try:
                        with open(self._get_fallback_price_file(), 'r') as f:
                            price_data = json.load(f)

                        # Prepare the event data
                        event_data = {
                            'version': self.version,
                            'price': price_data.get('price'),
                            'npv': price_data.get('npv'),
                            'complete': True,
                            'success': True,
                            'message': "Calculation was completed previously",
                            'timestamp': datetime.now().isoformat()
                        }

                        # Store the last data for new clients
                        self.last_data = event_data

                        # Notify all clients
                        for client in list(self.clients):
                            try:
                                client.put(event_data)
                            except Exception:
                                self.clients.remove(client)

                        # Stop monitoring
                        logger.info(f"Found optimal price file for version {self.version}")
                        self.stop()
                        break

                    except Exception as e:
                        logger.error(f"Error reading optimal price file: {str(e)}")
                        consecutive_errors += 1

                else:
                    # Neither file exists yet
                    consecutive_errors += 1
                    if consecutive_errors % 5 == 0:  # Log every 5th error
                        logger.warning(f"Status file not found for version {self.version}, consecutive errors: {consecutive_errors}")

            except Exception as e:
                logger.error(f"Error in monitoring loop for version {self.version}: {str(e)}")
                consecutive_errors += 1

            # Sleep before next check
            time.sleep(check_interval)

        if consecutive_errors >= max_errors:
            logger.error(f"Too many consecutive errors for version {self.version}, stopping monitor")
            # Notify clients of the error
            for client in self.clients:
                try:
                    client.put({
                        'version': self.version,
                        'error': "Monitoring stopped due to too many errors",
                        'complete': True,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception:
                    pass
            self.stop()

# =====================================
# Flask Application Initialization
# =====================================

def initialize_app():
    app = Flask(__name__)
    CORS(app)
    return app

app = initialize_app()

# =====================================
# Streaming Endpoints
# =====================================

@app.route('/stream_price/<version>', methods=['GET'])
def stream_price(version):
    """
    Stream real-time price optimization updates for a specific version using Server-Sent Events (SSE).
    This endpoint connects to a PriceOptimizationMonitor that watches status files for changes.
    """
    def generate():
        """Generator function for the SSE stream."""
        # Create a queue for this client
        client_queue = Queue()

        # Get or create a monitor for this version
        if version not in active_monitors:
            active_monitors[version] = PriceOptimizationMonitor(version)

        # Add this client to the monitor
        active_monitors[version].add_client(client_queue)

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'status': 'connected', 'version': version, 'timestamp': datetime.now().isoformat()})}\n\n"

            while True:
                # Wait for data from the monitor with a timeout
                try:
                    data = client_queue.get(timeout=30)  # 30 second timeout
                    yield f"data: {json.dumps(data)}\n\n"

                    # If calculation is complete, end the stream
                    if data.get('complete', False):
                        logger.info(f"Stream ending for version {version} - calculation complete")
                        break
                except queue.Empty:
                    # Send a heartbeat after timeout to keep connection alive
                    yield f"data: {json.dumps({'heartbeat': True, 'timestamp': datetime.now().isoformat()})}\n\n"
        except GeneratorExit:
            # Client disconnected
            logger.info(f"Client disconnected from stream for version {version}")
            pass
        finally:
            # Remove this client from the monitor
            if version in active_monitors:
                active_monitors[version].remove_client(client_queue)
                logger.info(f"Client removed from monitor for version {version}")

    return Response(generate(), mimetype='text/event-stream')

@app.route('/price/<version>', methods=['GET'])
def get_price(version):
    """
    Get the final optimized price for a specific version
    """
    try:
        results_folder = os.path.join(SCRIPT_DIR, "..", "..", "Original", f"Batch({version})", f"Results({version})")

        # Try both possible file names for the price data
        price_files = [
            os.path.join(results_folder, f"optimal_price_{version}.json"),  # New format from CFA.py
            os.path.join(results_folder, f"optimized_price_{version}.json")  # Old format for backward compatibility
        ]

        for price_file in price_files:
            if os.path.exists(price_file):
                with open(price_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Found price data for version {version} in {os.path.basename(price_file)}")
                    return jsonify(data)

        # If we get here, no price file was found
        logger.warning(f"No price data found for version {version}")
        return jsonify({"error": f"No price data found for version {version}"}), 404
    except Exception as e:
        logger.error(f"Error retrieving price data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/run', methods=['POST'])
def run_scripts():
    try:
        # Enhanced logging for request debugging
        logger.info("=" * 80)
        logger.info("RUN ENDPOINT CALLED")
        logger.info(f"Request received at: {datetime.now().isoformat()}")
        logger.info(f"Request headers: {dict(request.headers)}")

        # Get JSON data from request
        data = request.get_json()
        if not data:
            logger.error("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        # Log the request data
        logger.info(f"Request data: {json.dumps(data, indent=2)}")

        # Extract and validate parameters with defaults
        selected_versions = data.get('selectedVersions', [1])
        if not selected_versions:
            logger.error("No versions selected")
            return jsonify({"error": "No versions selected"}), 400

        # Extract state parameters with defaults
        selected_v = data.get('selectedV', DEFAULT_V_STATES)
        selected_f = data.get('selectedF', DEFAULT_F_STATES)
        selected_r = data.get('selectedR', {f'R{i+1}': 'off' for i in range(10)})  # Add default for R
        selected_rf = data.get('selectedRF', {f'RF{i+1}': 'off' for i in range(5)})  # Add default for RF
        selected_calculation_option = data.get('selectedCalculationOption', DEFAULT_CALCULATION_OPTION)

        # Validate calculation option
        if not selected_calculation_option:
            logger.error("No calculation option selected")
            return jsonify({"error": "No calculation option selected"}), 400
        if selected_calculation_option not in CALCULATION_SCRIPTS:
            logger.error(f"Invalid calculation option: {selected_calculation_option}")
            return jsonify({"error": "Invalid calculation option"}), 400

        # Extract additional parameters
        target_row = int(data.get('targetRow', DEFAULT_TARGET_ROW))
        sen_parameters = data.get('SenParameters', {})  # Note: Frontend uses SenParameters (capital S)
        form_values = data.get('formValues', {})

        # Extract year columns configuration (from Amount10 fields)
        year_columns_config = {}
        amount10_keys = [k for k in form_values.keys() if 'Amount10' in k]

        if amount10_keys:
            key = amount10_keys[0]  # Take the first Amount10 key found
            try:
                year_columns_value = int(form_values[key].get('value', 0))
                logger.info(f"Found year columns configuration from {key}: {year_columns_value}")

                # Apply to all selected versions
                for version in selected_versions:
                    year_columns_config[str(version)] = year_columns_value
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Invalid year columns value from {key}: {e}")

        # Extract optimization parameters with defaults
        optimization_params = data.get('optimizationParams', {})

        # Set default optimization parameters
        tolerance_lower = DEFAULT_TOLERANCE_LOWER
        tolerance_upper = DEFAULT_TOLERANCE_UPPER
        increase_rate = DEFAULT_INCREASE_RATE
        decrease_rate = DEFAULT_DECREASE_RATE

        # Override with global parameters if provided
        if 'global' in optimization_params:
            global_params = optimization_params['global']
            tolerance_lower = global_params.get('toleranceLower', DEFAULT_TOLERANCE_LOWER)
            tolerance_upper = global_params.get('toleranceUpper', DEFAULT_TOLERANCE_UPPER)
            increase_rate = global_params.get('increaseRate', DEFAULT_INCREASE_RATE)
            decrease_rate = global_params.get('decreaseRate', DEFAULT_DECREASE_RATE)

        # Log all parameters in structured format
        log_state_parameters(
            selected_versions,
            selected_v,
            selected_f,
            selected_r,  # Add R parameters
            selected_rf,  # Add RF parameters
            selected_calculation_option,
            target_row,
            tolerance_lower,
            tolerance_upper,
            increase_rate,
            decrease_rate,
            sen_parameters
        )

        # Additional logging for year columns configuration
        if year_columns_config:
            logger.info(f"Year columns configuration: {json.dumps(year_columns_config)}")

        # Change to script directory for relative path operations
        os.chdir(SCRIPT_DIR)

        # Process each version
        calculation_script = CALCULATION_SCRIPTS[selected_calculation_option]
        for version in selected_versions:
            logger.info(f"Processing version {version}")

            # Check for version-specific optimization parameters
            version_tolerance_lower = tolerance_lower
            version_tolerance_upper = tolerance_upper
            version_increase_rate = increase_rate
            version_decrease_rate = decrease_rate

            # Override with version-specific parameters if provided
            if str(version) in optimization_params:
                version_params = optimization_params[str(version)]
                version_tolerance_lower = version_params.get('toleranceLower', tolerance_lower)
                version_tolerance_upper = version_params.get('toleranceUpper', tolerance_upper)
                version_increase_rate = version_params.get('increaseRate', increase_rate)
                version_decrease_rate = version_params.get('decreaseRate', decrease_rate)

                logger.info(f"Using version-specific optimization parameters for version {version}:")
                logger.info(f"  - Tolerance bounds: Lower={version_tolerance_lower}, Upper={version_tolerance_upper}")
                logger.info(f"  - Adjustment rates: Increase={version_increase_rate}, Decrease={version_decrease_rate}")

            error = process_version(
                version,
                calculation_script,
                selected_v,
                selected_f,
                selected_r,  # Add R parameters
                selected_rf,  # Add RF parameters
                target_row,
                selected_calculation_option,
                version_tolerance_lower,
                version_tolerance_upper,
                version_increase_rate,
                version_decrease_rate,
                sen_parameters
            )
            if error:
                logger.error(f"Error processing version {version}: {error}")
                return jsonify({"error": error}), 500

        logger.info("Waiting 1 second before executing R scripts...")
        time.sleep(1)

        # Prepare response
        response_data = {
            "status": "success",
            "message": "Calculation completed successfully",
            "timestamp": datetime.now().isoformat(),
            "yearColumns": year_columns_config
        }

        logger.info("Calculation completed successfully")
        return jsonify(response_data) if selected_calculation_option == 'calculateForPrice' else ('', 204)

    except Exception as e:
        error_msg = f"Error during calculation: {str(e)}"
        logger.exception(error_msg)
        return jsonify({"error": error_msg}), 500

# =====================================
# Application Entry Point
# =====================================

if __name__ == '__main__':
    app.run(debug=True, port=5007)
