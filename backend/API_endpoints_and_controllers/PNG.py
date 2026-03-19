from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import logging
import json
from datetime import datetime
import sys
from pathlib import Path

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Path Configuration
ORIGINAL_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BACKEND_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUBLIC_DIR = ORIGINAL_DIR / 'Original'
LOG_DIR = BACKEND_DIR / "Logs"
SCRIPT_DIR = BACKEND_DIR / "Visualization_generators"
LOG_FILE = LOG_DIR / "PNG.log"

# Create log directory with verification
if not LOG_DIR.exists():
    try:
        LOG_DIR.mkdir(exist_ok=True)
        print(f"Created log directory at {LOG_DIR}")
    except Exception as e:
        print(f"Failed to create log directory: {e}")
        sys.exit(1)

# Custom handler that closes file after each write
class ImmediateFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.close()
        # Reopen for next write
        self.stream = self._open()

# Initialize logging to console instead of file
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    '%Y-%m-%d %H:%M:%S'
))

# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Commented out file logging that was causing the Git stash issue
# If file logging is needed, use the ImmediateFileHandler instead
# file_handler = ImmediateFileHandler(LOG_FILE)
# file_handler.setLevel(logging.INFO)
# file_handler.setFormatter(logging.Formatter(
#     '%(asctime)s [%(levelname)s] %(message)s',
#     '%Y-%m-%d %H:%M:%S'
# ))
# logger.addHandler(file_handler)

# Log initialization status
logger.info(f"Initialized logging in {LOG_FILE}")
logger.info(f"Backend directory: {BACKEND_DIR}")
logger.info(f"Script directory: {SCRIPT_DIR}")

# List of script files to execute
SCRIPT_FILES = ['PNG_PLOT.py']

def log_properties_as_table(properties):
    """
    Create a formatted table of properties in the log file.

    Args:
        properties (list): List of property identifiers to be logged
    """
    if not properties:
        logger.warning("No properties provided for logging")
        return

    # Calculate maximum property length for formatting
    max_length = max(len(str(prop)) for prop in properties)
    format_str = f"{{:<5}} | {{:<{max_length}}}"

    # Create and log table header
    header = format_str.format("Row", "Property")
    separator = '-' * len(header)

    logger.info(separator)
    logger.info(header)
    logger.info(separator)

    # Log each property with its index
    for index, prop in enumerate(properties, 1):
        logger.info(format_str.format(index, prop))
    logger.info(separator)

def log_sensitivity_parameters(sensitivity_params):
    """
    Log sensitivity analysis configuration in a structured format.

    Args:
        sensitivity_params (dict): Dictionary containing sensitivity analysis parameters
    """
    if not sensitivity_params:
        logger.info("No sensitivity parameters provided")
        return

    logger.info("Sensitivity Analysis Configuration:")
    enabled_params = {k: v for k, v in sensitivity_params.items() if v.get('enabled', False)}

    if not enabled_params:
        logger.info("No enabled sensitivity parameters found")
        return

    for param_id, config in enabled_params.items():
        logger.info(f"""
Parameter: {param_id}
- Param_ID: {config.get('Param_ID'), ('not specified')}
- Mode: {config.get('mode')}
- Values: {config.get('values', [])}
- Comparison: {config.get('compareToKey')} ({config.get('comparisonType')})
- Visualization Options:
  * Waterfall: {config.get('waterfall', False)}
  * Bar: {config.get('bar', False)}
  * Point: {config.get('point', False)}
""".strip())

def validate_request_data(data):
    """
    Validate and extract required parameters from request data.
    """
    try:
        # Extract and validate required parameters
        selected_versions = data.get('selectedVersions', [])
        if not isinstance(selected_versions, list):
            return False, "selectedVersions must be a list"

        # Validate that at least one version is selected and all versions are valid
        if not selected_versions:
            logger.info("No versions selected, using default version [1]")
            selected_versions = [1]  # Default to version 1 if none selected
        else:
            # Validate each version number
            try:
                selected_versions = [int(v) for v in selected_versions]
                if not all(v > 0 for v in selected_versions):
                    logger.warning("Invalid version numbers found, using default version [1]")
                    selected_versions = [1]
            except (ValueError, TypeError) as e:
                logger.error(f"Error validating version numbers: {str(e)}")
                selected_versions = [1]

        selected_properties = data.get('selectedProperties', [])
        if not isinstance(selected_properties, list):
            return False, "selectedProperties must be a list"

        # Validate that at least one property is selected
        if not selected_properties:
            logger.info("No properties selected, proceeding with empty list")
            selected_properties = []  # Ensure it's an empty list, not None

        remarks = str(data.get('remarks', 'off')).lower()
        if remarks not in ['on', 'off']:
            return False, "remarks must be 'on' or 'off'"

        customized_features = str(data.get('customizedFeatures', 'off')).lower()
        if customized_features not in ['on', 'off']:
            return False, "customizedFeatures must be 'on' or 'off'"

        sensitivity_params = data.get('S', {})
        logger.info(f"Received sensitivity parameters: {sensitivity_params}")
        if not isinstance(sensitivity_params, dict):
            return False, "S must be a dictionary"

        # Add validation for Param_ID
        for key, config in sensitivity_params.items():
            if config.get('enabled', False):
                param_id = config.get('Param_ID')
                if not param_id or not isinstance(param_id, str):
                    return False, f"Invalid Param_ID for parameter {key}"
                if not param_id.startswith('S') or not param_id[1:].isdigit():
                    return False, f"Param_ID must be in format 'S<number>' for parameter {key}"

        return True, {
            'selected_versions': selected_versions,
            'selected_properties': selected_properties,
            'remarks': remarks,
            'customized_features': customized_features,
            'sensitivity_params': sensitivity_params,
        }
    except Exception as e:
        return False, f"Validation error: {str(e)}"
@app.route('/generate_png_plots', methods=['POST'])
def run_scripts():
    """
    Main endpoint for running PNG visualization scripts.
    Handles request validation, script execution, and error handling.

    Returns:
        tuple: (response, status_code)
    """
    request_start_time = datetime.now()
    logger.info(f"New visualization request received at {request_start_time}")

    try:
        # Validate request data
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        success, result = validate_request_data(data)
        if not success:
            return jsonify({"error": result}), 400

        try:
            # Extract validated data
            selected_versions = result['selected_versions']
            selected_properties = result['selected_properties']
            remarks = result['remarks']
            customized_features = result['customized_features']
            sensitivity_params = result['sensitivity_params']

            # Validate selected versions
            if not selected_versions:
                logger.warning("No versions selected, using default version [1]")
                selected_versions = [1]

            # Log request parameters
            logger.info(f"Selected versions: {selected_versions}")
            log_properties_as_table(selected_properties)
            logger.info(f"Remarks state: {remarks}")
            logger.info(f"Customized features state: {customized_features}")
            log_sensitivity_parameters(sensitivity_params)

            # Prepare script execution
            if not SCRIPT_DIR.exists():
                return jsonify({"error": "Script directory not found"}), 500

            os.chdir(SCRIPT_DIR)
            selected_versions_str = ",".join(map(str, selected_versions))
            selected_properties_str = ",".join(selected_properties) if selected_properties else ""
            sensitivity_json = json.dumps(sensitivity_params)
        except Exception as e:
            logger.error(f"Error preparing script execution: {str(e)}")
            return jsonify({"error": "Error preparing script execution"}), 500

        # Execute each script
        for script_filename in SCRIPT_FILES:
            try:
                script_path = SCRIPT_DIR / script_filename
                if not script_path.exists():
                    logger.error(f"Script file not found: {script_filename}")
                    return jsonify({"error": f"Script file not found: {script_filename}"}), 500

                logger.info(f"Executing script: {script_filename}")
                logger.info(f"Command arguments: {[sys.executable, script_filename, selected_versions_str, selected_properties_str, remarks, customized_features, sensitivity_json]}")

                # Ensure all arguments are strings and not empty
                args = [
                    sys.executable,
                    script_filename,
                    selected_versions_str or "1",  # Default to version 1 if empty
                    selected_properties_str or "",  # Empty string if no properties
                    remarks or "on",  # Default to "on" if empty
                    customized_features or "off",  # Default to "off" if empty
                    sensitivity_json or "{}"  # Default to empty dict if empty
                ]

                # Create necessary directories and files
                try:
                    for version in selected_versions:
                        batch_dir = PUBLIC_DIR / f'Batch({version})'
                        results_dir = batch_dir / f'Results({version})'
                        config_dir = batch_dir / f'ConfigurationPlotSpec({version})'

                        # Create directories
                        for directory in [batch_dir, results_dir, config_dir]:
                            directory.mkdir(exist_ok=True)
                            logger.info(f"Created directory: {directory}")

                        # Create default files
                        config_file = config_dir / f'U_configurations({version}).py'
                        if not config_file.exists():
                            with open(config_file, 'w') as f:
                                f.write('filteredValues = []')
                            logger.info(f"Created default config file: {config_file}")
                except Exception as e:
                    logger.error(f"Error creating directories/files: {str(e)}")
                    return jsonify({"error": f"Error creating directories/files: {str(e)}"}), 500

                # Execute script
                try:
                    result = subprocess.run(
                        args,
                        capture_output=True,
                        text=True,
                        env=os.environ.copy()
                    )

                    # Log all output
                    if result.stdout:
                        logger.info(f"Script output: {result.stdout}")
                    if result.stderr:
                        logger.warning(f"Script stderr: {result.stderr}")

                    if result.returncode != 0:
                        error_msg = f"Error in {script_filename}: {result.stderr}"
                        logger.error(error_msg)
                        return jsonify({"error": error_msg}), 500
                except Exception as e:
                    logger.error(f"Error during script execution: {str(e)}")
                    return jsonify({"error": f"Error during script execution: {str(e)}"}), 500

            except Exception as e:
                logger.error(f"Error executing {script_filename}: {str(e)}", exc_info=True)
                return jsonify({"error": f"Error executing {script_filename}: {str(e)}"}), 500

        # Log successful completion
        request_duration = datetime.now() - request_start_time
        logger.info(f"Request completed successfully in {request_duration}")

        # Import and run album organizer
        try:
            # Import and run album organizer
            sys.path.append(str(BACKEND_DIR))
            from Album_organizer import organize_plot_albums
            organize_plot_albums()
            logger.info("Album organization completed")
        except Exception as e:
            logger.error(f"Error during album organization: {str(e)}")
            # Continue with normal flow, don't fail the request

        return '', 204

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/plots/<version>', methods=['GET'])
def get_plots(version):
    """
    Get all plots for a specific version.

    Args:
        version (str): The version number

    Returns:
        JSON response with plot information
    """
    try:
        logger.info(f"Fetching plots for version {version}")

        # Construct the path to the version's Results directory
        version_folder = PUBLIC_DIR / f'Batch({version})' / f'Results({version})'

        if not version_folder.exists():
            logger.warning(f"Results folder does not exist: {version_folder}")
            return jsonify({"error": "Version folder not found"}), 404

        # Find all plot files in the version folder
        plot_files = []

        # Look for plots in various subdirectories
        for root, dirs, files in os.walk(version_folder):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Get relative path from version folder
                    rel_path = os.path.relpath(os.path.join(root, file), version_folder)

                    # Extract category and group from path
                    path_parts = rel_path.split(os.path.sep)
                    category = path_parts[0] if len(path_parts) > 1 else "General"
                    group = path_parts[1] if len(path_parts) > 2 else "Default"

                    # Create plot info
                    plot_info = {
                        "id": len(plot_files) + 1,
                        "name": file,
                        "path": f"Batch({version})/Results({version})/{rel_path}",
                        "category": category,
                        "group": group
                    }

                    plot_files.append(plot_info)

        if not plot_files:
            logger.info(f"No plot files found for version {version}")
            return jsonify([]), 200

        logger.info(f"Found {len(plot_files)} plot files for version {version}")
        return jsonify(plot_files), 200

    except Exception as e:
        logger.error(f"Error fetching plots for version {version}: {str(e)}")
        return jsonify({"error": f"Error fetching plots: {str(e)}"}), 500

@app.route('/api/plots/<version>/<category>/<group>', methods=['GET'])
def get_plots_by_group(version, category, group):
    """
    Get plots for a specific version, category, and group.

    Args:
        version (str): The version number
        category (str): The plot category
        group (str): The plot group

    Returns:
        JSON response with plot information
    """
    try:
        logger.info(f"Fetching plots for version {version}, category {category}, group {group}")

        # Construct the path to the version's Results directory
        version_folder = PUBLIC_DIR / f'Batch({version})' / f'Results({version})'

        if not version_folder.exists():
            logger.warning(f"Results folder does not exist: {version_folder}")
            return jsonify({"error": "Version folder not found"}), 404

        # Find all plot files in the specified category and group
        plot_files = []

        # Look for plots in the specified category and group
        category_folder = version_folder / category
        if category_folder.exists():
            group_folder = category_folder / group
            if group_folder.exists():
                for file in os.listdir(group_folder):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        # Create plot info
                        plot_info = {
                            "id": len(plot_files) + 1,
                            "name": file,
                            "path": f"Batch({version})/Results({version})/{category}/{group}/{file}",
                            "category": category,
                            "group": group
                        }

                        plot_files.append(plot_info)

        if not plot_files:
            logger.info(f"No plot files found for version {version}, category {category}, group {group}")
            return jsonify([]), 200

        logger.info(f"Found {len(plot_files)} plot files for version {version}, category {category}, group {group}")
        return jsonify(plot_files), 200

    except Exception as e:
        logger.error(f"Error fetching plots for version {version}, category {category}, group {group}: {str(e)}")
        return jsonify({"error": f"Error fetching plots: {str(e)}"}), 500

@app.route('/api/sensitivity-plots/<version>', methods=['GET'])
def get_sensitivity_plots(version):
    """
    Get all sensitivity plots for a specific version.

    Args:
        version (str): The version number

    Returns:
        JSON response with plot information
    """
    try:
        logger.info(f"Fetching sensitivity plots for version {version}")

        # Construct the path to the version's Sensitivity directory
        sensitivity_folder = PUBLIC_DIR / f'Batch({version})' / f'Results({version})' / 'Sensitivity'

        if not sensitivity_folder.exists():
            logger.warning(f"Sensitivity folder does not exist: {sensitivity_folder}")
            return jsonify({"error": "Sensitivity folder not found"}), 404

        # Find all plot files in the sensitivity folder
        plot_files = []

        # Look for plots in various subdirectories
        for root, dirs, files in os.walk(sensitivity_folder):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Get relative path from sensitivity folder
                    rel_path = os.path.relpath(os.path.join(root, file), sensitivity_folder)

                    # Extract category and group from path
                    path_parts = rel_path.split(os.path.sep)
                    category = path_parts[0] if len(path_parts) > 1 else "General"
                    group = path_parts[1] if len(path_parts) > 2 else "Default"

                    # Create plot info
                    plot_info = {
                        "id": len(plot_files) + 1,
                        "name": file,
                        "path": f"Batch({version})/Results({version})/Sensitivity/{rel_path}",
                        "category": category,
                        "group": group
                    }

                    plot_files.append(plot_info)

        if not plot_files:
            logger.info(f"No sensitivity plot files found for version {version}")
            return jsonify([]), 200

        logger.info(f"Found {len(plot_files)} sensitivity plot files for version {version}")
        return jsonify(plot_files), 200

    except Exception as e:
        logger.error(f"Error fetching sensitivity plots for version {version}: {str(e)}")
        return jsonify({"error": f"Error fetching sensitivity plots: {str(e)}"}), 500

@app.route('/api/sensitivity-plots/<version>/<category>/<group>', methods=['GET'])
def get_sensitivity_plots_by_group(version, category, group):
    """
    Get sensitivity plots for a specific version, category, and group.

    Args:
        version (str): The version number
        category (str): The plot category
        group (str): The plot group

    Returns:
        JSON response with plot information
    """
    try:
        logger.info(f"Fetching sensitivity plots for version {version}, category {category}, group {group}")

        # Construct the path to the version's Sensitivity directory
        sensitivity_folder = PUBLIC_DIR / f'Batch({version})' / f'Results({version})' / 'Sensitivity'

        if not sensitivity_folder.exists():
            logger.warning(f"Sensitivity folder does not exist: {sensitivity_folder}")
            return jsonify({"error": "Sensitivity folder not found"}), 404

        # Find all plot files in the specified category and group
        plot_files = []

        # Look for plots in the specified category and group
        category_folder = sensitivity_folder / category
        if category_folder.exists():
            group_folder = category_folder / group
            if group_folder.exists():
                for file in os.listdir(group_folder):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        # Create plot info
                        plot_info = {
                            "id": len(plot_files) + 1,
                            "name": file,
                            "path": f"Batch({version})/Results({version})/Sensitivity/{category}/{group}/{file}",
                            "category": category,
                            "group": group
                        }

                        plot_files.append(plot_info)

        if not plot_files:
            logger.info(f"No sensitivity plot files found for version {version}, category {category}, group {group}")
            return jsonify([]), 200

        logger.info(f"Found {len(plot_files)} sensitivity plot files for version {version}, category {category}, group {group}")
        return jsonify(plot_files), 200

    except Exception as e:
        logger.error(f"Error fetching sensitivity plots for version {version}, category {category}, group {group}: {str(e)}")
        return jsonify({"error": f"Error fetching sensitivity plots: {str(e)}"}), 500

@app.route('/images/<path:filename>')
def serve_image(filename):
    """
    Serve image files from the Original directory
    """
    try:
        image_path = PUBLIC_DIR / filename
        if not image_path.exists():
            return jsonify({"error": f"Image not found: {filename}"}), 404
        return send_file(str(image_path))
    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5008))
    debug = os.getenv('FLASK_ENV') == 'development'

    # Create public/Original directory if it doesn't exist
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting PNG visualization server on port {port}")
    logger.info(f"Serving images from: {PUBLIC_DIR}")
    app.run(debug=debug, port=port)
