"""Flask service (port:8009) - Processes HTML files from batch results"""
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import re
import logging
import logging.config
import time
from pathlib import Path
from collections import deque

app = Flask(__name__)
CORS(app)

# Create a circular buffer to store the last 100 log messages
log_buffer = deque(maxlen=100)

# Custom log handler that stores messages in the buffer
class BufferHandler(logging.Handler):
    def emit(self, record):
        log_entry = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.created)),
            'level': record.levelname,
            'message': self.format(record)
        }
        log_buffer.append(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add the buffer handler to the root logger
buffer_handler = BufferHandler()
buffer_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(buffer_handler)

# Use Path for more consistent path handling
BASE_PATH = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "Original"

def get_versions(directory: Path):
    if not directory.exists():
        logging.warning(f"Directory not found: {directory}")
        return []
    return [name.split("(")[1].split(")")[0] for name in os.listdir(directory)
            if name.startswith("Batch(") and name.endswith(")")]

# Updated get_html_files function to handle HTML files in the nested directory structure
@app.route('/api/album_html/<version>')
def get_html_files(version: str):
    import time
    from threading import Timer

    # Define a timeout handler
    class TimeoutError(Exception):
        pass

    # Set a timeout for the entire request (30 seconds)
    REQUEST_TIMEOUT = 30

    # Start timing the request
    start_time = time.time()
    logging.info(f"Processing request for version: {version} (timeout: {REQUEST_TIMEOUT}s)")
    html_files = []

    # Instead of using a timer that raises an exception, we'll check the elapsed time periodically
    # This is more reliable than trying to raise an exception from a different thread
    timeout_timer = None
    request_timed_out = False

    # Define a function to set the timeout flag
    def mark_request_as_timed_out():
        nonlocal request_timed_out
        logging.error(f"Request timed out after {REQUEST_TIMEOUT} seconds")
        request_timed_out = True

    # Start a timer that will set the timeout flag
    timeout_timer = Timer(REQUEST_TIMEOUT, mark_request_as_timed_out)
    timeout_timer.daemon = True  # Allow the timer to be killed when the program exits
    timeout_timer.start()

    try:
        # Function to check if we're approaching timeout
        def is_timeout_approaching():
            elapsed = time.time() - start_time
            return elapsed > (REQUEST_TIMEOUT * 0.8)  # 80% of timeout

        if not BASE_PATH.exists():
            logging.warning(f"Directory not found: {BASE_PATH}")
            return jsonify([])

        # Construct the path to the version's Results directory
        version_folder = BASE_PATH / f"Batch({version})" / f"Results({version})"
        logging.info(f"Scanning directory: {version_folder}")

        if not version_folder.exists():
            logging.warning(f"Version folder not found: {version_folder}")
            return jsonify([])

        # Look for HTML files in the Results directory
        try:
            items = os.listdir(version_folder)
            logging.info(f"Found {len(items)} items in {version_folder}")

            # Process directories first (they're more likely to contain HTML files)
            directories = [item for item in items if os.path.isdir(version_folder / item)]
            files = [item for item in items if not os.path.isdir(version_folder / item) and item.lower().endswith('.html')]

            # Log all directories to help with debugging
            logging.info(f"Directories found: {directories}")
            logging.info(f"HTML files found in root: {files}")

            # Check if the request has timed out
            if request_timed_out:
                logging.warning("Request timed out while processing directories")
                return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408

            # First, prioritize known HTML directories that match our patterns
            html_directories = []
            for item in directories:
                # Check if it's a directory that matches our HTML patterns
                if (item.startswith('v') and ('_Plot' in item or '_Cumulative_Plot' in item)) or item.startswith('HTML_v'):
                    html_directories.append(item)

            # Process HTML directories first
            logging.info(f"HTML directories to process: {html_directories}")
            for item in html_directories:
                # Check if the request has timed out
                if request_timed_out:
                    logging.warning("Request timed out while processing HTML directories")
                    return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408

                item_path = version_folder / item

                # Skip processing if we've already spent too much time
                elapsed_time = time.time() - start_time
                if elapsed_time > REQUEST_TIMEOUT * 0.7:  # Use 70% of timeout as a safety margin
                    logging.warning(f"Approaching timeout ({elapsed_time:.2f}s), skipping remaining HTML directories")
                    break

                # Check if it's a directory that might contain HTML files
                logging.info(f"Checking HTML directory: {item_path}")
                try:
                    # Check if the request has timed out
                    if request_timed_out:
                        logging.warning("Request timed out while listing HTML directory")
                        return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408

                    dir_files = [f for f in os.listdir(item_path) if f.lower().endswith('.html')]
                    logging.info(f"Found {len(dir_files)} HTML files in {item_path}")

                    # Process only the first 5 HTML files to avoid timeout
                    for file in dir_files[:5]:
                        # Check if the request has timed out
                        if request_timed_out:
                            logging.warning("Request timed out while processing HTML files")
                            return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408

                        process_html_file(file, item_path, html_files)

                        # Check time after each file to avoid timeout
                        elapsed_time = time.time() - start_time
                        if elapsed_time > REQUEST_TIMEOUT * 0.8:
                            logging.warning(f"Approaching timeout ({elapsed_time:.2f}s), stopping HTML file processing")
                            break
                except Exception as e:
                    logging.error(f"Error processing directory {item_path}: {str(e)}")
                    continue

            # If we have enough HTML files, skip processing other directories
            if len(html_files) >= 5:
                logging.info(f"Found {len(html_files)} HTML files, skipping other directories")
            else:
                # Check if the request has timed out
                if request_timed_out:
                    logging.warning("Request timed out before processing other directories")
                    return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408

                # Process other directories if we haven't found enough HTML files
                other_directories = [item for item in directories if item not in html_directories]
                logging.info(f"Other directories to process: {other_directories}")
                for item in other_directories:
                    # Check if the request has timed out
                    if request_timed_out:
                        logging.warning("Request timed out while processing other directories")
                        return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408

                    item_path = version_folder / item

                    # Skip processing if we've already spent too much time
                    elapsed_time = time.time() - start_time
                    if elapsed_time > REQUEST_TIMEOUT * 0.8:  # Use 80% of timeout as a safety margin
                        logging.warning(f"Approaching timeout ({elapsed_time:.2f}s), skipping remaining directories")
                        break

                    # Check if it's a directory that might contain HTML files
                    logging.info(f"Checking directory: {item_path}")
                    try:
                        dir_files = [f for f in os.listdir(item_path) if f.lower().endswith('.html')]
                        logging.info(f"Found {len(dir_files)} HTML files in {item_path}")

                        # Process only the first 3 HTML files to avoid timeout
                        for file in dir_files[:3]:
                            process_html_file(file, item_path, html_files)

                            # Check time after each file to avoid timeout
                            elapsed_time = time.time() - start_time
                            if elapsed_time > REQUEST_TIMEOUT * 0.9:
                                logging.warning(f"Approaching timeout ({elapsed_time:.2f}s), stopping HTML file processing")
                                break
                    except Exception as e:
                        logging.error(f"Error processing directory {item_path}: {str(e)}")
                        continue

            # Process HTML files in the root directory
            # Check if the request has timed out
            if request_timed_out:
                logging.warning("Request timed out before processing root HTML files")
                return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408

            for file in files:
                # Check if the request has timed out
                if request_timed_out:
                    logging.warning("Request timed out while processing root HTML files")
                    return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408

                # Skip processing if we've already spent too much time
                elapsed_time = time.time() - start_time
                if elapsed_time > REQUEST_TIMEOUT * 0.9:  # Use 90% of timeout as a safety margin
                    logging.warning(f"Approaching timeout ({elapsed_time:.2f}s), skipping remaining files")
                    break

                process_html_file(file, version_folder, html_files)

        except Exception as e:
            logging.error(f"Error listing directory {version_folder}: {str(e)}")
            return jsonify({"error": f"Error listing directory: {str(e)}"}), 500

        # Cancel the timeout timer if it exists
        if timeout_timer and timeout_timer.is_alive():
            timeout_timer.cancel()

        # Calculate total processing time
        elapsed_time = time.time() - start_time
        logging.info(f"Request completed in {elapsed_time:.2f}s. Found {len(html_files)} HTML files across {len(set(f['album'] for f in html_files))} albums")

        # If we found no HTML files but the directories exist, return a more helpful error
        if len(html_files) == 0 and len(directories) > 0:
            logging.warning(f"No HTML files found in {len(directories)} directories")
            return jsonify({"error": "No HTML files found in the specified directories. Please check the server logs for more information."}), 404

        return jsonify(html_files)

    except Exception as e:
        logging.error(f"Unexpected error processing request: {str(e)}")
        # Check if the request timed out
        if request_timed_out:
            logging.error(f"Request timed out after {REQUEST_TIMEOUT} seconds")
            return jsonify({"error": f"Request timed out after {REQUEST_TIMEOUT} seconds. Try again with a more specific request."}), 408
        else:
            # Return a more detailed error message to help with debugging
            error_message = f"Unexpected error: {str(e)}"
            logging.error(error_message)
            return jsonify({
                "error": error_message,
                "type": type(e).__name__,
                "details": str(e)
            }), 500
    finally:
        # Make sure to cancel the timeout timer in case of any exception
        if timeout_timer and timeout_timer.is_alive():
            timeout_timer.cancel()

def process_html_file(file, directory, html_files):
    """Helper function to process an HTML file and add it to the list"""
    file_path = directory / file
    try:
        # Set a maximum size for HTML content to prevent memory issues
        MAX_HTML_SIZE = 1024 * 1024  # 1MB limit

        # Get file size before reading
        try:
            file_size = os.path.getsize(file_path)
            logging.info(f"Processing HTML file: {file_path}, size: {file_size} bytes")
        except OSError as e:
            logging.error(f"Error getting file size for {file_path}: {e}")
            # Create a placeholder with error information
            html_files.append({
                "name": file,
                "content": f"<html><body><h1>Error: File Not Accessible</h1><p>Could not access file: {str(e)}</p></body></html>",
                "album": directory.name,
                "display_name": f"Error: {directory.name}",
                "path": str(file_path),
                "error": str(e),
                "content_length": 0,
                "has_valid_content": False
            })
            return  # Skip further processing for this file

        content = ""
        if file_size > MAX_HTML_SIZE:
            logging.warning(f"HTML file too large: {file_path} ({file_size} bytes), truncating to {MAX_HTML_SIZE} bytes")
            # Read only the first MAX_HTML_SIZE bytes
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read(MAX_HTML_SIZE)
                    content += "\n<!-- Content truncated due to size limit -->"
            except Exception as e:
                logging.error(f"Error reading large file {file_path}: {e}")
                content = f"<html><body><h1>Error: File Read Error</h1><p>The file {file} could not be read: {str(e)}</p></body></html>"
        else:
            # Read the HTML content with proper encoding and error handling
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

                # Verify content is valid HTML
                if not content or not content.strip():
                    logging.warning(f"Empty HTML content in {file_path}")
                    content = f"<html><body><h1>Error: Empty HTML Content</h1><p>The file {file} appears to be empty.</p></body></html>"
                elif not ('<html' in content.lower() or '<!doctype html' in content.lower()):
                    logging.warning(f"Content in {file_path} does not appear to be valid HTML")
                    # Wrap the content in basic HTML tags if it doesn't look like HTML
                    content = f"<html><body><pre>{content}</pre></body></html>"
            except UnicodeDecodeError as ude:
                logging.error(f"Unicode decode error reading {file_path}: {ude}")
                # Provide a fallback HTML content
                content = f"<html><body><h1>Error: Unicode Decode Error</h1><p>The file {file} could not be decoded as text.</p></body></html>"
            except Exception as read_error:
                logging.error(f"Error reading {file_path}: {read_error}")
                # Provide a fallback HTML content
                content = f"<html><body><h1>Error: File Read Error</h1><p>The file {file} could not be read: {str(read_error)}</p></body></html>"

        # Log the content length to verify it's being read correctly
        logging.info(f"Read HTML content from {file}, length: {len(content)}")

        album = directory.name

        # Check if this is from an organized album (HTML_v1_2_PlotType)
        album_match = re.match(r"HTML_v(\d+_\d+)_(.+)", album)
        if album_match:
            # This is an organized album
            versions_id = album_match.group(1)
            plot_type = album_match.group(2)
            display_name = f"{plot_type.replace('_', ' ')} for versions [{versions_id.replace('_', ', ')}]"
        else:
            # Check if this is a legacy plot directory (v1_2_Annual_Cash_Flows_Plot or v1_Annual_Cash_Flows_Plot)
            legacy_match = re.match(r"v(\d+(?:_\d+)*)_(.+?)(_Plot)?$", album)
            if legacy_match:
                versions_id = legacy_match.group(1)
                plot_type = legacy_match.group(2)
                display_name = f"{plot_type.replace('_', ' ')} for versions [{versions_id.replace('_', ', ')}]"
            else:
                # Check if this is a cumulative plot directory (v1_Cumulative_Plot)
                cumulative_match = re.match(r"v(\d+)_Cumulative_Plot", album)
                if cumulative_match:
                    versions_id = cumulative_match.group(1)
                    display_name = f"Cumulative Plot for version {versions_id}"
                else:
                    # Fall back to the original album name
                    display_name = album.replace('_', ' ')

        # Create the HTML file object with all necessary information
        html_file_obj = {
            "name": file,
            "content": content,  # Include the full HTML content
            "album": album,
            "display_name": display_name,
            "path": str(file_path),  # Convert Path to string for JSON serialization
            "content_length": len(content),  # Add content length for debugging
            "has_valid_content": bool(content and content.strip())  # Add flag for valid content
        }

        # Log the object structure (without the full content)
        logging.info(f"Created HTML file object: {file}, album: {album}, path: {str(file_path)}, content_length: {len(content)}, has_valid_content: {bool(content and content.strip())}")

        # Add to the list of HTML files
        html_files.append(html_file_obj)
        logging.info(f"Processed {file} from album {album}")
    except Exception as e:
        logging.error(f"Failed to process {file}: {e}")
        logging.error(f"Exception details: {str(e)}")
        # Add a placeholder HTML file object with error information
        try:
            html_files.append({
                "name": file,
                "content": f"<html><body><h1>Error Processing File</h1><p>{str(e)}</p></body></html>",
                "album": directory.name,
                "display_name": f"Error: {directory.name}",
                "path": str(file_path),
                "error": str(e),
                "content_length": 0,
                "has_valid_content": False
            })
            logging.info(f"Added placeholder for {file} due to processing error")
        except Exception as placeholder_error:
            logging.error(f"Failed to add placeholder for {file}: {placeholder_error}")

# Add a route to serve static files from the correct directory
@app.route('/static/html/<version>/<album>/<filename>')
def serve_html(version, album, filename):
    """Serve HTML files from the correct directory based on version and album"""
    # Construct the path to the HTML file
    version_folder = BASE_PATH / f"Batch({version})" / f"Results({version})"
    file_path = version_folder / album / filename

    # If not found, try directly in the Results directory
    if not file_path.exists():
        file_path = version_folder / filename

    # Check if the file exists
    if not file_path.exists():
        return "File not found", 404

    # Serve the file from its directory
    try:
        return send_from_directory(str(file_path.parent), file_path.name)
    except Exception as e:
        return f"Error serving file: {e}", 500


@app.route('/test')
def test():
    """Simple test endpoint to check if the server is running"""
    return jsonify({"status": "ok", "message": "Server is running"}), 200

@app.route('/test/album_endpoints')
def test_album_endpoints():
    """
    Test endpoint to verify the album HTML content endpoints are working

    This endpoint tests both /api/album_html_content/<album> and /api/album_html_all
    by attempting to find and retrieve content from the first available album.

    Returns:
        JSON response with test results
    """
    logging.info("Running test for album HTML content endpoints")

    test_results = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "tests": []
    }

    # Test 1: Check if BASE_PATH exists
    test_results["tests"].append({
        "name": "Check BASE_PATH",
        "status": "PASS" if BASE_PATH.exists() else "FAIL",
        "message": f"BASE_PATH exists at {BASE_PATH}" if BASE_PATH.exists() else f"BASE_PATH not found at {BASE_PATH}"
    })

    # Test 2: Find available versions
    versions = get_versions(BASE_PATH)
    test_results["tests"].append({
        "name": "Find available versions",
        "status": "PASS" if versions else "FAIL",
        "message": f"Found versions: {versions}" if versions else "No versions found"
    })

    if not versions:
        return jsonify(test_results), 200

    # Use the first available version for testing
    test_version = versions[0]
    version_folder = BASE_PATH / f"Batch({test_version})" / f"Results({test_version})"

    # Test 3: Check if version folder exists
    test_results["tests"].append({
        "name": "Check version folder",
        "status": "PASS" if version_folder.exists() else "FAIL",
        "message": f"Version folder exists at {version_folder}" if version_folder.exists() else f"Version folder not found at {version_folder}"
    })

    if not version_folder.exists():
        return jsonify(test_results), 200

    # Test 4: Find album directories
    album_dirs = [d for d in version_folder.iterdir() 
                 if d.is_dir() and (d.name.startswith('HTML_v') or 
                                    (d.name.startswith('v') and '_Plot' in d.name))]

    test_results["tests"].append({
        "name": "Find album directories",
        "status": "PASS" if album_dirs else "FAIL",
        "message": f"Found {len(album_dirs)} album directories" if album_dirs else "No album directories found"
    })

    if not album_dirs:
        return jsonify(test_results), 200

    # Use the first available album for testing
    test_album = album_dirs[0].name

    # Test 5: Test /api/album_html_content/<album> endpoint
    try:
        # Simulate a request to the endpoint
        with app.test_client() as client:
            response = client.get(f'/api/album_html_content/{test_album}')

        test_results["tests"].append({
            "name": "Test /api/album_html_content/<album> endpoint",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "message": f"Endpoint returned status code {response.status_code}",
            "details": {
                "status_code": response.status_code,
                "album": test_album
            }
        })
    except Exception as e:
        test_results["tests"].append({
            "name": "Test /api/album_html_content/<album> endpoint",
            "status": "FAIL",
            "message": f"Error testing endpoint: {str(e)}"
        })

    # Test 6: Test /api/album_html_all endpoint
    try:
        # Simulate a request to the endpoint
        with app.test_client() as client:
            response = client.get(f'/api/album_html_all?version={test_version}')

        test_results["tests"].append({
            "name": "Test /api/album_html_all endpoint",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "message": f"Endpoint returned status code {response.status_code}",
            "details": {
                "status_code": response.status_code,
                "version": test_version
            }
        })
    except Exception as e:
        test_results["tests"].append({
            "name": "Test /api/album_html_all endpoint",
            "status": "FAIL",
            "message": f"Error testing endpoint: {str(e)}"
        })

    return jsonify(test_results), 200

@app.route('/api/album_html_content/<album>')
def get_album_html_content(album: str):
    """
    Fetch HTML content for a specific album

    Args:
        album: The album identifier

    Returns:
        JSON response with the album's HTML content
    """
    logging.info(f"Fetching HTML content for album: {album}")

    try:
        # Parse the album name to extract version and album type
        # Expected format: HTML_v{version}_{plot_type} or v{version}_{plot_type}_Plot
        version_match = re.search(r'(?:HTML_)?v(\d+(?:_\d+)*)_', album)

        if not version_match:
            logging.error(f"Invalid album format: {album}")
            return jsonify({"error": f"Invalid album format: {album}"}), 400

        # Extract the version from the album name
        version_str = version_match.group(1).split('_')[0]  # Take the first version if multiple
        logging.info(f"Extracted version: {version_str} from album: {album}")

        # Find the album directory
        version_folder = BASE_PATH / f"Batch({version_str})" / f"Results({version_str})"
        album_dir = version_folder / album

        if not album_dir.exists():
            logging.warning(f"Album directory not found: {album_dir}")
            # Try to find the album directory by partial match
            potential_dirs = [d for d in version_folder.iterdir() if d.is_dir() and album in d.name]
            if potential_dirs:
                album_dir = potential_dirs[0]
                logging.info(f"Found album directory by partial match: {album_dir}")
            else:
                return jsonify({"error": f"Album not found: {album}"}), 404

        # Find all HTML files in the album directory
        html_files = [f for f in album_dir.iterdir() if f.is_file() and f.suffix.lower() == '.html']

        if not html_files:
            logging.warning(f"No HTML files found in album directory: {album_dir}")
            return jsonify({"error": f"No HTML files found in album: {album}"}), 404

        # Get the first HTML file (most albums only have one main HTML file)
        html_file = html_files[0]
        logging.info(f"Using HTML file: {html_file}")

        # Read the HTML content
        try:
            with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            # Return the HTML content
            return jsonify({
                "album": album,
                "file": html_file.name,
                "content": content,
                "path": str(html_file)
            })
        except Exception as e:
            logging.error(f"Error reading HTML file {html_file}: {e}")
            return jsonify({"error": f"Error reading HTML file: {str(e)}"}), 500

    except Exception as e:
        logging.error(f"Error processing album {album}: {e}")
        return jsonify({"error": f"Error processing album: {str(e)}"}), 500

@app.route('/api/album_html_all')
def get_all_albums_html():
    """
    Fetch HTML content for all albums across specified versions

    Query parameters:
        version: One or more version numbers (can be specified multiple times)

    Returns:
        JSON response with all albums' HTML content
    """
    # Get versions from query parameters
    versions = request.args.getlist('version')

    if not versions:
        logging.warning("No versions specified in request")
        return jsonify({"error": "No versions specified"}), 400

    logging.info(f"Fetching HTML content for versions: {versions}")

    all_albums = []

    for version in versions:
        version_folder = BASE_PATH / f"Batch({version})" / f"Results({version})"

        if not version_folder.exists():
            logging.warning(f"Version folder not found: {version_folder}")
            continue

        # Find all potential album directories
        album_dirs = [d for d in version_folder.iterdir() 
                     if d.is_dir() and (d.name.startswith('HTML_v') or 
                                        (d.name.startswith('v') and '_Plot' in d.name))]

        for album_dir in album_dirs:
            # Find HTML files in the album directory
            html_files = [f for f in album_dir.iterdir() 
                         if f.is_file() and f.suffix.lower() == '.html']

            if not html_files:
                continue

            # Get the first HTML file
            html_file = html_files[0]

            try:
                # Read the HTML content
                with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

                # Add album to the list
                all_albums.append({
                    "album": album_dir.name,
                    "version": version,
                    "file": html_file.name,
                    "content": content,
                    "path": str(html_file)
                })

                logging.info(f"Added album: {album_dir.name} from version: {version}")

            except Exception as e:
                logging.error(f"Error reading HTML file {html_file}: {e}")
                # Continue to the next album

    if not all_albums:
        logging.warning("No albums found across specified versions")
        return jsonify({"error": "No albums found"}), 404

    return jsonify(all_albums)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Return the most recent log entries"""
    # Get the number of log entries to return (default to 50)
    count = min(int(request.args.get('count', 50)), 100)

    # Get the log level filter (default to all levels)
    level_filter = request.args.get('level', '').upper()

    # Get the search term filter (default to no filter)
    search_filter = request.args.get('search', '').lower()

    # Filter logs based on level and search term
    filtered_logs = list(log_buffer)
    if level_filter:
        filtered_logs = [log for log in filtered_logs if log['level'] == level_filter]
    if search_filter:
        filtered_logs = [log for log in filtered_logs if search_filter in log['message'].lower()]

    # Return the most recent logs (up to count)
    return jsonify(filtered_logs[-count:])

if __name__ == '__main__':
    # Get available versions and start the server
    versions = get_versions(BASE_PATH)
    logging.info(f"Available versions: {versions}")
    app.run(port=8009)
