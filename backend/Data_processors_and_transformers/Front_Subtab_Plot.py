"""
Flask server setup for handling PNG file requests.

This module sets up a Flask server that provides an API endpoint to retrieve a list of PNG files for a given version. The server scans the file system to find the available versions and the corresponding PNG files, and returns the file information as a JSON response.

The main functions are:
- `get_available_versions(directory: str) -> List[str]`: Retrieves a list of available versions based on the directory structure.
- `log_png_file_names_for_versions(versions: List[str], base_directory: str) -> None`: Logs the names and paths of all PNG files found for the given versions.
- `get_png_files(version: str) -> Tuple[str, int]`: Handles the API request to retrieve the PNG file information for the given version.
"""
# Flask server setup for handling PNG file requests

from flask import Flask, jsonify
from flask_cors import CORS
import os
import re
import logging
import logging.config
from typing import List, Dict, Tuple

app = Flask(__name__)
CORS(app)

BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Original")

def get_available_versions(directory: str) -> List[str]:
    versions = []
    if os.path.exists(directory):
        for folder_name in os.listdir(directory):
            if folder_name.startswith("Batch(") and folder_name.endswith(")"):
                version = folder_name.split("(")[1].split(")")[0]
                versions.append(version)
        logging.info(f"Available versions: {versions}")
    else:
        logging.warning(f"Directory does not exist: {directory}")
    return versions

def log_png_file_names_for_versions(versions: List[str], base_directory: str) -> None:
    for version in versions:
        version_folder = f"{base_directory}/Batch({version})/Results({version})/"
        if os.path.exists(version_folder):
            logging.info(f"Fetching PNG files for version {version} in folder {version_folder}")
            albums = [d for d in os.listdir(version_folder) if os.path.isdir(os.path.join(version_folder, d))]

            # Filter to include both new album format and legacy AnnotatedStaticPlots directories
            valid_albums = [a for a in albums if 
                           (a.endswith("_PlotType_" + a.split("_PlotType_")[1]) if "_PlotType_" in a else False) or 
                            "_AnnotatedStaticPlots" in a]
            
            for album in valid_albums:
                album_folder = os.path.join(version_folder, album)
                
                if os.path.exists(album_folder):
                    for filename in os.listdir(album_folder):
                        if filename.lower().endswith('.png'):
                            file_path = os.path.join(album_folder, filename)
                            logging.info(f"PNG file found: {filename}")
                            logging.info(f"Constructed Path: {file_path}")
                            logging.info(f"Exact Position: Version: {version}, Album: {album}")
                else:
                    logging.warning(f"Album folder does not exist for version {version}: {album_folder}")
        else:
            logging.warning(f"Results folder does not exist for version {version}: {version_folder}")

# In get_png_files function, enhance album handling
@app.route('/api/album/<version>', methods=['GET'])
def get_png_files(version: str) -> Tuple[str, int]:
    logging.info(f"Received request for PNG files with version: {version}")
    
    version_folder = f"{BASE_PATH}/Batch({version})/Results({version})/"
    
    if not os.path.exists(version_folder):
        logging.warning(f"Results folder does not exist: {version_folder}")
        return jsonify({"error": "Version folder not found"}), 404

    # Look for both organized albums and legacy directories
    albums = [d for d in os.listdir(version_folder) 
              if os.path.isdir(os.path.join(version_folder, d))]
    
    # Filter to include both new album format and legacy AnnotatedStaticPlots directories
    valid_albums = [a for a in albums if 
                   (a.endswith("_PlotType_" + a.split("_PlotType_")[1]) if "_PlotType_" in a else False) or 
                    "_AnnotatedStaticPlots" in a]
    
    png_files = []
    
    for album in valid_albums:
        album_folder = os.path.join(version_folder, album)
        
        if not os.path.exists(album_folder):
            logging.warning(f"Album folder does not exist: {album_folder}")
            continue

        for filename in os.listdir(album_folder):
            if filename.lower().endswith('.png'):
                file_path = os.path.join(album_folder, filename)
                png_files.append({
                    "name": filename,
                    "path": file_path,
                    "album": album
                })
                logging.info(f"PNG file found: {filename}")
    
    if not png_files:
        logging.info(f"No PNG files found for version {version}")
        return jsonify({"message": "No PNG files found"}), 404

    return jsonify(png_files), 200

if __name__ == '__main__':
    logging.info("Starting Flask server on port 8008")
    base_directory = BASE_PATH
    versions = get_available_versions(base_directory)
    log_png_file_names_for_versions(versions, base_directory)
    app.run(debug=True, port=8008)
