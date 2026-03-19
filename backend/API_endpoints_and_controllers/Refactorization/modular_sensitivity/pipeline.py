import threading
import time
from state import (
    PAYLOAD_REGISTERED, BASELINE_COMPLETED, CONFIG_COMPLETED, 
    RUNS_COMPLETED, PIPELINE_ACTIVE
)
from .logging_config import get_module_logger

logger = get_module_logger(__name__)

from state import clear_event

def reset_execution_pipeline():
    """Reset all execution pipeline events to initial state"""
    clear_event(PAYLOAD_REGISTERED, "PAYLOAD_REGISTERED")
    clear_event(BASELINE_COMPLETED, "BASELINE_COMPLETED") 
    clear_event(CONFIG_COMPLETED, "CONFIG_COMPLETED")
    clear_event(RUNS_COMPLETED, "RUNS_COMPLETED")
    clear_event(PIPELINE_ACTIVE, "PIPELINE_ACTIVE")

from state import set_event

def initialize_pipeline():
    """Initialize the pipeline and set it to active"""
    reset_execution_pipeline()
    set_event(PIPELINE_ACTIVE, "PIPELINE_ACTIVE")
    return time.strftime("%Y%m%d_%H%M%S")

def cancel_pipeline_after_timeout(timeout_seconds=1800):
    """Cancel the pipeline after a timeout"""
    def timeout_handler():
        # Wait for timeout
        time.sleep(timeout_seconds)
        # If pipeline is still active, reset it
        if PIPELINE_ACTIVE.is_set():
            reset_execution_pipeline()
            logger.warning(f"Pipeline automatically reset after {timeout_seconds}s timeout")

    # Start timeout thread
    timer_thread = threading.Thread(target=timeout_handler)
    timer_thread.daemon = True
    timer_thread.start()
    return timer_thread
