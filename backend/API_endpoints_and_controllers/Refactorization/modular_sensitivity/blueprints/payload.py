from flask import Blueprint, jsonify, request
import time
import os
from config import LOGS_DIR, PAYLOAD_LOCK_FILE
from state import GLOBAL_PAYLOAD_LOCK, PAYLOAD_REGISTERED
from decorators import with_file_lock, with_memory_lock
from pipeline import initialize_pipeline, cancel_pipeline_after_timeout
from utils import atomic_write_json

payload_bp = Blueprint('payload', __name__)

@payload_bp.route('/register_payload', methods=['POST'])
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
