"""Flask service (port:4560) - Processes CFA CSV files with version selection"""
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os, logging, logging.config
import pandas as pd
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
# Use the same BASE_PATH as the original script
BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Original")
PORT = 4560
CFA_PREFIX = "CFA"

# State management
class ConsolidationJob:
    def __init__(self, job_id: str, versions: List[str]):
        self.job_id = job_id
        self.versions = versions
        self.status = "pending"  # pending, processing, complete, error
        self.progress = 0
        self.message = "Job created"
        self.start_time = datetime.now()
        self.error = None
        self.results = None
        
class AppState:
    def __init__(self):
        self.selected_versions = []
        self.file_paths = {}
        self.consolidation_jobs = {}
        self.cell_details_cache = {}
        
    def update_selected_versions(self, versions: List[str]):
        self.selected_versions = versions
        
    def update_file_path(self, version: str, path: str):
        self.file_paths[version] = path
        
    def get_file_path(self, version: str) -> str:
        return self.file_paths.get(version, "")
    
    def create_consolidation_job(self, versions: List[str]) -> str:
        job_id = str(uuid.uuid4())
        self.consolidation_jobs[job_id] = ConsolidationJob(job_id, versions)
        return job_id
    
    def get_consolidation_job(self, job_id: str) -> Optional[ConsolidationJob]:
        return self.consolidation_jobs.get(job_id)
    
    def update_job_progress(self, job_id: str, progress: float, message: str):
        job = self.get_consolidation_job(job_id)
        if job:
            job.progress = progress
            job.message = message
    
    def complete_job(self, job_id: str, results: Dict):
        job = self.get_consolidation_job(job_id)
        if job:
            job.status = "complete"
            job.progress = 100
            job.message = "Consolidation complete"
            job.results = results
    
    def fail_job(self, job_id: str, error: str):
        job = self.get_consolidation_job(job_id)
        if job:
            job.status = "error"
            job.error = error
            job.message = f"Error: {error}"
    
    def add_cell_details(self, cell_key: str, details: Dict):
        self.cell_details_cache[cell_key] = details
    
    def get_cell_details(self, cell_key: str) -> Optional[Dict]:
        return self.cell_details_cache.get(cell_key)

state = AppState()



def get_cfa_versions() -> List[str]:
    """
    Find all CFA CSV files with versions 1-100 and return their version numbers.
    Handles multiple approaches to ensure files are found.
    """
    global BASE_PATH
    cfa_versions = []
    
    # Log the BASE_PATH to aid in debugging
    logging.info(f"Searching for CFA files in BASE_PATH: {BASE_PATH}")
    
    # Check if the BASE_PATH exists
    if not os.path.exists(BASE_PATH):
        logging.warning(f"Base directory not found: {BASE_PATH}")
        # Try to find the directory through symlink resolution or alternative paths
        alt_paths = [
            os.path.join(os.getcwd(), "public", "Original"),
            os.path.join(os.path.dirname(os.getcwd()), "public", "Original"),
            # Add other potential paths here
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                logging.info(f"Found alternative path: {alt_path}")
                
                BASE_PATH = alt_path
                break
        else:
            logging.error("Could not find a valid BASE_PATH")
            return cfa_versions
    
    # Approach 1: Follow the original script's directory structure
    batch_versions = []
    try:
        dir_contents = os.listdir(BASE_PATH)
        logging.info(f"Directory contents: {dir_contents}")
        
        batch_versions = [name.split("(")[1].split(")")[0] for name in dir_contents
                        if name.startswith("Batch(") and name.endswith(")")]
        logging.info(f"Found batch versions: {batch_versions}")
    except Exception as e:
        logging.error(f"Error reading batch folders: {e}")
    
    # Look for CFA files in the Results folders
    for version in batch_versions:
        try:
            results_path = os.path.join(BASE_PATH, f"Batch({version})", f"Results({version})")
            
            if not os.path.exists(results_path):
                logging.warning(f"Results folder not found: {results_path}")
                continue
                
            for root, _, files in os.walk(results_path):
                for file in files:
                    if file.lower().endswith('.csv'):
                        # First try to find exact CFA files
                        if file.startswith(CFA_PREFIX):
                            file_path = os.path.join(root, file)
                            cfa_versions.append(version)
                            state.update_file_path(version, file_path)
                            logging.info(f"Found CFA file for version {version} at: {file_path}")
                            break  # Only add each version once
        except Exception as e:
            logging.error(f"Error processing version {version}: {e}")
    
    # Approach 2: Direct search for CFA CSV files in the specified range
    if not cfa_versions:
        logging.info("No files found using batch structure. Trying direct CFA file search...")
        
        for root, _, files in os.walk(BASE_PATH):
            for file in files:
                if file.lower().endswith('.csv') and file.startswith(CFA_PREFIX):
                    try:
                        # Try to extract version number from filename
                        version_part = file.replace(CFA_PREFIX, "").lstrip("(").rstrip(").csv")
                        
                        # Try multiple version extraction approaches
                        version = None
                        if version_part.isdigit():
                            version = int(version_part)
                        else:
                            # Try to extract numeric part if mixed with other characters
                            import re
                            match = re.search(r'(\d+)', version_part)
                            if match:
                                version = int(match.group(1))
                        
                        # Only consider versions 1-100
                        if version and 1 <= version <= 100:
                            file_path = os.path.join(root, file)
                            version_str = str(version)
                            if version_str not in cfa_versions:
                                cfa_versions.append(version_str)
                                state.update_file_path(version_str, file_path)
                                logging.info(f"Found CFA version {version} at: {file_path}")
                    except Exception as e:
                        logging.warning(f"Couldn't parse version number from file: {file} - {e}")
    
    # Approach 3: If still no CFA files found, use any CSV files in the batch results
    if not cfa_versions:
        logging.info("No CFA files found. Falling back to any CSV files in batch folders...")
        
        for version in batch_versions:
            try:
                results_path = os.path.join(BASE_PATH, f"Batch({version})", f"Results({version})")
                
                if not os.path.exists(results_path):
                    continue
                    
                csv_found = False
                for root, _, files in os.walk(results_path):
                    if csv_found:
                        break
                    
                    for file in files:
                        if file.lower().endswith('.csv'):
                            file_path = os.path.join(root, file)
                            cfa_versions.append(version)
                            state.update_file_path(version, file_path)
                            logging.info(f"Using CSV file for version {version} at: {file_path}")
                            csv_found = True
                            break
            except Exception as e:
                logging.error(f"Error in fallback processing for version {version}: {e}")
    
    # Approach 4: Generate dummy versions if needed for testing
    if not cfa_versions and os.environ.get("CFA_TEST_MODE") == "1":
        logging.info("Test mode activated. Generating dummy versions...")
        for version in range(1, 6):  # Generate 5 test versions
            version_str = str(version)
            cfa_versions.append(version_str)
            # Use a dummy path
            state.update_file_path(version_str, f"dummy_path_for_testing/CFA({version}).csv")
    
    if not cfa_versions:
        logging.warning("No CFA versions found through any method")
    else:
        logging.info(f"Total CFA versions found: {len(cfa_versions)}")
    
    # Return unique versions sorted numerically
    return sorted(list(set(cfa_versions)), key=int)

def consolidate_data(versions: List[str]) -> Dict:
    """
    Consolidate data from multiple CFA versions into a single result set
    following specific consolidation policies for different columns.
    """
    logging.info(f"Beginning consolidation of versions: {versions}")
    
    consolidated_data = {
        "years": [],
        "columns": [],
        "values": [],
        "sources": {}  # Track sources for decomposition
    }
    
    dfs = []
    
    # Load all dataframes
    for version in versions:
        file_path = state.get_file_path(version)
        if file_path and os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                df['cfa_version'] = version  # Add version tracking
                dfs.append(df)
                logging.info(f"Loaded data from version {version} with {len(df)} rows")
            except Exception as e:
                logging.error(f"Failed to process CFA version {version}: {e}")
    
    if not dfs:
        logging.warning("No data frames could be loaded for consolidation")
        return consolidated_data
    
    # Determine the largest year range
    all_years = set()
    for df in dfs:
        if 'Year' in df.columns:
            all_years.update(df['Year'].unique())
            
    logging.info(f"Processing {len(dfs)} dataframes with years: {all_years}")
    
    # Sort years to maintain chronological order
    consolidated_data["years"] = sorted([int(year) for year in all_years])
    logging.info(f"Consolidated years range: {min(consolidated_data['years'])} to {max(consolidated_data['years'])}")
    
    # Define the policy for each column
    sum_columns = ['Revenue', 'Operating Expenses']
    exclude_columns = ['Loan', 'Federal Taxes', 'State Taxes', 'Depreciation', 
                      'After-Tax Cash Flow', 'Discounted Cash Flow', 'Cumulative Cash Flow']
    
    # Create the standard column list based on the policy
    consolidated_data["columns"] = sum_columns + exclude_columns
    
    # Initialize values with zeros
    consolidated_data["values"] = [
        [0.0 for _ in range(len(consolidated_data["columns"]))] 
        for _ in range(len(consolidated_data["years"]))
    ]
    
    # Initialize sources tracking only for summed columns
    for year in consolidated_data["years"]:
        year_str = str(year)
        consolidated_data["sources"][year_str] = {}
        for column in sum_columns:  # Only track sources for summed columns
            consolidated_data["sources"][year_str][column] = []
    
    # Apply the consolidation policy
    for year_idx, year in enumerate(consolidated_data["years"]):
        # Process columns that should be summed
        for col_idx, column in enumerate(consolidated_data["columns"]):
            if column in sum_columns:
                # Reset to zero for summed columns
                consolidated_data["values"][year_idx][col_idx] = 0.0
                
                for df_idx, df in enumerate(dfs):
                    if 'Year' in df.columns and column in df.columns:
                        try:
                            year_data = df[df['Year'] == year]
                            if not year_data.empty:
                                value = year_data[column].values[0]
                                if pd.notna(value):  # Skip NaN values
                                    # Add to the sum
                                    consolidated_data["values"][year_idx][col_idx] += value
                                    # Track the source with timestamp
                                    consolidated_data["sources"][str(year)][column].append({
                                        "version": df['cfa_version'].values[0],
                                        "value": float(value),
                                        "timestamp": datetime.now().isoformat()
                                    })
                        except Exception as e:
                            logging.error(f"Error processing {column} for year {year} from version {df['cfa_version'].values[0]}: {e}")
    
    logging.info(f"Consolidation complete. Processed {len(consolidated_data['years'])} years and {len(consolidated_data['columns'])} columns.")
    
    return consolidated_data

def get_cell_source_data(versions: List[str], year, column) -> List[Dict]:
    """Get source data for a specific cell from all versions"""
    sources = []
    
    for version in versions:
        file_path = state.get_file_path(version)
        if file_path and os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                if 'Year' in df.columns and column in df.columns:
                    year_data = df[df['Year'] == year]
                    if not year_data.empty:
                        value = year_data[column].values[0]
                        sources.append({
                            "version": version,
                            "value": float(value),
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    # Log available columns for debugging
                    logging.warning(f"Required columns not found in version {version}. Available: {df.columns.tolist()}")
            except Exception as e:
                logging.error(f"Failed to get cell data from version {version}: {e}")
    
    return sources

# API Routes
@app.route('/')
def index():
    """Render the selection interface"""
    cfa_versions = get_cfa_versions()
    return render_template('index.html', versions=cfa_versions)

@app.route('/api/versions')
def api_versions():
    """Return the list of available CFA versions"""
    cfa_versions = get_cfa_versions()
    return jsonify({"versions": cfa_versions})

@app.route('/api/directory-structure', methods=['GET'])
def directory_structure():
    """Debug endpoint to return the directory structure"""
    structure = {"base_path": BASE_PATH, "exists": os.path.exists(BASE_PATH), "contents": {}}
    
    if os.path.exists(BASE_PATH):
        try:
            for root, dirs, files in os.walk(BASE_PATH, topdown=True, followlinks=True):
                rel_path = os.path.relpath(root, BASE_PATH)
                if rel_path == '.':
                    structure["contents"]["files"] = files
                    structure["contents"]["dirs"] = dirs
                else:
                    path_parts = rel_path.split(os.sep)
                    current = structure["contents"]
                    for part in path_parts:
                        if part not in current:
                            current[part] = {"files": [], "dirs": []}
                        current = current[part]
                    current["files"] = files
                    current["dirs"] = dirs
        except Exception as e:
            structure["error"] = str(e)
    
    return jsonify(structure)

@app.route('/api/select-versions', methods=['POST'])
def select_versions():
    """Update the selected versions based on the request"""
    data = request.get_json()
    selected = data.get('selected', [])
    state.update_selected_versions(selected)
    logging.info(f"Updated selected versions: {selected}")
    return jsonify({"success": True, "selected": selected})

@app.route('/api/process/<version>')
def process_cfa_file(version: str):
    """Process the CFA file for the specified version"""
    logging.info(f"Processing CFA file for version: {version}")
    
    file_path = state.get_file_path(version)
    if not file_path:
        logging.warning(f"File path not found for CFA version: {version}")
        return jsonify({"error": f"CFA file for version {version} not found"})
    
    if not os.path.exists(file_path):
        logging.warning(f"CFA file not found at path: {file_path}")
        return jsonify({"error": f"CFA file not found at: {file_path}"})
    
    try:
        df = pd.read_csv(file_path)
        result = {
            "version": version,
            "filename": os.path.basename(file_path),
            "data": df.fillna("null").to_dict(orient='records')
        }
        logging.info(f"Successfully processed CFA version {version}")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Failed to process CFA version {version}: {e}")
        return jsonify({"error": f"Failed to process CFA version {version}: {str(e)}"})

@app.route('/api/process-selected')
def process_selected():
    """Process all selected CFA files"""
    results = []
    
    for version in state.selected_versions:
        file_path = state.get_file_path(version)
        if file_path and os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                results.append({
                    "version": version,
                    "filename": os.path.basename(file_path),
                    "data": df.fillna("null").to_dict(orient='records')
                })
                logging.info(f"Processed CFA version {version}")
            except Exception as e:
                logging.error(f"Failed to process CFA version {version}: {e}")
                results.append({
                    "version": version,
                    "error": f"Failed to process: {str(e)}"
                })
    
    return jsonify({"results": results})

# Consolidation API endpoints
@app.route('/api/consolidate', methods=['POST'])
def start_consolidation():
    """Start a consolidation job for the specified versions"""
    data = request.get_json()
    versions = data.get('versions', [])
    
    if not versions:
        return jsonify({"error": "No versions specified"}), 400
    
    job_id = state.create_consolidation_job(versions)
    logging.info(f"Created consolidation job {job_id} for versions: {versions}")
    
    # Start processing in the background (for a real app, use a task queue)
    # Here we'll just return the job ID and let the client poll for status
    return jsonify(job_id)

@app.route('/api/consolidate/status/<job_id>')
def get_consolidation_status(job_id: str):
    """Get the status of a consolidation job"""
    job = state.get_consolidation_job(job_id)
    
    if not job:
        return jsonify({"error": f"Job {job_id} not found"}), 404

    # Initialize processing if pending
    if job.status == "pending":
        job.status = "processing"
        job.message = "Starting consolidation..."
        job.progress = 0
    
    # Update progress during processing
    if job.status == "processing" and job.progress < 100:
        versions_count = len(job.versions)
        if versions_count > 0:
            # Calculate progress per version
            progress_per_version = 100 / versions_count
            current_version_index = int(job.progress / progress_per_version)
            
            if current_version_index < versions_count:
                current_version = job.versions[current_version_index]
                
                # Initialize results if not present
                if not job.results:
                    job.results = {
                        "years": [],
                        "columns": [],
                        "values": [],
                        "sources": {}
                    }
                
                # Process current version
                try:
                    # Update progress for current version
                    job.progress = min(100, (current_version_index + 1) * progress_per_version)
                    job.message = f"Processing CFA version {current_version}..."
                    
                    # Process current version
                    new_data = consolidate_data([current_version])
                    
                    # Initialize or merge results
                    if current_version_index == 0:
                        # First version sets the structure
                        job.results = new_data
                    else:
                        # Process each cell independently
                        for year_idx, year in enumerate(job.results["years"]):
                            # Find matching row in new_data
                            if year in new_data["years"]:
                                new_year_idx = new_data["years"].index(year)
                                year_str = str(year)
                                
                                # Process each column
                                for col_idx, column in enumerate(job.results["columns"]):
                                    if column in ['Revenue', 'Operating Expenses']:
                                        # Add value from this version
                                        value = new_data["values"][new_year_idx][col_idx]
                                        job.results["values"][year_idx][col_idx] += value
                                        
                                        # Track source with proper value
                                        source_entry = {
                                            "version": current_version,
                                            "value": float(value),
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        
                                        # Check if source already exists
                                        existing_sources = job.results["sources"][year_str][column]
                                        version_exists = any(s["version"] == current_version for s in existing_sources)
                                        
                                        if not version_exists:
                                            job.results["sources"][year_str][column].append(source_entry)
                    
                    # Complete job when all versions are processed
                    if current_version_index == versions_count - 1:
                        state.complete_job(job_id, job.results)
                        
                except Exception as e:
                    logging.error(f"Error processing version {current_version}: {e}")
                    job.status = "error"
                    job.error = str(e)
    
    return jsonify({
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "error": job.error
    })

@app.route('/api/consolidate/results/<job_id>')
def get_consolidation_results(job_id: str):
    """Get the results of a completed consolidation job"""
    job = state.get_consolidation_job(job_id)
    
    if not job:
        return jsonify({"error": f"Job {job_id} not found"}), 404
    
    if job.status != "complete":
        return jsonify({"error": f"Job {job_id} is not complete yet"}), 400
    
    return jsonify(job.results)

@app.route('/api/cell-details', methods=['POST'])
def get_cell_details():
    """
    Get detailed breakdown of a specific cell, particularly for summed columns
    such as Revenue and Operating Expenses, showing the contribution from each version.
    """
    data = request.get_json()
    year = data.get('year')
    column = data.get('column')
    row_index = data.get('rowIndex')
    col_index = data.get('colIndex')
    
    if not all([year, column]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    # Create a unique key for this cell
    cell_key = f"{year}_{column}_{row_index}_{col_index}"
    
    # Check if we have cached details
    cached_details = state.get_cell_details(cell_key)
    if cached_details:
        return jsonify(cached_details)
    
    # Define columns that have component tracking
    tracked_columns = ['Revenue', 'Operating Expenses']
    
    # Check if this column should be tracked in detail
    if column not in tracked_columns:
        return jsonify({
            "year": year,
            "column": column,
            "totalValue": 0,
            "sources": [],
            "message": f"Detailed tracking not available for {column}"
        })
    
    # Get source data from active consolidation job
    source_data = []
    total_value = 0
    
    # Find the active job for these versions
    active_jobs = [job for job in state.consolidation_jobs.values() 
                  if job.status == "complete" and 
                  set(job.versions) == set(state.selected_versions)]
    
    if active_jobs:
        # Use the most recent job's results
        latest_job = max(active_jobs, key=lambda j: j.start_time)
        consolidated_data = latest_job.results
        
        if str(year) in consolidated_data["sources"] and column in consolidated_data["sources"][str(year)]:
            source_data = consolidated_data["sources"][str(year)][column]
            total_value = sum(source["value"] for source in source_data)
            
            # Add timestamps to sources
            for source in source_data:
                source["timestamp"] = datetime.now().isoformat()
    
    # Calculate percentage contribution for each source
    if total_value > 0:
        for source in source_data:
            source["percentage"] = round((source["value"] / total_value) * 100, 2)
    
    # Sort sources by value (descending)
    source_data = sorted(source_data, key=lambda x: x["value"], reverse=True)
    
    details = {
        "year": year,
        "column": column,
        "totalValue": total_value,
        "sources": source_data,
        "sourceCount": len(source_data)
    }
    
    # Cache the details
    state.add_cell_details(cell_key, details)
    
    return jsonify(details)

# Create templates directory and index.html template
os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), 'templates', 'index.html'), 'w') as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>CFA Version Selection</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .version-list { margin: 20px 0; }
        .version-item { margin: 5px 0; }
        .actions { margin-top: 20px; }
        button { padding: 8px 16px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background: #45a049; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CFA Version Selection</h1>
        <div class="version-list">
            <h2>Available Versions</h2>
            {% if versions %}
                {% for version in versions %}
                <div class="version-item">
                    <input type="checkbox" id="version-{{ version }}" value="{{ version }}">
                    <label for="version-{{ version }}">CFA Version {{ version }}</label>
                </div>
                {% endfor %}
            {% else %}
                <p>No CFA versions found.</p>
            {% endif %}
        </div>
        <div class="actions">
            <button id="selectBtn">Process Selected Versions</button>
        </div>
        <div id="results" class="results"></div>
    </div>
    
    <script>
        document.getElementById('selectBtn').addEventListener('click', function() {
            const selected = [];
            document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
                selected.push(checkbox.value);
            });
            
            fetch('/api/select-versions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ selected: selected })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetch('/api/process-selected')
                    .then(response => response.json())
                    .then(result => {
                        const resultsDiv = document.getElementById('results');
                        resultsDiv.innerHTML = '<h2>Processing Results</h2>';
                        
                        if (result.results.length === 0) {
                            resultsDiv.innerHTML += '<p>No versions selected or processed.</p>';
                        } else {
                            const resultsList = document.createElement('ul');
                            result.results.forEach(item => {
                                const listItem = document.createElement('li');
                                if (item.error) {
                                    listItem.textContent = `Version ${item.version}: ${item.error}`;
                                } else {
                                    listItem.textContent = `Version ${item.version}: Successfully processed ${item.filename} with ${item.data.length} records`;
                                }
                                resultsList.appendChild(listItem);
                            });
                            resultsDiv.appendChild(resultsList);
                        }
                    });
                }
            });
        });
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    cfa_versions = get_cfa_versions()
    logging.info(f"Found {len(cfa_versions)} CFA versions: {', '.join(cfa_versions)}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
