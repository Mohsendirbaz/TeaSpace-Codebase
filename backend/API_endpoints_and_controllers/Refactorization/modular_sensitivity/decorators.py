import functools
import filelock
import threading
import logging
from flask import jsonify

# Import shared state
from state import (
    PAYLOAD_REGISTERED, BASELINE_COMPLETED, CONFIG_COMPLETED, 
    RUNS_COMPLETED, PIPELINE_ACTIVE
)

from .logging_config import get_module_logger
# Configure logging
logger = get_module_logger(__name__)

def with_file_lock(lock_file_path, operation_name="operation"):
    """Decorator to create a file lock for the decorated function"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock = filelock.FileLock(lock_file_path, timeout=180)  # 3 minute timeout
            try:
                logger.info(f"ACQUIRED FILE LOCK: {operation_name} - {lock_file_path}")
                with lock:
                    result = func(*args, **kwargs)
                    logger.info(f"RELEASED FILE LOCK: {operation_name} - {lock_file_path}")
                    return result
            except filelock.Timeout:
                logger.info(f"TIMEOUT FILE LOCK: {operation_name} - {lock_file_path}")
                raise Exception(f"Timeout waiting for {operation_name} lock")
        return wrapper
    return decorator

from state import acquire_lock

def with_memory_lock(lock_obj, operation_name="operation"):
    """Decorator to apply a threading lock for the decorated function"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Use helper to acquire lock with logging
                acquired_lock = acquire_lock(lock_obj, operation_name)
                try:
                    result = func(*args, **kwargs)
                    logger.info(f"RELEASED MEMORY LOCK: {operation_name}")
                    return result
                finally:
                    acquired_lock.release()
            except Exception as e:
                if "Timeout" in str(e):
                    logger.info(f"TIMEOUT MEMORY LOCK: {operation_name}")
                raise Exception(f"Timeout waiting for in-memory {operation_name} lock")
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
