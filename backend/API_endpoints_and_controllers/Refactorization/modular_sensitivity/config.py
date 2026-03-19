import os

# Base Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_DIR = os.path.join(BASE_DIR, 'backend')
LOGS_DIR = os.path.join(SCRIPT_DIR, 'Logs')
ORIGINAL_BASE_DIR = os.path.join(BASE_DIR, 'backend', 'Original')

# Create logs directory
os.makedirs(LOGS_DIR, exist_ok=True)

# Status file paths
SENSITIVITY_CONFIG_STATUS_PATH = os.path.join(LOGS_DIR, "sensitivity_config_status.json")
SENSITIVITY_CONFIG_DATA_PATH = os.path.join(LOGS_DIR, "sensitivity_config_data.pkl")
CONFIG_LOCK_FILE = os.path.join(LOGS_DIR, "sensitivity_config.lock")
RUN_LOCK_FILE = os.path.join(LOGS_DIR, "runs.lock")
VISUALIZATION_LOCK_FILE = os.path.join(LOGS_DIR, "visualization.lock")
PAYLOAD_LOCK_FILE = os.path.join(LOGS_DIR, "payload.lock")
BASELINE_LOCK_FILE = os.path.join(LOGS_DIR, "baseline.lock")

# Timeout for waiting (in seconds)
WAIT_TIMEOUT = 600  # 10 minutes

# Script configurations
COMMON_PYTHON_SCRIPTS = [
    os.path.join(SCRIPT_DIR, "Configuration_management", 'formatter.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'module1.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'config_modules.py'),
    os.path.join(SCRIPT_DIR, "Configuration_management", 'Table.py')
]

# Function to get calculation script path
def get_calculation_script(version):
    script_name = f'CFA.py'
    script_path = os.path.join(SCRIPT_DIR, "Core_calculation_engines", script_name)
    if os.path.exists(script_path):
        return script_path
    raise Exception(f"Calculation script not found for version {version}")

def get_sensitivity_calculation_script():
    """Get the CFA-b.py script for sensitivity analysis"""
    script_path = os.path.join(SCRIPT_DIR, "Core_calculation_engines", "CFA-b.py")
    if os.path.exists(script_path):
        return script_path
    raise Exception("CFA-b.py script not found for sensitivity calculations")

CALCULATION_SCRIPTS = {
    'calculateForPrice': get_calculation_script,
    'freeFlowNPV': get_calculation_script
}
