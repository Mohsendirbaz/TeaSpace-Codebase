from flask import Blueprint, jsonify, request
import time
import os
import logging
from config import LOGS_DIR, CONFIG_LOCK_FILE, SENSITIVITY_CONFIG_STATUS_PATH, SENSITIVITY_CONFIG_DATA_PATH
from state import GLOBAL_CONFIG_LOCK, CONFIG_COMPLETED, BASELINE_COMPLETED
from decorators import with_file_lock, with_memory_lock, with_pipeline_check
from utils import create_sensitivity_directories, save_sensitivity_config_files, atomic_write_json, atomic_write_pickle

# Configure logging
logger = logging.getLogger(__name__)

sensitivity_bp = Blueprint('sensitivity', __name__)

@sensitivity_bp.route('/sensitivity/configure', methods=['POST'])
@with_file_lock(CONFIG_LOCK_FILE, "sensitivity configuration")
@with_memory_lock(GLOBAL_CONFIG_LOCK, "sensitivity configuration")
@with_pipeline_check(required_event=BASELINE_COMPLETED, next_event=CONFIG_COMPLETED, operation_name="sensitivity configuration")
def configure_sensitivity():
    """Generate and save sensitivity configurations"""
    try:
        data = request.get_json()
        run_id = data.get('runId', 'unknown')
        logger.info(f"START sensitivity config for run: {run_id}")
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
        sensitivity_dir, config_dir = create_sensitivity_directories(version, config['SenParameters'])
        logger.info(f"CREATED dirs for version: {version}")

        # Save configuration files with thread-safe function
        saved_files = save_sensitivity_config_files(version, config_dir, config['SenParameters'])
        logger.info(f"SAVED {len(saved_files)} config files")

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

        return jsonify({
            "status": "success",
            "message": "Sensitivity configurations generated and saved successfully",
            "runId": run_id,
            "configDir": config_dir,
            "sensitivityDir": sensitivity_dir,
            "savedFiles": len(saved_files),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "next_step": "/runs"
        }), 200
        
        logger.info(f"COMPLETED config for run: {run_id}")

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
