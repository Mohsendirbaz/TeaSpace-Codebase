from flask import Blueprint, jsonify, request
import requests
import time
from state import (
    PIPELINE_ACTIVE, PAYLOAD_REGISTERED, BASELINE_COMPLETED,
    CONFIG_COMPLETED, RUNS_COMPLETED
)
from ..logging_config import get_module_logger

logger = get_module_logger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint that's always accessible"""
    start_time = time.time()
    client_ip = request.remote_addr
    logger.info(f"Health check request from {client_ip}")

    # Check if the 2600 service is running
    config_copy_service_status = "available"
    try:
        response = requests.get("http://localhost:2600/health", timeout=2)
        if not response.ok:
            config_copy_service_status = "unavailable"
            logger.warning(f"Config copy service returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        config_copy_service_status = "unavailable"
        logger.error(f"Config copy service check failed: {str(e)}")

    # Log pipeline state
    pipeline_state = {
        "active": PIPELINE_ACTIVE.is_set(),
        "payload_registered": PAYLOAD_REGISTERED.is_set(),
        "baseline_completed": BASELINE_COMPLETED.is_set(),
        "config_completed": CONFIG_COMPLETED.is_set(),
        "runs_completed": RUNS_COMPLETED.is_set()
    }
    logger.debug(f"Pipeline state: {pipeline_state}")

    response_time = (time.time() - start_time) * 1000  # in milliseconds
    logger.info(f"Health check completed in {response_time:.2f}ms")

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
