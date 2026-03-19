import os
import logging
import logging.config
import sys

# ---------------- Logging Setup Block Start ----------------
print(sys.executable)
print(sys.path)
# Determine the directory for log files
log_directory = os.getcwd()
# Define the log file paths
price_optimization_log = os.path.join(log_directory, 'price_optimization.log')

# Set up paths for log files
log_directory = os.getcwd()
price_optimization_log = os.path.join(log_directory, 'price_optimization.log')
app_cfa_log = os.path.join(log_directory, 'app_CFA.log')

# Ensure the log directory exists
os.makedirs(log_directory, exist_ok=True)

# Basic logger setup for price optimization and CFA
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO for both loggers
    format='%(asctime)s - %(message)s',
)

# Create specific loggers with separate file handlers
price_logger = logging.getLogger('price_optimization')
price_handler = logging.FileHandler(price_optimization_log)
price_handler.setLevel(logging.INFO)
price_logger.addHandler(price_handler)

cfa_logger = logging.getLogger('app_cfa')
cfa_handler = logging.FileHandler(app_cfa_log)
cfa_handler.setLevel(logging.INFO)
cfa_logger.addHandler(cfa_handler)

# Example log usage
price_logger.info("Price optimization started.")
cfa_logger.info("CFA process initiated.")
# ---------------- Logging Setup Block End ----------------

# ---------------- Utility Function Block Start ----------------
# Function to remove existing files
def remove_existing_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.debug(f"Removed existing file: {file_path}")
    else:
        logging.debug(f"No existing file to remove: {file_path}")
# ---------------- Utility Function Block End ----------------

# Helper function to pad or trim costs
def pad_or_trim(costs, target_length):
    if len(costs) < target_length:
        return costs + [0] * (target_length - len(costs))
    return costs[:target_length]