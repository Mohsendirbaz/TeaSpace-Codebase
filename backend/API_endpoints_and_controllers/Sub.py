from flask import Flask, request
from flask_cors import CORS
import subprocess
import os
import logging
import json

# Set up paths relative to the current file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Set up logging
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
log_file_path = os.path.join(LOGS_DIR, 'Flask_Sub.log')
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.info("Flask Sub.py logging initialized")

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes



script_dir = os.path.join(BASE_DIR, 'backend', 'Visualization_generators')
script_files = [ 'AggregatedSubPlots.py']

@app.route('/runSub', methods=['POST'])
def run_scripts():
    data = request.get_json()
    selected_versions = data.get('selectedVersions', [1])
    selected_properties = data.get('selectedProperties', ['initialSellingPriceAmount13'])  # Default to a list
    remarks = data.get('remarks', 'on')  # New remarks state passed from frontend
    customized_features = data.get('customizedFeatures', 'off')
    subplot_selection = data.get('subplotSelection', None)

    logging.info(f"Received data: {data}")


    try:
        # Change working directory to the script directory
        os.chdir(script_dir)
        logging.info(f"Changed working directory to: {script_dir}")

        # Convert versions and properties to a string format suitable for command line arguments
        selected_versions_str = ",".join(map(str, selected_versions))
        selected_properties_str = ",".join(selected_properties)

        logging.debug(f"Formatted versions string: {selected_versions_str}")
        logging.debug(f"Formatted properties string: {selected_properties_str}")

        # Run the script with the selected versions, properties, and remarks as arguments
        for script_filename in script_files:

            result = subprocess.run(
                ['python', script_filename, selected_versions_str, selected_properties_str, remarks, customized_features, json.dumps(subplot_selection)],  # Added remarks argument
                capture_output=True, text=True
            )

            # Check for errors in each script execution
            if result.returncode != 0:
                logging.error(f"Error running {script_filename}: {result.stderr}")
                return f"Error running {script_filename}: {result.stderr}", 500

        try:
            # Import and run HTML album organizer
            organizer_path = os.path.join(os.path.dirname(__file__), 'html_album_organizer.py')
            if os.path.exists(organizer_path):
                result = subprocess.run(
                    ['python', organizer_path],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    logging.error(f"Error running HTML album organizer: {result.stderr}")
                else:
                    logging.info("HTML album organization completed")
        except Exception as e:
            logging.error(f"Error during HTML album organization: {str(e)}")
            # Continue with normal flow, don't fail the request

    except FileNotFoundError:
        logging.error(f"File not found in directory: {script_dir}")
        return f"File not found in directory: {script_dir}", 404
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running scripts: {e}")
        return f"Error running scripts: {e}", 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return f"Unexpected error: {e}", 500

    return '', 204  # No Content response

if __name__ == '__main__':
    app.run(debug=True, port=5009)
