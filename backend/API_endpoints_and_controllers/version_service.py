from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Define the base directory of the project
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
STATIC_FOLDER = os.path.join(BASE_DIR, 'Original')

def get_all_versions():
    """Scan the Original directory and extract version numbers from Batch folders."""
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)
    
    import re
    versions = set()  # Use set to avoid duplicates
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(STATIC_FOLDER):
        for dir_name in dirs:
            # Match both Batch(X) and Batch(X.Y) formats
            match = re.match(r'Batch\((\d+(?:\.\d+)?)\)', dir_name)
            if match:
                version_str = match.group(1)
                try:
                    # Convert to float for decimal versions, but keep as int if possible
                    version = float(version_str)
                    if version.is_integer():
                        version = int(version)
                    versions.add(version)
                except ValueError:
                    continue

    # Return sorted list of unique versions
    return sorted(list(versions))

@app.route('/versions', methods=['GET'])
def list_versions_route():
    try:
        versions = get_all_versions()
        return jsonify({"versions": versions}), 200
    except Exception as e:
        return jsonify({"message": "Error listing versions", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8002)
