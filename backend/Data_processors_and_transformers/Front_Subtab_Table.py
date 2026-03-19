"""Flask service (port:8007) - Processes CSV files from batch results using pandas"""
from flask import Flask, jsonify
from flask_cors import CORS
import os, logging, logging.config
import pandas as pd

app = Flask(__name__)
CORS(app)

BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Original")

def get_versions(directory: str):
    if not os.path.exists(directory):
        logging.warning(f"Directory not found: {directory}")
        return []
    return [name.split("(")[1].split(")")[0] for name in os.listdir(directory) 
            if name.startswith("Batch(") and name.endswith(")")]

@app.route('/api/csv-files/<version>')
def get_csv_files(version: str):
    logging.info(f"Processing request for version: {version}")
    results_path = os.path.join(BASE_PATH, f"Batch({version})", f"Results({version})")
    csv_files = []

    if not os.path.exists(results_path):
        logging.warning(f"Results folder not found: {results_path}")
        return jsonify([])

    for root, _, files in os.walk(results_path):
        for file in files:
            if file.lower().endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    df = pd.read_csv(file_path)
                    csv_files.append({
                        "name": file,
                        "data": df.fillna("null").to_dict(orient='records')
                    })
                    logging.info(f"Processed {file}")
                except Exception as e:
                    logging.error(f"Failed to process {file}: {e}")

    return jsonify(csv_files)

if __name__ == '__main__':
    versions = get_versions(BASE_PATH)
    app.run(port=8007)
