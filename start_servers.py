import subprocess
import os
import sys
from pathlib import Path

def check_file_exists(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    return True

def get_pid_for_port(port):
    try:
        result = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, universal_newlines=True)
        if result:
            for line in result.splitlines():
                if f":{port}" in line:
                    try:
                        pid = int(line.strip().split()[-1])
                        if pid != 0:  # Skip system process
                            # Verify process exists
                            subprocess.check_output(f"tasklist /FI \"PID eq {pid}\"", shell=True)
                            return pid
                    except (ValueError, subprocess.CalledProcessError):
                        continue
    except subprocess.CalledProcessError:
        pass
    return None

def free_port(port):
    pid = get_pid_for_port(port)
    if pid:
        try:
            # Use taskkill with no output
            subprocess.run(f"taskkill /PID {pid} /F >nul 2>&1", shell=True)
        except subprocess.CalledProcessError:
            pass

# Base directory where your Flask apps are located
flask_base_dir = os.path.join(os.path.dirname(__file__))

# List of Flask apps with their subdirectories and ports
flask_apps = [
    (r"backend\Data_processors_and_transformers\Front_Subtab_Table.py", 8007),
    (r"backend\Data_processors_and_transformers\Front_Subtab_Plot.py", 8008),
    (r"backend\Data_processors_and_transformers\Front_Subtab_HTML.py", 8009),
    (r"backend\API_endpoints_and_controllers\Create_new_batch.py", 8001),
    (r"backend\API_endpoints_and_controllers\Remove_batch.py", 7001),
    (r"backend\API_endpoints_and_controllers\Calculations.py", 5007),
    (r"backend\API_endpoints_and_controllers\Calculations_and_Sensitivity.py", 2500),
    (r"backend\API_endpoints_and_controllers\sense_config_base.py", 2600),
    (r"backend\API_endpoints_and_controllers\IND2751.py", 2751),
    (r"backend\API_endpoints_and_controllers\PNG.py", 5008),
    (r"backend\API_endpoints_and_controllers\Sub.py", 5009),
    (r"backend\Utility_functions\property_mapping_service.py", 5010),
    (r"backend\API_endpoints_and_controllers\Load.py", 5000),
    (r"backend\API_endpoints_and_controllers\ConfigurationAPI.py", 5002),
    (r"backend\API_endpoints_and_controllers\CalSen.py", 2750),
    (r"backend\cfa_list.py", 4560),
    (r"backend\API_endpoints_and_controllers\Version_service.py", 8002),
    (r"backend\API_endpoints_and_controllers\subplot_metadata.py", 5011),
]

# Base directory where your Node.js scripts are located
node_base_dir = os.path.dirname(os.path.abspath(__file__))

# List of Node.js scripts to run with their respective ports
node_scripts = [
    ("submit_parameter_append.js", 3040),
    ("submitCompleteSet.js", 3052),
    (r"labelUpdate.js", 3060)
]

def verify_python_installation():
    try:
        subprocess.run(["python", "--version"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        print("Error: Python is not installed or not in PATH")
        return False

def verify_node_installation():
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        print("Error: Node.js is not installed or not in PATH")
        return False

def start_flask_apps():
    if not verify_python_installation():
        return []

    # Add flask_api directory to Python path for theme routes
    flask_api_dir = os.path.join(flask_base_dir, 'backend', 'flask_api')
    if flask_api_dir not in sys.path:
        sys.path.append(flask_api_dir)

    flask_processes = []
    for app, port in flask_apps:
        app_path = os.path.join(flask_base_dir, app)
        if not check_file_exists(app_path):
            continue

        # Silently free the port before starting the app
        free_port(port)

        try:
            env = os.environ.copy()
            env['PORT'] = str(port)

            # For theme routes app, run from its directory
            if 'flask_api\\app.py' in app:
                working_dir = os.path.dirname(app_path)
            else:
                working_dir = flask_base_dir

            process = subprocess.Popen(
                ["python", app_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env,
                cwd=working_dir
            )
            # Wait a moment to check if process started successfully
            import time
            time.sleep(1)

            if process.poll() is None:  # Process is still running
                flask_processes.append((process, port))  # Store process and port
                print(f"Started Flask app '{app}' on port {port}")
            else:
                out, err = process.communicate()
                if err:
                    print(f"Error starting Flask app '{app}': {err}")

        except Exception as e:
            print(f"Failed to start Flask app '{app}' on port {port}. Error: {e}")
    return flask_processes

def start_node_scripts():
    if not verify_node_installation():
        return []

    node_processes = []
    for script, port in node_scripts:
        script_path = os.path.join(node_base_dir, script)
        if not check_file_exists(script_path):
            continue

        # Silently free the port before starting the script
        free_port(port)

        try:
            process = subprocess.Popen(
                ["node", script_path, "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            # Wait a moment to check if process started successfully
            import time
            time.sleep(1)

            if process.poll() is None:  # Process is still running
                node_processes.append((process, port))  # Store process and port
                print(f"Started Node.js script '{script}' on port {port}")
            else:
                out, err = process.communicate()
                if err:
                    print(f"Error starting Node.js script '{script}': {err}")

        except Exception as e:
            print(f"Failed to start Node.js script '{script}' on port {port}. Error: {e}")
    return node_processes

if __name__ == "__main__":
    print("Checking dependencies and starting servers...")

    # Verify all paths exist before starting
    all_paths_valid = True
    for app, _ in flask_apps:
        app_path = os.path.join(flask_base_dir, app)
        if not check_file_exists(app_path):
            all_paths_valid = False

    for script, _ in node_scripts:
        script_path = os.path.join(node_base_dir, script)
        if not check_file_exists(script_path):
            all_paths_valid = False

    if not all_paths_valid:
        print("Error: Some required files are missing. Please check the paths.")
        sys.exit(1)

    # Start Flask apps and Node.js scripts
    flask_processes = start_flask_apps()
    node_processes = start_node_scripts()

    if not flask_processes and not node_processes:
        print("Error: No servers could be started. Please check the logs above.")
        sys.exit(1)

    print("Servers started. Press Ctrl+C to stop.")

    try:
        # Wait for all processes
        all_processes = flask_processes + node_processes
        while True:
            # Check if any process has terminated
            for process, port in all_processes:
                if process.poll() is not None:
                    out, err = process.communicate()
                    if err:
                        print(f"Process on port {port} terminated with error: {err}")
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTermination signal received. Stopping servers...")

        # Terminate all processes
        for process, port in flask_processes + node_processes:
            try:
                process.terminate()
                print(f"Terminated process on port {port}")
            except:
                pass  # Process may have already terminated

        print("All servers stopped. Exiting.")
