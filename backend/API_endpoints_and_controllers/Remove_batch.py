from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import shutil
import threading
import logging

app = Flask(__name__)
CORS(app)

# Define the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
STATIC_FOLDER = os.path.join(BASE_DIR,'Original')
ORIGINAL_BASE_DIR = os.path.join(BASE_DIR, 'backend', 'Original')

# Ensure the static/uploads directory exists
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

lock = threading.Lock()

def get_all_versions():
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)

    batches = [d for d in os.listdir(STATIC_FOLDER) if os.path.isdir(os.path.join(STATIC_FOLDER, d)) and d.startswith('Batch')]
    versions = []

    for batch in batches:
        try:
            version = int(batch.replace('Batch(', '').replace(')', ''))
            versions.append(version)
        except ValueError:
            pass

    return sorted(versions)


def remove_batch(version):
    """Remove a batch folder for the specified version from both locations."""
    batch_folder = os.path.join(STATIC_FOLDER, f'Batch({version})')
    original_batch_folder = os.path.join(ORIGINAL_BASE_DIR, f'Batch({version})')

    # Ensure thread-safe access
    with lock:
        success_messages = []
        error_messages = []

        # Remove from STATIC_FOLDER
        if os.path.exists(batch_folder):
            try:
                shutil.rmtree(batch_folder)  # Remove the entire folder
                success_messages.append(f"Batch({version}) removed from main location.")
            except Exception as e:
                error_messages.append(f"Error removing main batch: {str(e)}")
        else:
            error_messages.append(f"Batch({version}) does not exist in main location.")

        # Remove from ORIGINAL_BASE_DIR
        if os.path.exists(original_batch_folder):
            try:
                shutil.rmtree(original_batch_folder)  # Remove the entire folder
                success_messages.append(f"Batch({version}) removed from original location.")
            except Exception as e:
                error_messages.append(f"Error removing original batch: {str(e)}")
        else:
            error_messages.append(f"Batch({version}) does not exist in original location.")

        if error_messages and not success_messages:
            return {"status": "error", "message": " ".join(error_messages)}
        elif success_messages:
            logging.info(f"Batch({version}) removed from both locations successfully.")
            return {"status": "success", "message": " ".join(success_messages)}


def clear_log_file(file_path):
    """Clear the contents of a specified log file."""
    if not file_path:
        return {"status": "error", "message": "No file path provided"}

    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}

        # Clear file contents by opening in write mode
        with open(file_path, 'w') as f:
            f.write('')

        return {"status": "success", "message": f"File cleared: {file_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Error clearing file: {str(e)}"}


@app.route('/clear-log', methods=['POST'])
def clear_log_endpoint():
    """Clear the contents of a specified log file."""
    data = request.json
    file_path = data.get('path')

    if not file_path:
        return jsonify({"status": "error", "message": "No file path provided"}), 400

    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": f"File not found: {file_path}"}), 404

        # Clear file contents by opening in write mode
        with open(file_path, 'w') as f:
            f.write('')

        return jsonify({"status": "success", "message": f"File cleared: {file_path}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error clearing file: {str(e)}"}), 500


@app.route('/Remove_batch', methods=['POST'])
def remove_batch_endpoint():
    """Handle batch removal via POST request."""
    data = request.json
    version = data.get('version')
    log_path = data.get('path')  # Get log path if provided

    try:
        # Remove the batch
        rb = remove_batch(version)

        # Clear log if path is provided
        log_result = None
        if log_path:
            log_result = clear_log_file(log_path)

        # Get max version
        versions = get_all_versions()
        max_version = max(versions) if versions else 0

        response_data = {
            "rb": rb,
            "max_version": max_version
        }

        # Add log result if log was cleared
        if log_result:
            response_data["log_result"] = log_result

        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"message": "Error removing batch", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=7001)