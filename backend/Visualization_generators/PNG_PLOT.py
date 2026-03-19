import sys 
import numpy as np
import pandas as pd
import os
import shutil  # For removing directories
import json
import logging
import matplotlib.pyplot as plt
from pathlib import Path

# Configure backend directory in path
BACKEND_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

# Base paths
PUBLIC_DIR = BACKEND_DIR.parent / 'Original'
# Try to import property_mapping, use empty dict if not available
try:
    from Utility_functions.common_utils import property_mapping
except ImportError:
    logging.warning("Could not import property_mapping, using empty mapping")
    property_mapping = {}

# Rest of your PNG_PLOT.py code continues...
from matplotlib import font_manager
import matplotlib.ticker as ticker

# Configure logging to use console instead of file to avoid Git stashing issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logging.info("Script started.")
logger = logging.getLogger(__name__)

# Create log directory for future use if needed, but don't log to file
LOG_DIR = BACKEND_DIR / "Logs"
LOG_DIR.mkdir(exist_ok=True)

# Ensure base directory exists
os.makedirs(PUBLIC_DIR, exist_ok=True)
logging.info(f"Ensured base directory exists at {PUBLIC_DIR}")

# Define paths to save aggregated data and legend information
output_data_dir = os.path.join(PUBLIC_DIR, "aggregated_data")
os.makedirs(output_data_dir, exist_ok=True)
logging.info(f"Ensured aggregated data directory exists at {output_data_dir}")

# Save datasets as CSV files for use in R
def save_to_csv(data, filename):
    filepath = os.path.join(output_data_dir, filename)
    pd.DataFrame(data).to_csv(filepath, index=False)
    return filepath
# Parse versions and properties
def parse_versions(versions_str):
    try:
        if not versions_str or versions_str.strip() == '':
            logging.warning("Empty versions string, using default version [1]")
            return [1]
        try:
            versions = [int(v.strip()) for v in versions_str.split(',') if v.strip()]
            if not versions:
                logging.warning("No valid versions found, using default version [1]")
                return [1]
            return versions
        except ValueError as e:
            logging.error(f"Invalid version number: {str(e)}, using default version [1]")
            return [1]
    except Exception as e:
        logging.error(f"Error parsing versions: {str(e)}, using default version [1]")
        return [1]

def parse_properties(properties_str):
    try:
        if not properties_str or properties_str.strip() == '':
            logging.info("No properties selected")
            return []
        try:
            properties = [p.strip() for p in properties_str.split(',') if p.strip()]
            if not properties:
                logging.info("No valid properties found")
                return []
            return properties
        except ValueError as e:
            logging.error(f"Invalid property format: {str(e)}")
            return []
    except Exception as e:
        logging.error(f"Error parsing properties: {str(e)}")
        return []

try:
    if len(sys.argv) > 5:
        selected_versions = parse_versions(sys.argv[1])
        selected_properties = parse_properties(sys.argv[2])
        remarks_state = sys.argv[3] if sys.argv[3] in ["on", "off"] else "on"
        customized_features_state = sys.argv[4] if sys.argv[4] in ["on", "off"] else "off"
        try:
            sensitivity_params = json.loads(sys.argv[5])  # Parse sensitivity parameters
        except Exception as e:
            logging.error(f"Error parsing sensitivity parameters: {str(e)}")
            sensitivity_params = {}
    else:
        logging.warning("No command-line arguments provided, using default values.")
        selected_versions = [1]
        selected_properties = []
        remarks_state = "on"
        customized_features_state = "off"
        sensitivity_params = {}
except Exception as e:
    logging.error(f"Error processing command line arguments: {str(e)}, using default values")
    selected_versions = [1]
    selected_properties = []
    remarks_state = "on"
    customized_features_state = "off"
    sensitivity_params = {}

# Log received sensitivity parameters
if sensitivity_params:
    logging.info("Processing sensitivity analysis configuration:")
    enabled_params = {k: v for k, v in sensitivity_params.items() if v.get('enabled', False)}
    for param_id, config in enabled_params.items():
        logging.info(f"""
Sensitivity Parameter {param_id}:
Mode: {config['mode']}
Values Range: {config['values']}
Comparison: {config['compareToKey']} ({config['comparisonType']})
Visualization Options: 
- Waterfall Chart: {config['waterfall']}
- Bar Chart: {config['bar']}
- Point Plot: {config['point']}
""".strip())

logging.info(f"Selected versions: {selected_versions}")
logging.info(f"Selected properties: {selected_properties}")
logging.info(f"Include baseline remarks: {remarks_state}")
logging.info(f"Include customized features: {customized_features_state}")
# User preferences as boolean flags
include_in_remarks = True if remarks_state == "on" else False
include_customized_features = True if customized_features_state == "on" else False

# Generate a unique identifier based on the selected versions
versions_identifier = "_".join(map(str, sorted(selected_versions)))

# Function to extract customized features from Filtered_Value_Intervals CSV
def extract_customized_features(filtered_value_intervals_file, include_customized_features, include_in_remarks):
    customized_features = []
    if not include_customized_features:
        return customized_features

    if not os.path.exists(filtered_value_intervals_file):
        logging.warning(f"Filtered_Value_Intervals file does not exist: {filtered_value_intervals_file}")
        return customized_features

    try:
        # Read and validate CSV file
        try:
            filtered_value_intervals_df = pd.read_csv(filtered_value_intervals_file)
            required_columns = ['ID', 'Start', 'End', 'Value', 'Remarks']
            missing_columns = [col for col in required_columns if col not in filtered_value_intervals_df.columns]
            if missing_columns:
                raise ValueError(f"Missing columns in Filtered_Value_Intervals file: {missing_columns}")
        except Exception as e:
            logging.error(f"Error reading Filtered_Value_Intervals file: {str(e)}")
            # Create new file with default columns
            filtered_value_intervals_df = pd.DataFrame(columns=['ID', 'Start', 'End', 'Value', 'Remarks'])
            filtered_value_intervals_df.to_csv(filtered_value_intervals_file, index=False)
            return customized_features

        # Process each row
        for _, row in filtered_value_intervals_df.iterrows():
            try:
                prop_id = row['ID'] if pd.notna(row['ID']) else ""
                start = row['Start'] if pd.notna(row['Start']) else ""
                end = row['End'] if pd.notna(row['End']) else ""
                value = row['Value'] if pd.notna(row['Value']) else ""
                remarks = row['Remarks'] if pd.notna(row['Remarks']) else ""

                if prop_id:  # If ID exists
                    if include_in_remarks and remarks:
                        customized_features.append(f"{prop_id}: {value}, [{start}-{end}], Remarks: {remarks}")
                    else:
                        customized_features.append(f"{prop_id}: {value}, [{start}-{end}]")
                else:  # If ID is missing
                    if remarks:  # Only include remarks if they exist
                        customized_features.append(f"{remarks}")
            except Exception as e:
                logging.error(f"Error processing row in Filtered_Value_Intervals file: {str(e)}")
                continue

    except Exception as e:
        logging.error(f"Error processing Filtered_Value_Intervals file: {str(e)}")

    return customized_features



# Initialize dictionaries to store version statistics with row numbers as keys
custom_version_stat = {}
legend_cluster_version_stat = {}

# Calculate cluster_size (minimum 1 if no properties selected)
cluster_size = max(1, len(selected_properties))

for i, selected_version in enumerate(selected_versions, start=1):
    batch_folder = os.path.join(PUBLIC_DIR, f'Batch({selected_version})')
    results_folder = os.path.join(batch_folder, f'Results({selected_version})')

    # Create all required directories first
    try:
        # Create batch folder
        os.makedirs(batch_folder, exist_ok=True)
        logging.info(f"Ensured Batch folder exists for version {selected_version}")

        # Create results folder
        os.makedirs(results_folder, exist_ok=True)
        logging.info(f"Ensured Results folder exists for version {selected_version}")

        # Create ConfigurationPlotSpec directory
        config_dir = os.path.join(batch_folder, f'ConfigurationPlotSpec({selected_version})')
        os.makedirs(config_dir, exist_ok=True)
        logging.info(f"Ensured ConfigurationPlotSpec directory exists for version {selected_version}")

        # Create U_configurations file with default content
        config_file = os.path.join(config_dir, f'U_configurations({selected_version}).py')
        if not os.path.exists(config_file):
            with open(config_file, 'w') as f:
                f.write('filteredValues = []')
            logging.info(f"Created default U_configurations file for version {selected_version}")
    except Exception as e:
        logging.error(f"Error creating directories or files: {str(e)}")
        # Instead of returning, continue with default values
        logging.info("Continuing with default values")

    # Create empty Filtered_Value_Intervals file if it doesn't exist
    filtered_value_intervals_file = os.path.join(results_folder, f'Filtered_Value_Intervals({selected_version}).csv')
    if not os.path.exists(filtered_value_intervals_file):
        pd.DataFrame(columns=['ID', 'Start', 'End', 'Value', 'Remarks']).to_csv(filtered_value_intervals_file, index=False)
        logging.info(f"Created empty Filtered_Value_Intervals file for version {selected_version}")

    # Create default CFA file if it doesn't exist
    cfa_file = os.path.join(results_folder, f"CFA({selected_version}).csv")
    if not os.path.exists(cfa_file):
        default_data = {
            'After-Tax Cash Flow': [0] * 20,
            'Revenue': [0] * 20,
            'Operating Expenses': [0] * 20,
            'Depreciation': [0] * 20,
            'State Taxes': [0] * 20,
            'Federal Taxes': [0] * 20,
            'Cumulative Cash Flow': [0] * 20
        }
        pd.DataFrame(default_data).to_csv(cfa_file, index=False)
        logging.info(f"Created default CFA file for version {selected_version}")

    # Extract customized features
    customized_features = extract_customized_features(filtered_value_intervals_file, include_customized_features, include_in_remarks)
    
    # Calculate custom_count with cluster_size added
    custom_count_with_cluster = len(customized_features) + cluster_size

    # Store the version and updated custom count under the row number key in custom_version_stat
    custom_version_stat[i] = {
        "version": selected_version,
        "custom_count": custom_count_with_cluster
    }

    # Store the row number, version, and custom count in legend_cluster_version_stat
    legend_cluster_version_stat[i] = {
        "version": selected_version,
        "custom_count": custom_count_with_cluster
    }



logging.info(f"legend_cluster_version_stat {legend_cluster_version_stat}")




# Ensure directory exists or clear old files
def prepare_version_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
      
    else:
        # Clean specific files, not the entire directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
               
def format_number(value, prop_id=None):
    if isinstance(value, (int, float)):
        # Properties requiring two decimal places
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
        ]
        
        # Properties requiring integer formatting
        integer_properties = [
            
        ]

        # Check for properties needing two decimal places
        if prop_id in decimal_properties:
            return f"{value:,.2f}"  # Format with commas and two decimal places
        elif prop_id in integer_properties:
            return f"{value:,.0f}"  # Format as integer with commas and no decimal places
        else:
            return f"{value:,.0f}"  # Default integer formatting if property not specified
    return value  # Return as is if not numeric


# Function to extract selected properties from U_configurations
def extract_selected_properties(config_file, selected_properties, include_in_remarks):
    properties = []
    version_headers = []  # Initialize version_headers array
    
    if not os.path.exists(config_file):
        logging.warning(f"Configuration file does not exist: {config_file}")
        return version_headers, properties

    try:
        # Read the file content
        with open(config_file, 'r') as file:
            content = file.read().strip()
            
        # Validate content format
        if not content or content == 'filteredValues = []':
            logging.info(f"Empty or default configuration in {config_file}")
            return version_headers, properties

        # Create a new namespace to execute the Python file
        namespace = {}
        try:
            exec(content, namespace)
        except Exception as e:
            logging.error(f"Error executing configuration file: {str(e)}")
            # Reset file with default content
            with open(config_file, 'w') as f:
                f.write('filteredValues = []')
            return version_headers, properties
        
        # Get filteredValues from the namespace
        filtered_values = namespace.get('filteredValues', [])
        if not isinstance(filtered_values, list):
            logging.error(f"Invalid filteredValues format in {config_file}")
            return version_headers, properties

        for prop in selected_properties:
            try:
                prop_data = next((item for item in filtered_values if item.get("id") == prop), None)
                if prop_data:
                    value = prop_data.get("value", None)
                    remarks = prop_data.get("remarks", "")
                    presentable_name = property_mapping.get(prop, prop)
                    formatted_value = format_number(value, prop_id=prop) if value is not None else value

                    if prop == "bECAmount1" and remarks:
                        # Special handling for bECAmount1
                        version_headers.append(remarks)  # Assign remarks to version_headers
                        if formatted_value is not None:
                            properties.append(f"{presentable_name}: {formatted_value}")  # Exclude remarks in properties
                    elif formatted_value is not None:
                        # For all other properties
                        if include_in_remarks and remarks:
                            properties.append(f"{presentable_name}: {formatted_value} {remarks}")
                            logging.info(f"Property extracted with remarks: {presentable_name}: {formatted_value} (Remarks: {remarks})")
                        else:
                            properties.append(f"{presentable_name}: {formatted_value}")
                            logging.info(f"Property extracted without remarks: {presentable_name}: {formatted_value}")
            except Exception as e:
                logging.error(f"Error processing property {prop}: {str(e)}")
                continue

    except Exception as e:
        logging.error(f"Error reading configuration file: {str(e)}")

    return version_headers, properties  # Return both version_headers and properties



# Initialize lists to store aggregated data
all_annual_cash_flows_net = []
all_annual_revenues = []
all_annual_operating_expenses = []
all_depreciation_schedules = []
all_state_taxes = []
all_federal_taxes = []
all_cumulative_cash_flows = []

# Initialize the cumulative legend items list
cumulative_legend_items = []


# Iterate over each selected version to aggregate data
for i, selected_version in enumerate(selected_versions):
    batch_folder = os.path.join(PUBLIC_DIR, f'Batch({selected_version})')
    results_folder = os.path.join(batch_folder, f'Results({selected_version})')

    # Create results folder if it doesn't exist
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
        logging.info(f"Created Results folder for version {selected_version}")

    try:
        # Prepare version-specific plot directory
        version_specific_dir = os.path.join(results_folder, f'{versions_identifier}_AnnotatedStaticPlots')
        if os.path.exists(version_specific_dir):
            shutil.rmtree(version_specific_dir)
            
        os.makedirs(version_specific_dir, exist_ok=True)
        logging.info(f"Created version-specific plot directory: {version_specific_dir}")
    except Exception as e:
        logging.error(f"Error creating version-specific plot directory: {str(e)}")
        # Create in results folder as fallback
        version_specific_dir = results_folder
        logging.info(f"Using results folder as fallback: {version_specific_dir}")

    # Create or read CFA file
    cfa_file = os.path.join(results_folder, f"CFA({selected_version}).csv")
    try:
        if not os.path.exists(cfa_file):
            # Create default CFA file with zeros
            default_data = {
                'After-Tax Cash Flow': [0] * 20,
                'Revenue': [0] * 20,
                'Operating Expenses': [0] * 20,
                'Depreciation': [0] * 20,
                'State Taxes': [0] * 20,
                'Federal Taxes': [0] * 20,
                'Cumulative Cash Flow': [0] * 20
            }
            summary_table = pd.DataFrame(default_data)
            summary_table.to_csv(cfa_file, index=False)
            logging.info(f"Created default CFA file for version {selected_version}")
        else:
            try:
                summary_table = pd.read_csv(cfa_file)
                # Validate required columns
                required_columns = [
                    'After-Tax Cash Flow', 'Revenue', 'Operating Expenses',
                    'Depreciation', 'State Taxes', 'Federal Taxes', 'Cumulative Cash Flow'
                ]
                missing_columns = [col for col in required_columns if col not in summary_table.columns]
                if missing_columns:
                    raise ValueError(f"Missing columns in CFA file: {missing_columns}")
            except Exception as e:
                logging.error(f"Error reading CFA file {cfa_file}: {str(e)}")
                # Create new file with default data
                default_data = {
                    'After-Tax Cash Flow': [0] * 20,
                    'Revenue': [0] * 20,
                    'Operating Expenses': [0] * 20,
                    'Depreciation': [0] * 20,
                    'State Taxes': [0] * 20,
                    'Federal Taxes': [0] * 20,
                    'Cumulative Cash Flow': [0] * 20
                }
                summary_table = pd.DataFrame(default_data)
                summary_table.to_csv(cfa_file, index=False)
                logging.info(f"Created new default CFA file for version {selected_version} due to error")

        # Log data being loaded
        annual_cash_flow_net = summary_table['After-Tax Cash Flow'].values
        annual_revenue = summary_table['Revenue'].values
        annual_operating_expenses = summary_table['Operating Expenses'].values
        depreciation_schedule = summary_table['Depreciation'].values
        state_taxes = summary_table['State Taxes'].values
        federal_taxes = summary_table['Federal Taxes'].values
        cumulative_cash_flow = summary_table['Cumulative Cash Flow'].values
    except Exception as e:
        logging.error(f"Error processing CFA file: {str(e)}")
        # Return empty arrays if there's an error
        annual_cash_flow_net = np.array([])
        annual_revenue = np.array([])
        annual_operating_expenses = np.array([])
        depreciation_schedule = np.array([])
        state_taxes = np.array([])
        federal_taxes = np.array([])
        cumulative_cash_flow = np.array([])

    all_annual_cash_flows_net.append(annual_cash_flow_net)
    all_annual_revenues.append(annual_revenue)
    all_annual_operating_expenses.append(annual_operating_expenses)
    all_depreciation_schedules.append(depreciation_schedule)
    all_state_taxes.append(state_taxes)
    all_federal_taxes.append(federal_taxes)
    all_cumulative_cash_flows.append(cumulative_cash_flow)

    

    # Collect properties and customized features for this version
    config_file = os.path.join(batch_folder, f'ConfigurationPlotSpec({selected_version})', f'U_configurations({selected_version}).py')
    version_headers, properties = extract_selected_properties(config_file, selected_properties, include_in_remarks)

    filtered_value_intervals_file = os.path.join(results_folder, f'Filtered_Value_Intervals({selected_version}).csv')
    customized_features = extract_customized_features(filtered_value_intervals_file, include_customized_features, include_in_remarks)



    try:
        # Get header from version_headers if available
        header = version_headers[0] if version_headers and len(version_headers) > 0 else None

        # Initialize version_legend with the header or default
        version_legend = ["Version " + str(selected_version)]
        if header:
            version_legend = [header]
    except Exception as e:
        logging.error(f"Error processing version headers: {str(e)}")
        version_legend = ["Version " + str(selected_version)]
    
    # Add properties and features if they exist
    if properties:
        version_legend.extend(properties)
    if customized_features:
        version_legend.extend(customized_features)

    # Log the version-specific legend before adding to cumulative
    logger.info(f"Version-specific legend: {version_legend}")

    # Add to cumulative legend, ensuring version-specific legend is stored
    cumulative_legend_items.append(version_legend)
    logger.info(f"Cumulative legend: {cumulative_legend_items}")
  

# Example list of fonts to choose from
    available_fonts = ['Arial', 'Verdana', 'Helvetica', 'Times New Roman', 'Courier New', 'Georgia']

    # You can select the font of your choice from the list
    chosen_title_font = 'Georgia'
    chosen_axis_font = 'Georgia'
    chosen_legend_font = 'Georgia'
    legend_item_spacing = 1  # Space between legend items
# Colors and markers for the plots
def get_colors_and_markers(num_versions):
    """Get colors and markers for plotting."""
    if num_versions == 0:
        return [], []
    colors = plt.cm.tab20(np.linspace(0, 1, max(1, num_versions)))
    markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', 'h', '*']
    return colors, markers[:num_versions]

# Initialize colors and markers
colors, markers = get_colors_and_markers(len(selected_versions))

# Plot function with cumulative legend and save for each version
def plot_aggregated(datasets, title, xlabel, ylabel, filename, title_font=chosen_title_font, axis_font=chosen_axis_font, legend_font=chosen_legend_font, title_size=18, label_size=14):
    # Check if we have any non-empty datasets
    if not datasets or not any(len(dataset) > 0 for dataset in datasets):
        logging.warning(f"No data available for {title}")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot only non-empty datasets and apply styling
    has_data = False
    for i, dataset in enumerate(datasets):
        if len(dataset) > 0:
            # Get color and marker safely
            color = colors[i] if i < len(colors) else 'blue'
            marker = markers[i % len(markers)] if markers else 'o'
            
            ax.plot(dataset, color=color, marker=marker, linestyle='-', linewidth=1, markersize=5)
            has_data = True
        else:
            logging.warning(f"Dataset {i} for {title} is empty.")

    # Only apply styling if we have data
    if has_data:
        # Apply title and labels with custom fonts
        ax.set_title(title, fontsize=title_size, fontname=title_font, weight='bold', loc='center', pad=20)
        ax.set_xlabel(xlabel, fontsize=label_size, fontname=axis_font)
        ax.set_ylabel(ylabel, fontsize=label_size, fontname=axis_font)

        # Set X-ticks with customized intervals and labels
        if datasets and len(datasets) > 0 and len(datasets[0]) > 0:
            xtick_positions = np.arange(0, len(datasets[0]), 5)  # Customize x-ticks every 5 points
            ax.set_xticks(xtick_positions)
            ax.set_xticklabels([f"{i}" for i in xtick_positions], fontsize=12, fontname=axis_font)

        # Set y-tick format with comma separation
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'${int(x):,}'))

        # Customize font properties for yticks
        plt.yticks(fontname=axis_font)

        # Construct the custom legend with colors and markers corresponding to the plot
        legend_handles = []
        if cumulative_legend_items:
            for i, sublist in enumerate(cumulative_legend_items):
                if not sublist:  # Skip empty sublists
                    continue
                    
                # Get color and marker safely
                color = colors[i] if i < len(colors) else 'blue'
                marker = markers[i % len(markers)] if markers else 'o'
                version_header = sublist[0]

                # Create a handle for the version header with the corresponding color and marker
                header_handle = ax.plot([], [], color=color, marker=marker, linestyle='None',
                                    label=version_header, markersize=8, markeredgewidth=2, 
                                    alpha=0.9, markerfacecolor="none")[0]
                legend_handles.append(header_handle)

                # Loop through the rest of the items for the version
                for item in sublist[1:]:
                    item_handle = ax.plot([], [], color=color, marker=marker, linestyle='None',
                                        label=item, markersize=6, markeredgewidth=1.5, alpha=0.7)[0]
                    legend_handles.append(item_handle)

        title_font = font_manager.FontProperties(family='Georgia', size=12)

        # Add the custom legend only if there are legend handles
        if legend_handles:
            ax.legend(handles=legend_handles, loc='center left', bbox_to_anchor=(1.05, 0.5), frameon=True,
                        fancybox=True, edgecolor='black', fontsize=10, labelspacing=legend_item_spacing, prop={'family': legend_font}, title='Investment Scenario Configurations', title_fontproperties=title_font)

        # Add grid lines for both horizontal and vertical axes
        ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)  # Vertical grid lines
        ax.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5)  # Horizontal grid lines
        # Set plot background color and finalize layout
        ax.set_facecolor('#f0f0f0')  # Light grey background
        # Adjust layout to ensure nothing is cut off
        plt.tight_layout(rect=[0, 0, 1, 1])

    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        plt.savefig(filename, bbox_inches='tight')
        logging.info(f"Successfully saved plot to {filename}")
    except Exception as e:
        logging.error(f"Error saving plot to {filename}: {str(e)}")
        # Try to save in output_data_dir as fallback
        try:
            # Create a version-specific subdirectory in output_data_dir
            version_dir = os.path.join(output_data_dir, f'version_{versions_identifier}')
            os.makedirs(version_dir, exist_ok=True)
            fallback_filename = os.path.join(version_dir, os.path.basename(filename))
            plt.savefig(fallback_filename, bbox_inches='tight')
            logging.info(f"Successfully saved plot to fallback location: {fallback_filename}")
        except Exception as e:
            logging.error(f"Error saving plot to fallback location: {str(e)}")
            # Try one last time in output_data_dir directly
            try:
                last_resort_filename = os.path.join(output_data_dir, os.path.basename(filename))
                plt.savefig(last_resort_filename, bbox_inches='tight')
                logging.info(f"Successfully saved plot to last resort location: {last_resort_filename}")
            except Exception as e:
                logging.error(f"Failed to save plot anywhere: {str(e)}")
    finally:
        plt.close()
    
# Plot and save for each version
for selected_version in selected_versions:
    try:
        # Create version-specific directory path
        batch_folder = os.path.join(PUBLIC_DIR, f'Batch({selected_version})')
        results_folder = os.path.join(batch_folder, f'Results({selected_version})')
        version_specific_dir = os.path.join(results_folder, f'{versions_identifier}_AnnotatedStaticPlots')
        
        # Create directories if they don't exist
        os.makedirs(batch_folder, exist_ok=True)
        os.makedirs(results_folder, exist_ok=True)
        os.makedirs(version_specific_dir, exist_ok=True)
        
        filename_suffix = f'_{versions_identifier}.png'
        logging.info(f"Using directory for version {selected_version}: {version_specific_dir}")
    except Exception as e:
        logging.error(f"Error setting up directories for version {selected_version}: {str(e)}")
        # Use output_data_dir as fallback
        version_specific_dir = output_data_dir
        filename_suffix = f'_v{selected_version}_{versions_identifier}.png'
        logging.info(f"Using fallback directory: {version_specific_dir}")

    plot_aggregated(all_annual_cash_flows_net, 'Aggregated Annual Cash Flow Net', 'Year', 'Net Cash Flow', f'{version_specific_dir}/aggregated_annual_cash_flow_net{filename_suffix}')
    plot_aggregated(all_annual_revenues, 'Aggregated Annual Revenue', 'Year', 'Revenue', f'{version_specific_dir}/aggregated_revenue{filename_suffix}')
    plot_aggregated(all_annual_operating_expenses, 'Annual Operating Expenses', 'Year', 'Operating Expenses', f'{version_specific_dir}/aggregated_operating_expenses{filename_suffix}')
    plot_aggregated(all_depreciation_schedules, 'Aggregated Depreciation', 'Year', 'Depreciation', f'{version_specific_dir}/aggregated_depreciation{filename_suffix}')
    plot_aggregated(all_state_taxes, 'Aggregated State Taxes', 'Year', 'State Taxes', f'{version_specific_dir}/aggregated_state_taxes{filename_suffix}')
    plot_aggregated(all_federal_taxes, 'Aggregated Federal Taxes', 'Year', 'Federal Taxes', f'{version_specific_dir}/aggregated_federal_taxes{filename_suffix}')
    plot_aggregated(all_cumulative_cash_flows, 'Aggregated Cumulative Cash Flow', 'Year', 'Cumulative Cash Flow', f'{version_specific_dir}/aggregated_cumulative_cash_flow{filename_suffix}')
    # Save each dataset
cash_flow_path = save_to_csv(all_annual_cash_flows_net, "all_annual_cash_flows_net.csv")
revenue_path = save_to_csv(all_annual_revenues, "all_annual_revenues.csv")
expenses_path = save_to_csv(all_annual_operating_expenses, "all_annual_operating_expenses.csv")
depreciation_path = save_to_csv(all_depreciation_schedules, "all_depreciation_schedules.csv")
state_taxes_path = save_to_csv(all_state_taxes, "all_state_taxes.csv")
federal_taxes_path = save_to_csv(all_federal_taxes, "all_federal_taxes.csv")
cumulative_cash_flow_path = save_to_csv(all_cumulative_cash_flows, "all_cumulative_cash_flows.csv")

# Save cumulative legend items to a JSON file
legend_path = os.path.join(output_data_dir, "cumulative_legend_items.json")
with open(legend_path, 'w') as legend_file:
    json.dump(cumulative_legend_items, legend_file)

logging.info("All data and legend information saved for R script.")
logging.info("All plots completed successfully.")
print("All plots completed successfully.")
