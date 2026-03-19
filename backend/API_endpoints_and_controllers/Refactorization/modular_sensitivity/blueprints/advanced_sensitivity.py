from flask import Blueprint, jsonify, request, send_file, Response
import subprocess
import os
import json
import time
import sys
import tempfile
import requests
import threading
import filelock

# Import from parent modules with relative imports
from ..config import (
    LOGS_DIR, VISUALIZATION_LOCK_FILE, RUN_LOCK_FILE, BASE_DIR, SCRIPT_DIR,
    get_sensitivity_calculation_script
)
from ..state import (
    GLOBAL_VISUALIZE_LOCK, GLOBAL_RUN_LOCK, PIPELINE_ACTIVE,
    CONFIG_COMPLETED, RUNS_COMPLETED
)
from ..decorators import with_file_lock, with_memory_lock, with_pipeline_check
from ..utils import (
    atomic_read_json, atomic_read_pickle, atomic_write_json, atomic_write_pickle,
    get_sensitivity_data, run_script
)
from ..logging_config import get_module_logger

logger = get_module_logger(__name__)

advanced_sensitivity_bp = Blueprint('advanced_sensitivity', __name__)

@advanced_sensitivity_bp.route('/run-script-econ', methods=['POST'])
def run_script_econ():
    """
    Execute script_econ.py to extract metrics from Economic Summary CSV files
    and append them to calsen_paths.json.
    """
    data = request.get_json()
    version = data.get('version', '1')

    # Log the start of the operation
    logger.info(f"Starting script_econ.py execution for version {version}")

    try:
        # Get path to script_econ.py
        script_path = os.path.join(BASE_DIR, 'backend', 'API_endpoints_and_controllers', 'script_econ.py')
        logger.info(f"Script path: {script_path}")

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
        logger.error(f"Error executing script_econ.py: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error executing script_econ.py: {str(e)}'
        }), 500

@advanced_sensitivity_bp.route('/run-add-axis-labels', methods=['POST'])
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
        logger.error(f"Error executing add_axis_labels.py: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error executing add_axis_labels.py: {str(e)}'
        }), 500

@advanced_sensitivity_bp.route('/run-generate-plots', methods=['POST'])
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
        logger.error(f"Error executing generate_plots.py: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error executing generate_plots.py: {str(e)}'
        }), 500

@advanced_sensitivity_bp.route('/check-calsen-paths', methods=['GET'])
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

    # Check if file exists
    file_exists = os.path.exists(calsen_paths_file)

    # Include payload details for monitoring
    payload_details = {
        "operation": "check_calsen_paths",
        "version": version,
        "path": calsen_paths_file,
        "exists": file_exists
    }

    # Log payload details for monitoring
    logger.info(f"Payload details: {json.dumps(payload_details)}")

    return jsonify({
        'exists': file_exists,
        'path': calsen_paths_file
    })
