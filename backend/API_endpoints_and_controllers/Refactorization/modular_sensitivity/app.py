from flask import Flask
from flask_cors import CORS
import os
import sys
import time
import threading
import filelock
from config import LOGS_DIR

# Import and configure shared logging
from .logging_config import setup_logging, logger

setup_logging(logs_dir=LOGS_DIR)

# Import blueprints
from blueprints.health import health_bp
from blueprints.payload import payload_bp
from blueprints.baseline import baseline_bp
from blueprints.sensitivity import sensitivity_bp
from blueprints.runs import runs_bp
from blueprints.advanced_sensitivity import advanced_sensitivity_bp

# Import middleware
from middleware import check_endpoint_availability

# Import pipeline reset function
from pipeline import reset_execution_pipeline
from state import set_event

# Import configuration
from config import LOGS_DIR, CONFIG_LOCK_FILE, RUN_LOCK_FILE, VISUALIZATION_LOCK_FILE, PAYLOAD_LOCK_FILE, BASELINE_LOCK_FILE

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app)

    # Register middleware
    app.before_request(check_endpoint_availability)

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(payload_bp)
    app.register_blueprint(baseline_bp)
    app.register_blueprint(sensitivity_bp)
    app.register_blueprint(runs_bp)
    app.register_blueprint(advanced_sensitivity_bp)

    return app

def run_health_check():
    """Background thread for periodic health checks"""
    while True:
        logger.info("Performing system health check")
        # Check critical resources
        for lock_file in [CONFIG_LOCK_FILE, RUN_LOCK_FILE, VISUALIZATION_LOCK_FILE,
                         PAYLOAD_LOCK_FILE, BASELINE_LOCK_FILE]:
            if os.path.exists(lock_file):
                try:
                    with filelock.FileLock(lock_file, timeout=1):
                        logger.debug(f"Lock file {lock_file} is accessible")
                except filelock.Timeout:
                    logger.warning(f"Lock file {lock_file} is stuck")

        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    # Use filelock to ensure single instance
    app_lock = filelock.FileLock(os.path.join(LOGS_DIR, "app.lock"))
    try:
        with app_lock.acquire(timeout=5):
            logger.info("Acquired application lock - starting single instance")

            # Ensure all lock files are cleaned up on startup
            for lock_file in [CONFIG_LOCK_FILE, RUN_LOCK_FILE, VISUALIZATION_LOCK_FILE,
                            PAYLOAD_LOCK_FILE, BASELINE_LOCK_FILE]:
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                        logger.debug(f"Cleaned up lock file: {lock_file}")
                    except Exception as e:
                        logger.error(f"Failed to clean lock file {lock_file}: {str(e)}")

            # Initialize event flags
            reset_execution_pipeline()

            # Start health check thread
            health_thread = threading.Thread(target=run_health_check, daemon=True)
            health_thread.start()
            logger.info("Started health check background thread")

            # Create and run the application
            app = create_app()
            logger.info("Starting Flask application on 127.0.0.1:2500")
            app.run(debug=True, host='127.0.0.1', port=2500)

    except filelock.Timeout:
        logger.error("Another instance is already running - exiting")
        sys.exit(1)
