import os
import pandas as pd
import numpy as np
import json
import logging
import re
import sys
from pathlib import Path

# =====================================================================
# SETUP AND CONFIGURATION
# =====================================================================

# Configure backend directory in path
BACKEND_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

# Define property_mapping directly in this file to avoid import issues
property_mapping = {
    "plantLifetimeAmount10": "Plant Lifetime",
    "bECAmount11": "Bare Erected Cost",
    "numberOfUnitsAmount12": "Number of Units",
    "initialSellingPriceAmount13": "Price",
    "totalOperatingCostPercentageAmount14": "Direct Total Operating Cost Percentage as % of Revenue",
    "engineering_Procurement_and_Construction_EPC_Amount15": "Engineering Procurement and Construction as % of BEC",
    "process_contingency_PC_Amount16": "Process Contingency as % of BEC",
    "project_Contingency_PT_BEC_EPC_PCAmount17": "Project Contingency as % of BEC, EPC, PC",
    "use_direct_operating_expensesAmount18": "Use Direct Operating Expenses",
    "use_direct_revenueAmount19": "Use Direct Revenue",
    "depreciationMethodAmount20": "Depreciation Method",
    "loanTypeAmount21": "Loan Type",
    "interestTypeAmount22": "Interest Type",
    "generalInflationRateAmount23": "General Inflation Rate",
    "interestProportionAmount24": "Interest Proportion",
    "principalProportionAmount25": "Principal Proportion",
    "loanPercentageAmount26": "Loan Percentage of TOC",
    "repaymentPercentageOfRevenueAmount27": "Repayment Percentage Of Revenue",
    "numberofconstructionYearsAmount28": "Number of Construction Years",
    "iRRAmount30": "Internal Rate of Return",
    "annualInterestRateAmount31": "Annual Interest Rate",
    "stateTaxRateAmount32": "State Tax Rate",
    "federalTaxRateAmount33": "Federal Tax Rate",
    "rawmaterialAmount34": "Feedstock Cost",
    "laborAmount35": "Labor Cost",
    "utilityAmount36": "Utility Cost",
    "maintenanceAmount37": "Maintenance Cost",
    "insuranceAmount38": "Insurance Cost",
    "vAmount40": "v40",
    "vAmount41": "v41",
    "vAmount42": "v42",
    "vAmount43": "v43",
    "vAmount44": "v44",
    "vAmount45": "v45",
    "vAmount46": "v46",
    "vAmount47": "v47",
    "vAmount48": "v48",
    "vAmount49": "v49",
    "vAmount50": "v50",
    "vAmount51": "v51",
    "vAmount52": "v52",
    "vAmount53": "v53",
    "vAmount54": "v54",
    "vAmount55": "v551",
    "vAmount56": "v56",
    "vAmount57": "v57",
    "vAmount58": "v58",
    "vAmount59": "v59",
    "rAmount60": "r60",
    "rAmount61": "r61",
    "rAmount62": "r62",
    "rAmount63": "r63",
    "rAmount64": "r64",
    "rAmount65": "r65",
    "rAmount66": "r66",
    "rAmount67": "r67",
    "rAmount68": "r68",
    "rAmount69": "r69",
    "rAmount70": "r70",
    "rAmount71": "r71",
    "rAmount72": "r72",
    "rAmount73": "r73",
    "rAmount74": "r74",
    "rAmount75": "r75",
    "rAmount76": "r76",
    "rAmount77": "r77",
    "rAmount78": "r78",
    "rAmount79": "r79",
    "RFAmount80": "Material Revenue",
    "RFAmount81": "Labor Revenue",
    "RFAmount82": "Utility Revenue",
    "RFAmount83": "Maintenance Revenue",
    "RFAmount84": "Insurance Revenue",
}

# Define the base directory for your uploads and batches
ORIGINAL_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
uploads_dir = ORIGINAL_DIR / "Original"

# Initialize logging
LOGS_DIR = Path(BACKEND_DIR) / "Logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
log_file_path = LOGS_DIR / "Aggregated_SubPlots.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.info("AggregatedSubPlots.py logging initialized")

# =====================================================================
# COMMAND LINE ARGUMENT PARSING
# =====================================================================

def parse_versions(versions_str):
    """Convert comma-separated version string to list of integers"""
    return list(map(int, versions_str.split(',')))

def parse_properties(properties_str):
    """Convert comma-separated properties string to list of strings"""
    return properties_str.split(',')

# Check if command-line arguments are provided, otherwise use defaults
if len(sys.argv) > 5:
    selected_versions = parse_versions(sys.argv[1])
    selected_properties = parse_properties(sys.argv[2])
    remarks_state = sys.argv[3]
    customized_features_state = sys.argv[4]
    subplot_selection = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}  # Default to empty dict for subplot selection
    logging.info(f"Selected Subplots: {subplot_selection}")
else:
    logging.warning("No command-line arguments provided, using default values.")
    selected_versions = [1, 2]  # Example versions for testing
    selected_properties = ["Annual_Cash_Flows", "Annual_Revenues"]
    remarks_state = "on"
    customized_features_state = "off"

# Convert string flags to boolean values
include_remarks = True if remarks_state == "on" else False
customized_features = True if customized_features_state == "on" else False

# Create a unique identifier for the combination of versions
versions_identifier = "_".join(map(str, sorted(selected_versions)))

# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================

def preprocess_json_string(json_str):
    """Remove redundant double quotes from JSON string"""
    json_str = re.sub(r'""', '"', json_str)  # Remove redundant double quotes
    return json_str


def format_number(value, prop_id=None):
    """Format numeric values based on property type

    Args:
        value: The numeric value to format
        prop_id: The property ID to determine formatting rules

    Returns:
        Formatted string representation of the value
    """
    # Handle None, NaN, or invalid values
    if value is None:
        return "N/A"

    # Check if value is numeric
    if isinstance(value, (int, float)):
        # Handle special cases like infinity or NaN
        if not np.isfinite(value):
            return "N/A"

        # Properties requiring two decimal places (percentages, rates, prices)
        decimal_properties = [
            "initialSellingPriceAmount13", 
            "interestProportionAmount24",
            "principalProportionAmount25",
            "loanPercentageAmount26",
            "repaymentPercentageOfRevenueAmount27",
            "iRRAmount30",
            "annualInterestRateAmount31",
            "stateTaxRateAmount32",
            "federalTaxRateAmount33",
            "generalInflationRateAmount23",
            "process_contingency_PC_Amount16",
            "project_Contingency_PT_BEC_EPC_PCAmount17",
            "totalOperatingCostPercentageAmount14",
            "engineering_Procurement_and_Construction_EPC_Amount15",
            # Add any other properties that should have decimal places
        ]

        # Properties requiring integer formatting (counts, years, etc.)
        integer_properties = [
            "plantLifetimeAmount10",
            "numberOfUnitsAmount12",
            "numberofconstructionYearsAmount28",
            # Add any other properties that should be formatted as integers
        ]

        try:
            # Check for properties needing two decimal places
            if prop_id in decimal_properties:
                return f"{value:,.2f}"  # Format with commas and two decimal places
            elif prop_id in integer_properties:
                return f"{value:,.0f}"  # Format as integer with commas and no decimal places
            else:
                # Default formatting based on value
                if value.is_integer() or abs(value) >= 1000:
                    return f"{value:,.0f}"  # Use integer format for whole numbers or large values
                else:
                    return f"{value:,.2f}"  # Use decimal format for small non-integer values
        except Exception as e:
            logging.warning(f"Error formatting value {value} for property {prop_id}: {e}")
            return str(value)  # Return string representation as fallback

    # Return as is if not numeric
    return str(value)


# =====================================================================
# DATA EXTRACTION AND PROCESSING FUNCTIONS
# =====================================================================

def extract_selected_properties(config_file, selected_properties, include_remarks):
    """Extract selected properties from U_configurations file

    Args:
        config_file: Path to the configuration file
        selected_properties: List of property IDs to extract
        include_remarks: Whether to include remarks in the output

    Returns:
        Tuple of (version_headers, properties list)
    """
    properties = []
    version_headers = ""  # Initialize version_headers as an empty string

    try:
        with open(config_file, 'r') as file:
            data = file.read()

        lines = data.split('\n')
        should_append = False
        filtered_values_content = ""

        # Extract the filteredValues section from the configuration file
        for line in lines:
            if 'filteredValues' in line:
                should_append = True
            if should_append:
                filtered_values_content += line
                if '}' in line:
                    break

        filtered_values_content = filtered_values_content.replace("'", '"')
        filtered_values_dict = json.loads(filtered_values_content)

        # Process each selected property
        for prop in selected_properties:
            prop_data = next((item for item in filtered_values_dict['filteredValues'] if item.get("id") == prop), None)
            if prop_data:
                value = prop_data.get("value", None)
                remarks = prop_data.get("remarks", "")
                presentable_name = property_mapping.get(prop, prop)
                # Format the value if it's numeric
                formatted_value = format_number(value, prop_id=prop) if value is not None else value

                # Check if the property is bECAmount1 and assign its remarks to version_headers
                if prop == "bECAmount1" and remarks:
                    version_headers = remarks  # Assign remarks to version_headers

                if formatted_value is not None:
                    if include_remarks and remarks:
                        properties.append(f"{presentable_name}: {formatted_value} {remarks}")
                        logging.info(f"Property extracted with remarks: {presentable_name}: {formatted_value} (Remarks: {remarks})")
                    else:
                        properties.append(f"{presentable_name}: {formatted_value}")
                        logging.info(f"Property extracted without remarks: {presentable_name}: {formatted_value}")

    except Exception as e:
        logging.error(f"Error reading configuration file: {str(e)}")

    return version_headers, properties  # Return both version_headers and properties


def sanitize_for_html(text):
    """Sanitize text for safe inclusion in HTML

    Args:
        text: The text to sanitize

    Returns:
        Sanitized text safe for HTML inclusion
    """
    if not isinstance(text, str):
        text = str(text)

    # Replace special characters with HTML entities
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        # Add more replacements if needed
    }

    for char, entity in replacements.items():
        text = text.replace(char, entity)

    return text

def extract_hover_text(filtered_values_str, include_remarks, customized_features):
    """Extract hover text from filtered values string

    Args:
        filtered_values_str: JSON string containing filtered values
        include_remarks: Whether to include remarks in hover text
        customized_features: Whether customized features are enabled

    Returns:
        HTML-formatted hover text or None if customized features are disabled and remarks not included
    """
    # If customized features are disabled but remarks are included, we still want to extract remarks
    # This ensures that unchecked customized with checked remarks gather data from U_configurations
    if not customized_features and not include_remarks:
        return None

    hover_text_lines = []

    # Handle empty or None filtered_values_str
    if not filtered_values_str:
        logging.warning("Empty filtered values string received")
        return ""

    # Preprocess the JSON string to handle formatting issues
    filtered_values_str = preprocess_json_string(filtered_values_str)

    try:
        filtered_values = json.loads(filtered_values_str)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        return f"Error parsing data: {sanitize_for_html(str(e))}"

    # Handle case where filtered_values is not a list
    if not isinstance(filtered_values, list):
        logging.error(f"Filtered values is not a list: {type(filtered_values)}")
        return "Error: Invalid data format"

    # Process each entry in the filtered values
    for entry in filtered_values:
        # Skip if entry is not a dictionary
        if not isinstance(entry, dict):
            logging.warning(f"Skipping non-dictionary entry: {entry}")
            continue

        key = entry.get("id", "Unknown ID")
        value = entry.get("value", "Unknown Value")
        remarks = entry.get("remarks", None)

        # If customized features are disabled, only include entries with remarks if remarks are enabled
        if not customized_features and (not remarks or not include_remarks):
            continue

        # Map the property name and sanitize all values for HTML
        mapped_key = property_mapping.get(key, key)
        safe_key = sanitize_for_html(mapped_key)
        safe_value = sanitize_for_html(value)

        # Format the hover text
        hover_text = f"{safe_key}: {safe_value}"

        # Add remarks if enabled and available
        if include_remarks and remarks:
            safe_remarks = sanitize_for_html(remarks)
            hover_text += f" {safe_remarks}"

        hover_text_lines.append(hover_text)
        logging.info(f"Hover text extracted: {hover_text}")

    # Join all hover text lines with HTML line breaks
    return "<br>".join(hover_text_lines)


def combine_hover_texts(interval_hover_text_CF, interval_hover_text_SP):
    """Combine hover texts from configuration matrix and selected properties

    Args:
        interval_hover_text_CF: Hover text from configuration matrix
        interval_hover_text_SP: Hover text from selected properties

    Returns:
        Combined hover text with HTML formatting
    """
    # Check if interval_hover_text_CF is None and initialize as empty list if so
    if interval_hover_text_CF is None:
        cf_list = []
    else:
        cf_list = interval_hover_text_CF.split("<br>")

    # Check if interval_hover_text_SP is None and initialize as empty list if so
    if interval_hover_text_SP is None:
        sp_list = []
    else:
        sp_list = interval_hover_text_SP  # Assuming this is already a list

    # Prioritize properties by combining lists with properties first
    combined_list = sp_list + cf_list

    # Convert back to the desired format with "<br>" separation
    return "<br>".join(combined_list)



# =====================================================================
# DATA INITIALIZATION AND PROCESSING
# =====================================================================

# Initialize data structures to store metrics and hover text information
metrics_data = {
    'Annual_Cash_Flows': [],          # Cash flow data for each version
    'Annual_Revenues': [],            # Revenue data for each version
    'Annual_Operating_Expenses': [],  # Operating expenses data for each version
    'Loan_Repayment_Terms': [],       # Loan repayment data for each version
    'Depreciation_Schedules': [],     # Depreciation data for each version
    'State_Taxes': [],                # State taxes data for each version
    'Federal_Taxes': [],              # Federal taxes data for each version
    'Cumulative_Cash_Flows': []       # Cumulative cash flow data for each version
}

# Initialize hover text structure with data and active state for each metric
all_hover_texts = {
    'Annual_Cash_Flows': {'data': [], 'active': []},
    'Annual_Revenues': {'data': [], 'active': []},
    'Annual_Operating_Expenses': {'data': [], 'active': []},
    'Loan_Repayment_Terms': {'data': [], 'active': []},
    'Depreciation_Schedules': {'data': [], 'active': []},
    'State_Taxes': {'data': [], 'active': []},
    'Federal_Taxes': {'data': [], 'active': []},
    'Cumulative_Cash_Flows': {'data': [], 'active': []}
}

# Initialize additional data structures
hover_texts = {metric: [] for metric in metrics_data}  # Hover text for each metric
all_version_headers = []  # Headers for each version

# Process each selected version to extract and organize data
for version in selected_versions:
    # Set up paths for the current version
    version_dir = os.path.join(uploads_dir, f'Batch({version})', f'Results({version})')
    batch_folder = os.path.join(uploads_dir, f'Batch({version})')
    results_folder = os.path.join(batch_folder, f'Results({version})')
    config_file = os.path.join(batch_folder, f'ConfigurationPlotSpec({version})', f'U_configurations({version}).py')

    # Extract properties from configuration file
    version_headers, interval_hover_text_SP = extract_selected_properties(config_file, selected_properties, include_remarks)
    all_version_headers.append(version_headers)
    logging.info(f"Version headers: {version_headers}")

    # Read CFA table for financial data
    CFA_table_path = os.path.join(version_dir, f"CFA({version}).csv")
    if not os.path.exists(CFA_table_path):
        logging.error(f"CFA table not found for version {version}")
        continue

    CFA_table = pd.read_csv(CFA_table_path)

    # Extract financial data for each metric from the CFA table
    metrics_data['Annual_Cash_Flows'].append(CFA_table['After-Tax Cash Flow'].tolist())
    logging.info(f"metrics_data_aggregation {metrics_data['Annual_Cash_Flows']}")
    metrics_data['Annual_Revenues'].append(CFA_table['Revenue'].tolist())
    metrics_data['Annual_Operating_Expenses'].append(CFA_table['Operating Expenses'].tolist())
    metrics_data['Loan_Repayment_Terms'].append(CFA_table.get('Loan Repayment', pd.Series(np.zeros(len(CFA_table)))).tolist())
    metrics_data['Depreciation_Schedules'].append(CFA_table['Depreciation'].tolist())
    metrics_data['State_Taxes'].append(CFA_table['State Taxes'].tolist())
    metrics_data['Federal_Taxes'].append(CFA_table['Federal Taxes'].tolist())
    metrics_data['Cumulative_Cash_Flows'].append(CFA_table['Cumulative Cash Flow'].tolist())

    # Process configuration matrix for hover text
    # Use General_Configuration_Matrix for better year-by-year granularity
    config_matrix_file = os.path.join(version_dir, f"General_Configuration_Matrix({version}).csv")
    config_matrix_df = pd.read_csv(config_matrix_file)

    # Log the configuration matrix structure for debugging
    logging.info(f"Configuration matrix has {len(config_matrix_df)} rows")
    if not config_matrix_df.empty:
        logging.info(f"First row: start={config_matrix_df.iloc[0]['start']}, end={config_matrix_df.iloc[0]['end']}")

    # Initialize hover text structures for this version
    hover_text_for_version = {metric: [] for metric in metrics_data}
    hover_texts_for_version = {metric: [] for metric in metrics_data}

    # Process each row in the configuration matrix (each row represents a time interval)
    for _, row in config_matrix_df.iterrows():
        start, end = row['start'], row['end']
        filtered_values = row['filtered_values']

        # Extract hover text from filtered values
        interval_hover_text_CF = extract_hover_text(filtered_values, include_remarks, customized_features)

        # Combine with selected properties, prioritizing properties
        interval_hover_text = combine_hover_texts(interval_hover_text_CF, interval_hover_text_SP)

        # For each year in this interval, add the hover text to all metrics
        # This ensures proper disbursement of hover texts into specific time bins
        for i in range(int(start), int(end) + 1):
            for metric in metrics_data:
                # Add to both hover text structures
                hover_text_for_version[metric].append(interval_hover_text)
                hover_texts_for_version[metric].append(interval_hover_text)

    # Store hover text data and set default inactive state
    for metric in metrics_data:
        # Store in hover_texts for backward compatibility
        hover_texts[metric].append(hover_texts_for_version[metric])

        # Store in all_hover_texts for the visualization
        all_hover_texts[metric]['data'].append(hover_texts_for_version[metric])
        logging.info(f"all_hover_texts {metric} has {len(hover_texts_for_version[metric])} entries")
        all_hover_texts[metric]['active'].append(False)

    logging.info(f"metrics_data_aggregation {metrics_data['Annual_Cash_Flows']}")

# Define metric abbreviations for display and reference
metric_abbreviations = {
    'Annual_Cash_Flows': 'ACF',
    'Annual_Revenues': 'ARV',
    'Annual_Operating_Expenses': 'AOE',
    'Loan_Repayment_Terms': 'LRT',
    'Depreciation_Schedules': 'DSC',
    'State_Taxes': 'STX',
    'Federal_Taxes': 'FTX',
    'Cumulative_Cash_Flows': 'CCF'
}

# List of metrics to match against 'V1' to 'V8'
metrics_list = list(metric_abbreviations.keys())


# =====================================================================
# HTML GENERATION AND FILE SAVING
# =====================================================================

def sanitize_filename(filename):
    """Sanitize a filename to ensure it's valid across platforms

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename safe for use in file paths
    """
    # Replace invalid filename characters with underscores
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', str(filename))

    # Ensure the filename isn't too long (max 255 chars is safe for most filesystems)
    if len(sanitized) > 255:
        # Keep extension if present
        name_parts = sanitized.rsplit('.', 1)
        if len(name_parts) > 1:
            # Truncate the name part and keep the extension
            sanitized = name_parts[0][:250] + '.' + name_parts[1]
        else:
            # No extension, just truncate
            sanitized = sanitized[:255]

    return sanitized

def save_html_content(html_content, metric_name, version, versions_identifier):
    """Save the HTML content in both Results(versions_identifier) and Results(version) folders.

    Args:
        html_content: The HTML content to save
        metric_name: The name of the metric (used in file naming)
        version: The version number
        versions_identifier: String identifier for the combination of versions

    Returns:
        bool: True if successful, False if any errors occurred
    """
    success = True

    # Sanitize inputs to prevent path traversal or invalid filenames
    safe_metric_name = sanitize_filename(metric_name)
    safe_version = sanitize_filename(version)
    safe_versions_identifier = sanitize_filename(versions_identifier)

    try:
        # 1. Individual version folder: Results(version)
        version_dir = os.path.join(
            uploads_dir, f'Batch({safe_version})', f'Results({safe_version})', 
            f'v{safe_versions_identifier}_{safe_metric_name}_Plot'
        )

        # Create directory with error handling
        try:
            os.makedirs(version_dir, exist_ok=True)
        except OSError as e:
            logging.error(f"Error creating directory {version_dir}: {e}")
            success = False

        if success:
            version_file = os.path.join(version_dir, f'{safe_metric_name}_Plot.html')

            # Write file with error handling
            try:
                with open(version_file, 'w', encoding='utf-8') as file:
                    file.write(html_content)
                logging.info(f"HTML file saved in version folder at: {version_file}")
            except IOError as e:
                logging.error(f"Error writing to file {version_file}: {e}")
                success = False
    except Exception as e:
        logging.error(f"Unexpected error saving to version folder: {e}")
        success = False

    try:
        # 2. Cumulative version folder
        cumulative_version_dir = os.path.join(
            uploads_dir, f'Batch({safe_version})', f'Results({safe_version})', 
            f'v{safe_versions_identifier}_Cumulative_Plot'
        )

        # Create directory with error handling
        try:
            os.makedirs(cumulative_version_dir, exist_ok=True)
        except OSError as e:
            logging.error(f"Error creating directory {cumulative_version_dir}: {e}")
            success = False

        if success:
            cumulative_version_file = os.path.join(cumulative_version_dir, f'{safe_metric_name}_Cumulative_Plot.html')

            # Write file with error handling
            try:
                with open(cumulative_version_file, 'w', encoding='utf-8') as file:
                    file.write(html_content)
                logging.info(f"HTML file saved in cumulative folder at: {cumulative_version_file}")
            except IOError as e:
                logging.error(f"Error writing to file {cumulative_version_file}: {e}")
                success = False
    except Exception as e:
        logging.error(f"Unexpected error saving to cumulative folder: {e}")
        success = False

    return success

# Reference for possible version headers (commented out)
# version_headers = ["Standard Version", "Standard Fully Automated", "Scaled Version", "Scaled Fully Automated",
#                   "Wood Pellet Version", "Coir Pith Version", "Rice Husk Version", "RIL 1 (Natural Wood) Version", 
#                   "RIL 2 (Wood Waste) Version", "Agrol Version", "Verge Grass Version", "Paper Residue Sludge Version"]

# Process selected visualizations based on user selection
for key, status in subplot_selection.items():
    # Only process metrics that are turned on and not the special case SP9
    if status == 'on' and key != 'SP9':  # Handle individual metrics
        # Convert SP1-SP8 to corresponding metric index (0-7)
        metric_idx = int(key[2:]) - 1
        metric_name = list(metrics_data.keys())[metric_idx]

        # Create trace names by combining metric name with version headers
        traces_names = [f"{metric_name.replace('_', ' ')} - {all_version_headers[i]}"
                        for i in range(len(selected_versions))]
        logging.info(f"Traces names: {traces_names}")

        # Define colors for each version to ensure consistent coloring across plots
        version_colors = [
            "#ff0000",  # Red
            "#0000ff",  # Blue
            "#ff6e31",  # Orange
            "#00a600",  # Chartreuse Green
            "#12c9ca",  # Cyan
            "#8b00ff",  # Indigo
            "#9400D3",  # Dark Violet
            "#f215a5",  # Violet/Magenta
            "#ff1493"   # Deep Pink
        ]
        # Generate the HTML content for the metric with embedded JavaScript for interactive visualization
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Financial Analysis - {metric_name.replace('_', ' ').title()}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
            .plot-container {{
    width: 50%;
    margin: 0 auto;
}}
.button-grid {{
    width: 50%;
    display: flex;
    justify-content: space-between;
    gap: 15px;
    margin: 15px auto;
    padding: 0 5px;
}}
.button-grid button {{
    flex: 1;
    padding: 8px 12px;
    font-size: 14px;
    white-space: nowrap;
    border: none;
    border-radius: 4px;
    background-color: #f8f9fa;
    color: #495057;
    transition: all 0.2s ease-in-out;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    cursor: pointer;
}}
.button-grid button:hover {{
    background-color: #e9ecef;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}
.button-grid button:active {{
    transform: translateY(1px);
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}}
.button-grid button:disabled {{
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}}
#plot {{
    width: 100%;
    height: 500px;
}}
            </style>
        </head>
        <body>
        <div class="plot-container">
            <div id="plot"></div>
            <div class="button-grid">
                <button id="fix-button" disabled>Press 1 to fix hover</button>
                <button id="release-button" disabled>Press 2 to release hover</button>
                <button id="global-reset-button">Global Reset</button>
            </div>
</div>
            <script type="text/javascript">
                const metric = '{metric_name}';
                const selected_versions = {json.dumps(selected_versions)};
                const metrics_data = {json.dumps(metrics_data)};
                const hover_texts = {json.dumps(all_hover_texts)};
                const traces_names = {json.dumps(traces_names)};
                const version_colors = {json.dumps(version_colors)};
                let annotations = [];
                let hoverTextStatus = {{}};
                let currentHoverPoint = null;
                let traces = [];

                const marker_styles = [
                    {{ symbol: "circle", size: 6 }},
                    {{ symbol: "square", size: 6 }},
                    {{ symbol: "diamond", size: 6 }},
                    {{ symbol: "cross", size: 6 }},
                    {{ symbol: "triangle-up", size: 6 }},
                    {{ symbol: "triangle-down", size: 6 }},
                    {{ symbol: "pentagon", size: 6 }},
                    {{ symbol: "hexagon", size: 6 }}
                ];

                for (let vIdx = 0; vIdx < selected_versions.length; vIdx++) {{
                    const version = selected_versions[vIdx];
                    traces.push({{
                        x: Array.from({{ length: metrics_data[metric][vIdx].length }}, (_, i) => i + 1),
                        y: metrics_data[metric][vIdx],
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: traces_names[vIdx],
                        text: hover_texts[metric]['data'][vIdx],
                        hoverinfo: 'text',
                        marker: {{ ...marker_styles[vIdx % marker_styles.length], color: version_colors[vIdx % version_colors.length] }}
                    }});
                }}

                const layout = {{
                    grid: {{ rows: 1, columns: 1, pattern: 'independent' }},
                    hovermode: 'closest',
                    title: `{metric_name.replace('_', ' ').title()}`,
                    annotations: [],
                }};

                Plotly.newPlot('plot', traces, layout);

                document.getElementById('fix-button').disabled = false;
                document.getElementById('release-button').disabled = false;

                document.getElementById('plot').on('plotly_hover', function(eventData) {{
                    currentHoverPoint = eventData.points[0];
                }});

                function toggleHoverText(fix) {{
                    if (currentHoverPoint !== null) {{
                        const pointKey = `${{currentHoverPoint.curveNumber}}-${{currentHoverPoint.pointIndex}}`;
                        const color = version_colors[currentHoverPoint.curveNumber % version_colors.length];  // Get color for version

                        if (fix) {{
                            hoverTextStatus[pointKey] = true;
                            const hoverAnnotation = {{
                                x: currentHoverPoint.x,
                                y: currentHoverPoint.y,
                                text: `<span style="color:${{color}};">${{currentHoverPoint.text}}</span>`,  // Apply color to text
                                showarrow: true,
                                arrowhead: 5,
                                ax: 0,
                                ay: -70,
                                axref: 'pixel',
                                ayref: 'pixel'
                            }};
                            annotations.push(hoverAnnotation);
                            Plotly.relayout('plot', {{ annotations }});
                        }} else {{
                            hoverTextStatus[pointKey] = false;
                            annotations = annotations.filter(ann => ann.x !== currentHoverPoint.x || ann.y !== currentHoverPoint.y);
                            Plotly.relayout('plot', {{ annotations }});
                        }}
                    }}
                }}

                document.addEventListener('keydown', (event) => {{
                    if (event.key === '1') {{
                        toggleHoverText(true);
                    }} else if (event.key === '2') {{
                        toggleHoverText(false);
                    }}
                }});

                function globalReset() {{
                    hoverTextStatus = {{}};
                    annotations = [];
                    Plotly.relayout('plot', {{ annotations: [] }});
                }}

                document.getElementById('global-reset-button').addEventListener('click', globalReset);
            </script>
        </body>
        </html>
        """

        # Save the HTML content in both places
        save_success = True
        for version in selected_versions:
            # Call save_html_content and track if any save operation fails
            if not save_html_content(html_content, metric_name, version, versions_identifier):
                save_success = False
                logging.error(f"Failed to save HTML content for metric {metric_name}, version {version}")

        if not save_success:
            logging.warning(f"Some HTML content could not be saved for metric {metric_name}")
        else:
            logging.info(f"All HTML content successfully saved for metric {metric_name}")
