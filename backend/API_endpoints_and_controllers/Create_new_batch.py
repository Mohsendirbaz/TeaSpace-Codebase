from flask import Flask, jsonify
from flask_cors import CORS
import os
import shutil
import threading

app = Flask(__name__)
CORS(app)

# Define the base directory of the project
# Define path directly from project root
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
STATIC_FOLDER = os.path.join(BASE_DIR,'Original')


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

def rename_files_in_folder(folder, old_version, new_version):
    for root, dirs, files in os.walk(folder):
        for filename in files:
            if f'({old_version})' in filename:
                new_filename = filename.replace(f'({old_version})', f'({new_version})')
                src = os.path.join(root, filename)
                dst = os.path.join(root, new_filename)
                os.rename(src, dst)

def find_next_missing_versions(versions):
    """Find all missing version numbers and the next new version number."""
    max_version = max(versions) if versions else 0
    missing_versions = [i for i in range(1, max_version) if i not in versions]
    next_new_version = max_version + 1
    return missing_versions, next_new_version

def create_new_batch():
    with lock:
        current_versions = get_all_versions()
        missing_versions, next_new_version = find_next_missing_versions(current_versions)

        # Create batches for all missing versions
        for version in missing_versions:
            create_batch(version)

        # Create a new batch for the next version after the highest
        create_batch(next_new_version)

        # Return the new batch number
        return next_new_version

def create_batch(version):
    """Create a batch for the specified version number."""
    new_batch_folder = os.path.join(STATIC_FOLDER, f'Batch({version})')
    new_config_folder = os.path.join(new_batch_folder, f'ConfigurationPlotSpec({version})')
    results_folder = os.path.join(new_batch_folder, f'Results({version})')

    if not os.path.exists(new_batch_folder):
        os.makedirs(new_batch_folder)

    if not os.path.exists(new_config_folder):
        os.makedirs(new_config_folder)

    # Ensure the results folder exists
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    # Copy from Batch(0)/ConfigurationPlotSpec(0)
    previous_config_folder = os.path.join(STATIC_FOLDER, f'Batch(0)', f'ConfigurationPlotSpec(0)')
    if os.path.exists(previous_config_folder):
        for item in os.listdir(previous_config_folder):
            src = os.path.join(previous_config_folder, item)
            dst = os.path.join(new_config_folder, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        # Rename files in the new configuration folder after copying
        rename_files_in_folder(new_config_folder, 0, version)

@app.route('/create_new_batch', methods=['POST'])
def create_new_batch_route():
    try:
        # Create a new batch and get the new batch number
        NewBatchNumber = create_new_batch()
        return jsonify({
            "message": "New batch created successfully", 
            "NewBatchNumber": NewBatchNumber
        }), 200
    except Exception as e:
        return jsonify({"message": "Error creating new batches", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8001)
