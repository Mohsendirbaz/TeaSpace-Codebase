"""
CalSen - Configuration and Sensitivity Path Resolution Service
Provides dynamic path resolution for sensitivity analysis configurations.
Running on port 2750, this service helps determine appropriate file paths
for configuration files, matrices, and results based on version and parameters.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import json
import glob
import time
import sys

# Base directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_DIR = os.path.join(BASE_DIR, 'backend')
LOGS_DIR = os.path.join(SCRIPT_DIR, 'Logs')
ORIGINAL_BASE_DIR = os.path.join(BASE_DIR, 'backend', 'Original')

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Log file path for CalSen
CALSEN_LOG_PATH = os.path.join(LOGS_DIR, "CALSEN.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CALSEN_LOG_PATH),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('calsen')
logger.info("CalSen service starting up")

# Create Flask app
app = Flask(__name__)
CORS(app)

# =====================================
# Path Building Functions
# =====================================

def find_configuration_files(version, param_id=None, mode=None, variation=None):
    """
    Find configuration files based on provided filters.

    Args:
        version (int): Version number
        param_id (str, optional): Parameter ID (e.g., "S35")
        mode (str, optional): Mode (percentage, directvalue, absolutedeparture, montecarlo)
        variation (float, optional): Variation value

    Returns:
        list: List of found configuration file paths
    """
    base_dir = os.path.join(ORIGINAL_BASE_DIR, f"Batch({version})", f"Results({version})")
    sensitivity_dir = os.path.join(base_dir, "Sensitivity")

    # If no filters provided, return the base sensitivity directory
    if not param_id and not mode and variation is None:
        return [sensitivity_dir]

    # Build search pattern based on provided filters
    search_pattern = sensitivity_dir

    if param_id:
        search_pattern = os.path.join(search_pattern, param_id)
    else:
        search_pattern = os.path.join(search_pattern, "S*")

    if mode:
        # Ensure lowercase for directory search
        mode_lower = mode.lower()
        search_pattern = os.path.join(search_pattern, mode_lower)
    else:
        search_pattern = os.path.join(search_pattern, "*")

    if variation is not None:
        var_str = f"{variation:+.2f}"
        search_pattern = os.path.join(search_pattern, var_str)
    else:
        search_pattern = os.path.join(search_pattern, "*")

    # Search for config files
    search_pattern = os.path.join(search_pattern, f"*config*.json")
    found_files = glob.glob(search_pattern)

    return found_files

def build_paths_for_version(version):
    """
    Build all required paths for a given version using the sensitivity config.

    Args:
        version (int): Version number

    Returns:
        dict: Dictionary of path sets for each enabled parameter
    """
    logger.info(f"Building paths for version {version}")

    # Standard paths
    code_files_path = ORIGINAL_BASE_DIR

    # Path to sensitivity config file
    sensitivity_config_path = os.path.join(
        code_files_path,
        f"Batch({version})",
        f"Results({version})",
        "Sensitivity",
        "Reports",
        "sensitivity_config.json"
    )

    # Load sensitivity config if available
    if os.path.exists(sensitivity_config_path):
        logger.info(f"Found sensitivity configuration at {sensitivity_config_path}")
        try:
            with open(sensitivity_config_path, 'r') as f:
                sensitivity_config = json.load(f)
                # Extract parameters from the nested structure if needed
                if 'parameters' in sensitivity_config:
                    sensitivity_config = sensitivity_config['parameters']
        except Exception as e:
            logger.error(f"Error loading sensitivity configuration: {str(e)}")
            return None
    else:
        # Try to find any sensitivity directories if config not found
        logger.warning(f"No sensitivity configuration found at {sensitivity_config_path}")
        sensitivity_dir = os.path.join(
            code_files_path,
            f"Batch({version})",
            f"Results({version})",
            "Sensitivity"
        )

        if not os.path.exists(sensitivity_dir):
            logger.warning(f"No sensitivity directory found at {sensitivity_dir}")
            return None

        # Look for parameter directories
        param_dirs = glob.glob(os.path.join(sensitivity_dir, "S*"))
        if not param_dirs:
            logger.warning(f"No parameter directories found in {sensitivity_dir}")
            return None

        # Build a simple config based on directory structure
        sensitivity_config = {}
        for param_dir in param_dirs:
            param_id = os.path.basename(param_dir)
            mode_dirs = glob.glob(os.path.join(param_dir, "*"))

            if mode_dirs:
                mode = os.path.basename(mode_dirs[0])
                sensitivity_config[param_id] = {
                    "enabled": True,
                    "mode": mode,
                    "number": param_id[1:] if param_id.startswith('S') and param_id[1:].isdigit() else None
                }

    # Build path sets for all enabled S parameters
    path_sets = {}

    for param_id, config in sensitivity_config.items():
        if not config.get('enabled', False):
            continue

        # Convert S10 to S10, ensure proper formatting
        if param_id.startswith('S') and param_id[1:].isdigit():
            s_param = param_id
            s_num = param_id[1:]
        else:
            continue

        # Get mode and determine variation format
        mode = config.get('mode', 'percentage').lower()
        values = config.get('values', [])

        if not values:
            continue

        # Determine variations based on mode
        try:
            # For all modes, use the values provided directly without special handling
            variations = [float(v) for v in values if v is not None]
        except (TypeError, ValueError):
            logger.warning(f"Invalid values for {mode} mode in {param_id}: {values}")
            continue

        if not variations:
            continue

        # Process each variation
        param_paths = {}

        for variation in variations:
            # Format variation string
            var_str = f"{variation:+.2f}"

            # Build paths for this variation
            # Economic variation directory (lowercase mode)
            Econ_var_dir = os.path.join(
                code_files_path,
                f"Batch({version})",
                f"Results({version})",
                "Sensitivity",
                s_param,
                mode.lower(),  # Ensure lowercase for consistency
                "Configuration",
                f"{s_param}_{var_str}"
            )
            # Parameter variation directory (lowercase mode)
            param_var_dir = os.path.join(
                code_files_path,
                f"Batch({version})",
                f"Results({version})",
                "Sensitivity",
                s_param,
                mode.lower(),  # Ensure lowercase for consistency
                var_str
            )

            # Mode directory with capitalized name
            # With this:
            mode_dir_mapping = {
                'percentage': 'Percentage',
                'directvalue': 'DirectValue',
                'absolutedeparture': 'AbsoluteDeparture',
                'montecarlo': 'MonteCarlo'
            }
            mode_dir_name = mode_dir_mapping.get(mode.lower(), 'Percentage')  # Default to Percentage

            # Configuration directory (capitalized mode)
            config_var_dir = os.path.join(
                code_files_path,
                f"Batch({version})",
                f"Results({version})",
                "Sensitivity",
                mode_dir_name,
                "Configuration",
                f"{s_param}_{var_str}"
            )

            # Configuration matrix file
            config_matrix_file = os.path.join(
                param_var_dir,
                f"General_Configuration_Matrix({version}).csv"
            )

            # Look for alternate locations if not found
            if not os.path.exists(config_matrix_file):
                alt_config_matrix_file = os.path.join(
                    code_files_path,
                    f"Batch({version})",
                    f"Results({version})",
                    f"General_Configuration_Matrix({version}).csv"
                )
                if os.path.exists(alt_config_matrix_file):
                    config_matrix_file = alt_config_matrix_file

            # Configuration file
            config_file = os.path.join(
                code_files_path,
                f"Batch({version})",
                f"ConfigurationPlotSpec({version})",
                f"configurations({version}).py"
            )

            # Only include if paths exist or can be created
            os.makedirs(param_var_dir, exist_ok=True)
            os.makedirs(config_var_dir, exist_ok=True)

            # Add paths for this variation
            var_key = var_str
            param_paths[var_key] = {
                "param_var_dir": param_var_dir,
                "config_var_dir": config_var_dir,
                "config_matrix_file": config_matrix_file,
                "config_file": config_file,
                "Econ_var_dir": Econ_var_dir,
                "mode": mode,
                "variation": variation,
                "variation_str": var_str
            }

        # Add this parameter's paths to the main collection
        if param_paths:
            path_sets[s_param] = {
                "mode": mode,
                "variations": param_paths,
                "compareToKey": config.get('compareToKey', 'S13'),
                "comparisonType": config.get('comparisonType', 'primary')
            }

    logger.info(f"Built path sets for {len(path_sets)} parameters")
    return path_sets

# =====================================
# API Endpoints
# =====================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "CalSen",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/get_config_paths', methods=['POST'])
def get_config_paths():
    """
    Get configuration paths based on version and payload.

    Expected JSON request format:
    {
        "version": 1,
        "payload": {
            "selectedVersions": [1],
            "selectedV": {"V1": "on", ...},
            "selectedF": {"F1": "on", ...},
            "calculationOption": "freeFlowNPV",
            "targetRow": 20,
            "SenParameters": {
                "S13": {
                    "enabled": true,
                    "mode": "percentage",
                    "values": [10],
                    ...
                },
                ...
            }
        }
    }
    """
    try:
        data = request.json

        if not data:
            logger.warning("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        version = data.get('version')
        payload = data.get('payload', {})

        if not version:
            logger.warning("No version provided in request")
            return jsonify({"error": "Version number is required"}), 400

        logger.info(f"Processing get_config_paths request for version {version}")

        # Build path sets for this version
        path_sets = build_paths_for_version(version)

        if not path_sets:
            logger.warning(f"No enabled configurations found for version {version}")
            return jsonify({"error": f"No enabled configurations found for version {version}"}), 404

        # Prepare response with path sets
        response = {
            "status": "success",
            "version": version,
            "path_sets": path_sets,
            "payload": payload  # Forward original payload
        }

        logger.info(f"Returning path sets for {len(path_sets)} parameters")
        return jsonify(response)

    except Exception as e:
        error_msg = f"Error processing get_config_paths request: {str(e)}"
        logger.exception(error_msg)
        return jsonify({"error": error_msg}), 500

@app.route('/find_config_files', methods=['POST'])
def find_config_files():
    """
    Find configuration files based on provided filters.

    Expected JSON request format:
    {
        "version": 1,
        "param_id": "S35",  # Optional
        "mode": "percentage",  # Optional
        "variation": 10.0  # Optional
    }
    """
    try:
        data = request.json

        if not data:
            logger.warning("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        version = data.get('version')

        if not version:
            logger.warning("No version provided in request")
            return jsonify({"error": "Version number is required"}), 400

        # Extract optional filters
        param_id = data.get('param_id')
        mode = data.get('mode')
        variation = data.get('variation')

        if variation is not None:
            try:
                variation = float(variation)
            except (TypeError, ValueError):
                logger.warning(f"Invalid variation value: {variation}")
                return jsonify({"error": f"Invalid variation value: {variation}"}), 400

        logger.info(f"Finding config files for version {version}, param={param_id}, mode={mode}, variation={variation}")

        # Find matching configuration files
        config_files = find_configuration_files(version, param_id, mode, variation)

        # Prepare response
        response = {
            "status": "success",
            "version": version,
            "filters": {
                "param_id": param_id,
                "mode": mode,
                "variation": variation
            },
            "files": config_files,
            "count": len(config_files)
        }

        logger.info(f"Found {len(config_files)} configuration files")
        return jsonify(response)

    except Exception as e:
        error_msg = f"Error finding configuration files: {str(e)}"
        logger.exception(error_msg)
        return jsonify({"error": error_msg}), 500

@app.route('/list_parameters', methods=['POST'])
def list_parameters():
    """
    List all enabled sensitivity parameters for a version.

    Expected JSON request format:
    {
        "version": 1
    }
    """
    try:
        data = request.json

        if not data:
            logger.warning("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        version = data.get('version')

        if not version:
            logger.warning("No version provided in request")
            return jsonify({"error": "Version number is required"}), 400

        logger.info(f"Listing parameters for version {version}")

        # Get path sets which contain parameter information
        path_sets = build_paths_for_version(version)

        if not path_sets:
            logger.warning(f"No enabled parameters found for version {version}")
            return jsonify({"error": f"No enabled parameters found for version {version}"}), 404

        # Extract parameter information
        parameters = {}
        for param_id, path_set in path_sets.items():
            parameters[param_id] = {
                "mode": path_set.get("mode"),
                "variations": list(path_set.get("variations", {}).keys()),
                "compareToKey": path_set.get("compareToKey"),
                "comparisonType": path_set.get("comparisonType")
            }

        # Prepare response
        response = {
            "status": "success",
            "version": version,
            "parameters": parameters,
            "count": len(parameters)
        }

        logger.info(f"Found {len(parameters)} enabled parameters")
        return jsonify(response)

    except Exception as e:
        error_msg = f"Error listing parameters: {str(e)}"
        logger.exception(error_msg)
        return jsonify({"error": error_msg}), 500

# =====================================
# Main Application
# =====================================

if __name__ == '__main__':
    # Get port from command line arguments or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 2750

    logger.info(f"Starting CalSen service on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)