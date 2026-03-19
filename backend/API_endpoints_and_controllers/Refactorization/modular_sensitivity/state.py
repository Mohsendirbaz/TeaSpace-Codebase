import threading
from .logging_config import get_module_logger

logger = get_module_logger(__name__)

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

# Pipeline active flag (holds all routes except the active one)
PIPELINE_ACTIVE = threading.Event()

# Add logging for lock acquisitions
def acquire_lock(lock, name):
    """Helper to log lock acquisitions"""
    lock.acquire()
    logger.info(f"Acquired lock: {name}")
    return lock

# Add logging for event flag changes
def set_event(event, name):
    """Helper to log event flag changes"""
    event.set()
    logger.info(f"Set event flag: {name}")
    return event

def clear_event(event, name):
    """Helper to log event flag clears"""
    event.clear()
    logger.info(f"Cleared event flag: {name}")
    return event
