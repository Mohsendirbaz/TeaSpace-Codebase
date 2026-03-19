from flask import Blueprint, request, jsonify, send_file
import logging
import os
import subprocess
import json
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from Sensitivity_File_Manager import SensitivityFileManager

# Configure logger
logger = logging.getLogger('sensitivity')

sensitivity_routes = Blueprint('sensitivity_routes', __name__)

# Mode directory mapping function
def get_mode_directory(mode):
    """
    Maps a sensitivity mode to its directory name.

    Args:
        mode (str): One of: 'percentage', 'directvalue', 'absolutedeparture', 'montecarlo'

    Returns:
        str: Capitalized directory name for the mode
    """
    mode_dir_mapping = {
        'percentage': 'Percentage',
        'directvalue': 'DirectValue',
        'absolutedeparture': 'AbsoluteDeparture',
        'montecarlo': 'MonteCarlo'
    }

    # Default to Percentage if unknown mode
    return mode_dir_mapping.get(mode.lower(), 'Percentage')

# Central path resolution function
def get_sensitivity_paths(version, param_id, mode, variation=None, compare_to_key='S13', comparison_type='primary'):
    """
    Get standardized paths for sensitivity analysis.

    Args:
        version (int): Version number
        param_id (str): Parameter ID (e.g., "S35")
        mode (str): One of 'percentage', 'directvalue', 'absolutedeparture', 'montecarlo'
        variation (float, optional): Variation value
        compare_to_key (str, optional): Comparison parameter
        comparison_type (str, optional): Comparison type

    Returns:
        dict: Dictionary of paths for this parameter
    """
    # Map mode to directory name
    mode_dir = get_mode_directory(mode)

    # Base paths
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', 'Original')

    paths = {
        'base_dir': base_dir,
        'sensitivity_dir': os.path.join(base_dir, f'Batch({version})', f'Results({version})', 'Sensitivity'),
        'param_dir': os.path.join(base_dir, f'Batch({version})', f'Results({version})', 'Sensitivity', param_id),
        'mode_dir': os.path.join(base_dir, f'Batch({version})', f'Results({version})', 'Sensitivity', mode_dir),
        'plots_dir': {}
    }

    # Add plot paths
    for plot_type in ['waterfall', 'bar', 'point']:
        plot_name = f"{plot_type}_{param_id}_{compare_to_key}_{comparison_type}.png"
        plot_path = os.path.join(paths['mode_dir'], plot_type, plot_name)
        paths['plots_dir'][plot_type] = plot_path

    # If variation is provided, add variation-specific paths
    if variation is not None:
        var_str = f"{variation:+.2f}"

        paths['param_var_dir'] = os.path.join(paths['param_dir'], mode.lower(), var_str)
        paths['config_var_dir'] = os.path.join(paths['mode_dir'], 'Configuration', f"{param_id}_{var_str}")

        # Economic summary in parameter variation directory
        paths['economic_summary'] = os.path.join(
            paths['param_var_dir'],
            f"Economic_Summary({version}).csv"
        )

        # Results file path
        paths['results_file'] = os.path.join(
            paths['mode_dir'],
            f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
        )

    return paths

# Base directory path - should be adjusted based on deployment context
base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'Original')
file_manager = SensitivityFileManager(base_dir)

def find_economic_summary_price(version, param_id=None, mode=None, variation=None):
    """
    Extracts price (S13) value from economic summary.

    Args:
        version (int): Version number
        param_id (str, optional): Parameter ID
        mode (str, optional): Analysis mode
        variation (float, optional): Variation value

    Returns:
        float: Price value or None if not found
    """
    try:
        # If we have param_id, mode, and variation, look in the specific directory
        if param_id and mode and variation is not None:
            paths = get_sensitivity_paths(version, param_id, mode, variation)
            economic_summary_path = paths['economic_summary']

            if os.path.exists(economic_summary_path):
                logger.info(f"Found economic summary at: {economic_summary_path}")
                economic_df = pd.read_csv(economic_summary_path)
            else:
                logger.warning(f"Economic summary not found at: {economic_summary_path}")
                return None
        else:
            # Otherwise use default path
            economic_summary_path = os.path.join(
                base_dir,
                f'Batch({version})',
                f'Results({version})',
                f"Economic_Summary({version}).csv"
            )

            if not os.path.exists(economic_summary_path):
                logger.warning(f"Economic summary not found: {economic_summary_path}")
                return None

            economic_df = pd.read_csv(economic_summary_path)

        price_row = economic_df[economic_df['Metric'] == 'Average Selling Price (Project Life Cycle)']

        if price_row.empty:
            logger.warning("Price row not found in economic summary")
            return None

        price_value = price_row.iloc[0, 1]  # Assuming value is in second column

        # Try to convert to float if it's a string
        if isinstance(price_value, str):
            # Remove $ and , if present
            price_value = price_value.replace('$', '').replace(',', '')
            try:
                price_value = float(price_value)
            except ValueError:
                logger.warning(f"Could not convert price value to float: {price_value}")

        logger.info(f"Extracted price value: {price_value}")
        return price_value

    except Exception as e:
        logger.error(f"Error extracting price from economic summary: {str(e)}")
        return None

def generate_plot_from_results(version, param_id, compare_to_key, plot_type, mode, result_path):
    """
    Generate a plot from existing result data using actual parameter values.

    Args:
        version (int): Version number
        param_id (str): Parameter ID
        compare_to_key (str): Comparison parameter ID
        plot_type (str): Type of plot to generate (waterfall, bar, point)
        mode (str): Analysis mode (percentage, directvalue, absolutedeparture, montecarlo)
        result_path (str): Path to the result data file

    Returns:
        bool: True if plot was generated successfully, False otherwise
    """
    logger.info(f"=== PLOT GENERATION FROM RESULTS ===")
    logger.info(f"Version: {version}")
    logger.info(f"Parameter: {param_id}")
    logger.info(f"Compare to: {compare_to_key}")
    logger.info(f"Plot type: {plot_type}")
    logger.info(f"Mode: {mode}")
    logger.info(f"Result path: {result_path}")

    try:
        # First, check if the result file exists
        if not os.path.exists(result_path):
            logger.error(f"Result file not found: {result_path}")
            return False

        # Load the result data
        with open(result_path, 'r') as f:
            result_data = json.load(f)

        # Extract variations
        variations = result_data.get('variations', [])
        if not variations:
            logger.error(f"No variation data found in {result_path}")
            return False

        # Get the datapoints file which contains actual parameter values
        datapoints_path = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            f"SensitivityPlotDatapoints_{version}.json"
        )

        # Check if datapoints file exists
        actual_parameter_values = None
        if os.path.exists(datapoints_path):
            try:
                with open(datapoints_path, 'r') as f:
                    datapoints = json.load(f)

                # Extract actual parameter values using param_id and compare_to_key
                key = f"{param_id},{compare_to_key}"
                if key in datapoints:
                    actual_parameter_values = datapoints[key]
                    logger.info(f"Found actual parameter values in datapoints file for {key}")
            except Exception as e:
                logger.warning(f"Error loading datapoints file: {str(e)}")

        # Get mode directory name
        mode_dir = get_mode_directory(mode)
        comparison_type = result_data.get('comparison_type', 'primary')

        # Construct plot path
        plot_name = f"{plot_type}_{param_id}_{compare_to_key}_{comparison_type}.png"

        # Define directory structure
        plot_path = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity',
            mode_dir,
            plot_type,
            plot_name
        )

        # Ensure directory exists
        os.makedirs(os.path.dirname(plot_path), exist_ok=True)

        # Extract variation values and prices
        x_values = []
        y_values = []
        point_labels = []

        for variation in variations:
            var_value = variation.get('variation')
            if var_value is not None:
                # Store the variation value (for label)
                point_labels.append(f"{var_value:+}")

                # Use actual parameter value if available
                if actual_parameter_values:
                    # In directvalue mode, use the variation directly
                    if mode.lower() == 'directvalue':
                        x_value = var_value
                    else:
                        # Try to find corresponding actual value
                        var_str = f"{var_value:+.2f}"
                        if "data" in actual_parameter_values:
                            for key in actual_parameter_values["data"]:
                                # Find closest match
                                if abs(float(key) - var_value) < 0.01:
                                    x_value = float(key)
                                    break
                            else:
                                # If not found, use variation as fallback
                                x_value = var_value
                        else:
                            x_value = var_value
                else:
                    # If no actual values available, use variation directly
                    x_value = var_value

                x_values.append(x_value)

                # Get price value
                price = None
                if 'values' in variation and 'price' in variation['values']:
                    price = variation['values']['price']

                y_values.append(price)

        # Sort values by x for proper ordering
        combined = sorted(zip(x_values, y_values, point_labels), key=lambda point: point[0])
        x_values = [point[0] for point in combined]
        y_values = [point[1] for point in combined]
        point_labels = [point[2] for point in combined]

        # Create plot
        plt.figure(figsize=(10, 6))

        if plot_type == 'waterfall':
            # Create waterfall plot with actual parameter values
            cumulative = 0
            for i, (x, y, label) in enumerate(zip(x_values, y_values, point_labels)):
                if i == 0:
                    # First bar is the base
                    plt.bar(i, y, width=0.5, color='blue', label=f"{label}")
                    cumulative = y
                else:
                    # Show difference from previous
                    diff = y - cumulative
                    color = 'green' if diff >= 0 else 'red'
                    plt.bar(i, diff, bottom=cumulative, width=0.5, color=color, label=f"{label}")
                    cumulative = y

            plt.title(f"Waterfall Analysis: {param_id} vs {compare_to_key}")
            plt.ylabel('Price')
            plt.xlabel(f'{param_id} Value')
            plt.xticks(range(len(x_values)), point_labels)

        elif plot_type == 'bar':
            # Create bar plot with actual parameter values
            plt.bar(x_values, y_values, color='blue')
            plt.title(f"Bar Analysis: {param_id} vs {compare_to_key}")
            plt.ylabel('Price')
            plt.xlabel(f'{param_id} Value')

        elif plot_type == 'point':
            # Create point/line plot with actual parameter values
            plt.plot(x_values, y_values, 'o-', color='blue')
            plt.title(f"Point Analysis: {param_id} vs {compare_to_key}")
            plt.ylabel('Price')
            plt.xlabel(f'{param_id} Value')

        # Add grid and save
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        # Verify file was created
        if os.path.exists(plot_path) and os.path.getsize(plot_path) > 0:
            logger.info(f"Successfully generated {plot_type} plot at {plot_path}")
            file_stats = os.stat(plot_path)
            logger.info(f"Plot file size: {file_stats.st_size} bytes")
            logger.info(f"Plot creation time: {time.ctime(file_stats.st_mtime)}")
            return True
        else:
            logger.error(f"Plot file creation failed or file is empty: {plot_path}")
            return False

    except Exception as e:
        logger.error(f"Error generating {plot_type} plot: {str(e)}")
        return False

@sensitivity_routes.route('/sensitivity/analysis', methods=['POST'])
def handle_sensitivity_analysis():
    """
    Processes sensitivity analysis for any mode.

    Expected JSON payload:
    {
        "param_id": "S10",
        "mode": "percentage",  # or "directvalue", "absolutedeparture", "montecarlo"
        "values": [10.0],
        "compareToKey": "S13",
        "comparisonType": "primary",
        "version": 1,
        "waterfall": true,
        "bar": true,
        "point": true
    }
    """
    run_id = time.strftime("%Y%m%d_%H%M%S")
    logger.info(f"\n{'='*80}")
    logger.info(f"Sensitivity Analysis Request - Run ID: {run_id}")
    logger.info(f"{'='*80}")

    try:
        data = request.json
        logger.info(f"Request data: {data}")

        # Validate required parameters
        param_id = data.get('param_id')
        if not param_id or not param_id.startswith('S') or not param_id[1:].isdigit():
            return jsonify({"error": "Invalid parameter ID format"}), 400

        # Get values array
        values = data.get('values', [])
        if not values:
            return jsonify({"error": "No variation values provided"}), 400

        # Get mode with default to percentage
        mode = data.get('mode', 'percentage')
        if mode not in ['percentage', 'directvalue', 'absolutedeparture', 'montecarlo']:
            logger.warning(f"Unknown mode '{mode}', defaulting to 'percentage'")
            mode = 'percentage'

        # Use S13 as default compareToKey if none provided
        compare_to_key = data.get('compareToKey', 'S13')
        version = data.get('version', 1)
        comparison_type = data.get('comparisonType', 'primary')

        logger.info(f"Processing {param_id} with {len(values)} variation(s) in {mode} mode vs {compare_to_key}")

        # Get all necessary paths
        paths = get_sensitivity_paths(version, param_id, mode, compare_to_key=compare_to_key, comparison_type=comparison_type)

        # Ensure mode directory exists
        os.makedirs(paths['mode_dir'], exist_ok=True)

        # Create results data structure
        result_data = {
            'parameter': param_id,
            'compare_to_key': compare_to_key,
            'comparison_type': comparison_type,
            'mode': mode,
            'version': version,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'variations': []
        }

        # Execute calculations for each variation
        for var in values:
            var_str = f"{var:+.2f}"
            logger.info(f"Processing variation: {var_str}")

            # Get paths for this specific variation
            var_paths = get_sensitivity_paths(version, param_id, mode, var, compare_to_key, comparison_type)

            # Ensure parameter variation directory exists
            os.makedirs(var_paths['param_var_dir'], exist_ok=True)

            # Execute the sensitivity calculation script
            calculation_script = os.path.join(base_dir, "Core_calculation_engines", "CFA-b.py")

            if not os.path.exists(calculation_script):
                logger.warning(f"CFA-b.py not found: {calculation_script}")
                calculation_script = os.path.join(base_dir, "Core_calculation_engines", "CFA.py")

            calc_result = subprocess.run(
                [
                    'python',
                    calculation_script,
                    str(version),
                    param_id,
                    str(var),
                    compare_to_key,
                    mode  # Add mode as parameter to calculation script
                ],
                capture_output=True,
                text=True
            )

            if calc_result.returncode != 0:
                error_msg = f"Calculation failed for {param_id} ({var_str}): {calc_result.stderr}"
                logger.error(error_msg)
                result_data['variations'].append({
                    'variation': var,
                    'variation_str': var_str,
                    'status': 'error',
                    'error': error_msg
                })
                continue

            # Extract price from economic summary in the parameter variation directory
            price_value = find_economic_summary_price(version, param_id, mode, var)

            # Add variation result
            result_data['variations'].append({
                'variation': var,
                'variation_str': var_str,
                'status': 'completed',
                'values': {
                    'price': price_value
                }
            })

            logger.info(f"Completed calculation for variation {var_str}")

        # Store calculation results using file manager with the new mode
        result_path = file_manager.store_calculation_result(
            version=version,
            param_id=param_id,
            result_data=result_data,
            mode=mode,
            compare_to_key=compare_to_key
        )

        logger.info(f"Stored calculation results at {result_path['path'] if isinstance(result_path, dict) else result_path}")

        # Generate requested plots
        plot_types = []
        if data.get('waterfall'): plot_types.append('waterfall')
        if data.get('bar'): plot_types.append('bar')
        if data.get('point'): plot_types.append('point')

        generated_plots = {}

        for plot_type in plot_types:
            # Create plot directory if it doesn't exist
            plot_dir = os.path.join(paths['mode_dir'], plot_type)
            os.makedirs(plot_dir, exist_ok=True)

            # Generate plot using our internal function
            try:
                logger.info(f"Generating {plot_type} plot for {param_id}")

                result_file_path = result_path['path'] if isinstance(result_path, dict) else result_path

                plot_generated = generate_plot_from_results(
                    version=version,
                    param_id=param_id,
                    compare_to_key=compare_to_key,
                    plot_type=plot_type,
                    mode=mode,
                    result_path=result_file_path
                )

                if plot_generated:
                    plot_path = paths['plots_dir'][plot_type]
                    generated_plots[plot_type] = {
                        'status': 'completed',
                        'path': os.path.relpath(plot_path, base_dir)
                    }
                    logger.info(f"Generated {plot_type} plot at {plot_path}")
                else:
                    error_msg = f"Failed to generate {plot_type} plot"
                    logger.error(error_msg)
                    generated_plots[plot_type] = {
                        'status': 'error',
                        'error': error_msg
                    }
            except Exception as e:
                error_msg = f"Error generating {plot_type} plot: {str(e)}"
                logger.error(error_msg)
                generated_plots[plot_type] = {
                    'status': 'error',
                    'error': error_msg
                }

        # Prepare response
        response = {
            "status": "success",
            "runId": run_id,
            "message": f"{mode.capitalize()} analysis completed",
            "parameter": param_id,
            "compareToKey": compare_to_key,
            "mode": mode,
            "variations": values,
            "plots": generated_plots,
            "directory": paths['mode_dir'],
            "results_path": result_path['path'] if isinstance(result_path, dict) else result_path
        }

        logger.info(f"\n{'='*80}")
        logger.info(f"Analysis Completed - Run ID: {run_id}")
        logger.info(f"{'='*80}")

        return jsonify(response)

    except Exception as e:
        error_msg = f"Error in sensitivity analysis: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            "error": error_msg,
            "runId": run_id
        }), 500

@sensitivity_routes.route('/api/sensitivity/parameters', methods=['GET'])
def get_sensitivity_parameters():
    """Returns all sensitivity parameters for a specific version."""
    try:
        version = request.args.get('version', '1')

        # Define paths
        base_dir_results = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity'
        )

        if not os.path.exists(base_dir_results):
            return jsonify([])

        parameters = {}

        # Check parameter directories
        for item in os.listdir(base_dir_results):
            item_path = os.path.join(base_dir_results, item)

            # Look for parameter directories (starting with S)
            if os.path.isdir(item_path) and item.startswith('S'):
                param_id = item

                # Determine modes from subdirectories
                modes = []
                if os.path.exists(os.path.join(item_path, 'percentage')):
                    modes.append('percentage')
                if os.path.exists(os.path.join(item_path, 'directvalue')):
                    modes.append('directvalue')
                if os.path.exists(os.path.join(item_path, 'absolutedeparture')):
                    modes.append('absolutedeparture')
                if os.path.exists(os.path.join(item_path, 'montecarlo')):
                    modes.append('montecarlo')

                # Get compare_to_key from result files
                compare_to_key = 'S13'  # Default
                for mode in ['Percentage', 'DirectValue', 'AbsoluteDeparture', 'MonteCarlo']:
                    mode_dir = os.path.join(base_dir_results, mode)

                    if not os.path.exists(mode_dir):
                        continue

                    # Check result files
                    for file in os.listdir(mode_dir):
                        if file.startswith(f"{param_id}_vs_") and file.endswith('_results.json'):
                            parts = file.replace('_results.json', '').split('_vs_')
                            if len(parts) >= 2:
                                compare_to_key = parts[1].split('_')[0]
                                break

                # Add parameter info
                parameters[param_id] = {
                    'id': param_id,
                    'modes': modes,
                    'compareToKey': compare_to_key
                }

        return jsonify(list(parameters.values()))

    except Exception as e:
        logger.error(f"Error retrieving sensitivity parameters: {str(e)}")
        return jsonify({
            "error": f"Error retrieving sensitivity parameters: {str(e)}"
        }), 500

@sensitivity_routes.route('/api/sensitivity/visualize', methods=['POST'])
def sensitivity_visualize():
    """
    Generate visualization data for sensitivity analysis.

    Expected JSON payload:
    {
        "version": 1,
        "param_id": "S10",
        "mode": "percentage",
        "compareToKey": "S13",
        "plotTypes": ["waterfall", "bar", "point"]
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract parameters
        version = data.get('version', 1)
        param_id = data.get('param_id')
        mode = data.get('mode', 'percentage')
        compare_to_key = data.get('compareToKey', 'S13')
        comparison_type = data.get('comparisonType', 'primary')
        plot_types = data.get('plotTypes', ['waterfall', 'bar', 'point'])

        if not param_id:
            return jsonify({"error": "Parameter ID is required"}), 400

        # Get paths
        paths = get_sensitivity_paths(version, param_id, mode, compare_to_key=compare_to_key, comparison_type=comparison_type)

        # Get result file path
        result_file = os.path.join(
            paths['mode_dir'],
            f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
        )

        # Check if results file exists
        if not os.path.exists(result_file):
            return jsonify({
                "error": "Sensitivity results not found",
                "message": f"No results available for {param_id} in {mode} mode"
            }), 404

        # Load results data
        with open(result_file, 'r') as f:
            result_data = json.load(f)

        # Check if plots exist or need to be generated
        plots_info = {}

        for plot_type in plot_types:
            plot_path = paths['plots_dir'][plot_type]

            if os.path.exists(plot_path):
                # Plot exists
                plots_info[plot_type] = {
                    "status": "available",
                    "path": os.path.relpath(plot_path, base_dir)
                }
            else:
                # Generate plot
                try:
                    plot_generated = generate_plot_from_results(
                        version=version,
                        param_id=param_id,
                        compare_to_key=compare_to_key,
                        plot_type=plot_type,
                        mode=mode,
                        result_path=result_file
                    )

                    if plot_generated:
                        plots_info[plot_type] = {
                            "status": "generated",
                            "path": os.path.relpath(plot_path, base_dir)
                        }
                    else:
                        plots_info[plot_type] = {
                            "status": "error",
                            "error": "Failed to generate plot"
                        }
                except Exception as e:
                    plots_info[plot_type] = {
                        "status": "error",
                        "error": str(e)
                    }

        # Prepare visualization data
        visualization_data = {
            "parameter": param_id,
            "compareToKey": compare_to_key,
            "mode": mode,
            "data": result_data,
            "plots": plots_info
        }

        return jsonify(visualization_data)

    except Exception as e:
        logger.error(f"Error in visualization endpoint: {str(e)}")
        return jsonify({
            "error": f"Error generating visualization: {str(e)}"
        }), 500

@sensitivity_routes.route('/sensitivity/plots/<mode>/<plot_type>', methods=['GET'])
def get_sensitivity_plot(mode, plot_type):
    """
    Retrieves a specific sensitivity plot.

    Query parameters:
    - param_id: Parameter ID (e.g., S10)
    - compareToKey: Comparison parameter ID (default: S13)
    - comparisonType: Comparison type (default: primary)
    - version: Version number
    """
    try:
        param_id = request.args.get('param_id')
        compare_to_key = request.args.get('compareToKey', 'S13')
        comparison_type = request.args.get('comparisonType', 'primary')
        version = request.args.get('version', '1')

        if not param_id:
            return jsonify({"error": "Parameter ID is required"}), 400

        logger.info(f"Retrieving {plot_type} plot for {param_id} vs {compare_to_key} in {mode} mode")

        # Get plot information from file manager
        plot_info = file_manager.get_plot_path(
            version=int(version),
            mode=mode,
            plot_type=plot_type,
            param_id=param_id,
            compare_to_key=compare_to_key,
            comparison_type=comparison_type
        )

        if plot_info['status'] != 'ready':
            return jsonify({
                "error": f"Plot not found: {plot_info.get('error', 'Unknown error')}"
            }), 404

        logger.info(f"Returning plot from {plot_info['full_path']}")
        return send_file(plot_info['full_path'], mimetype='image/png')

    except Exception as e:
        error_msg = f"Error retrieving plot: {str(e)}"
        logger.error(error_msg)
        return
@sensitivity_routes.route('/api/sensitivity-plots/<version>', methods=['GET'])
def get_sensitivity_plots_by_version(version):
    """Returns all sensitivity plots for a specific version."""
    try:
        # Define paths
        base_dir_results = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity'
        )

        if not os.path.exists(base_dir_results):
            return jsonify([])

        plots_data = []

        # Search in all mode directories
        for mode in ['Percentage', 'DirectValue', 'AbsoluteDeparture', 'MonteCarlo']:
            mode_dir = os.path.join(base_dir_results, mode)

            if not os.path.exists(mode_dir):
                continue

            # Search for plot files in each plot type subdirectory
            for plot_type in ['waterfall', 'bar', 'point']:
                plot_type_dir = os.path.join(mode_dir, plot_type)

                if not os.path.exists(plot_type_dir):
                    continue

                # Find all PNG files
                for root, _, files in os.walk(plot_type_dir):
                    for file in files:
                        if file.endswith('.png'):
                            # Extract parameter and comparison info from filename
                            file_parts = file.replace('.png', '').split('_')

                            if len(file_parts) >= 4:
                                # Extract parts from filename (e.g., waterfall_S10_S13_primary.png)
                                plot_data = {
                                    'path': os.path.join(root, file),
                                    'title': f"{file_parts[0].capitalize()} Plot: {file_parts[1]} vs {file_parts[2]}",
                                    'category': file_parts[1],  # Parameter ID (e.g., S10)
                                    'group': plot_type.capitalize(),  # Plot type as group
                                    'description': f"Comparison type: {file_parts[3]}",
                                    'mode': mode
                                }

                                plots_data.append(plot_data)

                # Also check for plots directly in mode directory
                for file in os.listdir(mode_dir):
                    if file.endswith('.png') and file.startswith(f"{plot_type}_"):
                        # Extract parameter and comparison info from filename
                        file_parts = file.replace('.png', '').split('_')

                        if len(file_parts) >= 4:
                            plot_data = {
                                'path': os.path.join(mode_dir, file),
                                'title': f"{file_parts[0].capitalize()} Plot: {file_parts[1]} vs {file_parts[2]}",
                                'category': file_parts[1],  # Parameter ID (e.g., S10)
                                'group': plot_type.capitalize(),  # Plot type as group
                                'description': f"Comparison type: {file_parts[3]}",
                                'mode': mode
                            }

                            plots_data.append(plot_data)

        return jsonify(plots_data)

    except Exception as e:
        logger.error(f"Error retrieving sensitivity plots: {str(e)}")
        return jsonify({
            "error": f"Error retrieving sensitivity plots: {str(e)}"
        }), 500

@sensitivity_routes.route('/api/sensitivity-plots/<version>/<param_id>', methods=['GET'])
def get_sensitivity_plots_by_parameter(version, param_id):
    """Returns sensitivity plots for a specific parameter."""
    try:
        # Define paths
        base_dir_results = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity'
        )

        if not os.path.exists(base_dir_results):
            return jsonify([])

        plots_data = []

        # Search in all mode directories
        for mode in ['Percentage', 'DirectValue', 'AbsoluteDeparture', 'MonteCarlo']:
            mode_dir = os.path.join(base_dir_results, mode)

            if not os.path.exists(mode_dir):
                continue

            # Search for plot files in each plot type subdirectory
            for plot_type in ['waterfall', 'bar', 'point']:
                plot_type_dir = os.path.join(mode_dir, plot_type)

                if not os.path.exists(plot_type_dir):
                    continue

                # Find all PNG files for this parameter
                for root, _, files in os.walk(plot_type_dir):
                    for file in files:
                        if file.endswith('.png') and f"_{param_id}_" in file:
                            # Extract parameter and comparison info from filename
                            file_parts = file.replace('.png', '').split('_')

                            if len(file_parts) >= 4:
                                plot_data = {
                                    'path': os.path.join(root, file),
                                    'title': f"{file_parts[0].capitalize()} Plot: {file_parts[1]} vs {file_parts[2]}",
                                    'category': file_parts[1],  # Parameter ID (e.g., S10)
                                    'group': plot_type.capitalize(),  # Plot type as group
                                    'description': f"Comparison type: {file_parts[3]}",
                                    'mode': mode
                                }

                                plots_data.append(plot_data)

                # Also check for plots directly in mode directory
                for file in os.listdir(mode_dir):
                    if file.endswith('.png') and file.startswith(f"{plot_type}_") and f"_{param_id}_" in file:
                        # Extract parameter and comparison info from filename
                        file_parts = file.replace('.png', '').split('_')

                        if len(file_parts) >= 4:
                            plot_data = {
                                'path': os.path.join(mode_dir, file),
                                'title': f"{file_parts[0].capitalize()} Plot: {file_parts[1]} vs {file_parts[2]}",
                                'category': file_parts[1],  # Parameter ID (e.g., S10)
                                'group': plot_type.capitalize(),  # Plot type as group
                                'description': f"Comparison type: {file_parts[3]}",
                                'mode': mode
                            }

                            plots_data.append(plot_data)

        return jsonify(plots_data)

    except Exception as e:
        logger.error(f"Error retrieving sensitivity plots: {str(e)}")
        return jsonify({
            "error": f"Error retrieving sensitivity plots: {str(e)}"
        }), 500

@sensitivity_routes.route('/api/sensitivity-plots/<version>/<category>/<group>', methods=['GET'])
def get_sensitivity_plots_by_category_and_group(version, category, group):
    """Returns sensitivity plots for a specific category and group."""
    try:
        # Define paths
        base_dir_results = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity'
        )

        if not os.path.exists(base_dir_results):
            return jsonify([])

        plots_data = []

        # Determine which mode directories to search
        # Map group to mode if it's one of our modes
        group_lower = group.lower()
        if group_lower in ['percentage', 'directvalue', 'absolutedeparture', 'montecarlo']:
            # If group is a mode, search only in that mode directory
            modes = [get_mode_directory(group_lower)]
        else:
            # Otherwise search in all mode directories
            modes = ['Percentage', 'DirectValue', 'AbsoluteDeparture', 'MonteCarlo']

        for mode in modes:
            mode_dir = os.path.join(base_dir_results, mode)

            if not os.path.exists(mode_dir):
                continue

            # If group is a plot type, search in that directory
            if group.lower() in ['bar', 'waterfall', 'point']:
                plot_type_dir = os.path.join(mode_dir, group.lower())

                if not os.path.exists(plot_type_dir):
                    continue

                # Find all PNG files for this category
                for root, _, files in os.walk(plot_type_dir):
                    for file in files:
                        if file.endswith('.png') and (f"_{category}_" in file or file.startswith(f"{group.lower()}_{category}_")):
                            # Extract parameter and comparison info from filename
                            file_parts = file.replace('.png', '').split('_')

                            if len(file_parts) >= 4:
                                plot_data = {
                                    'path': os.path.join(root, file),
                                    'title': f"{file_parts[0].capitalize()} Plot: {file_parts[1]} vs {file_parts[2]}",
                                    'category': file_parts[1],  # Parameter ID (e.g., S10)
                                    'group': file_parts[0].capitalize(),  # Plot type as group
                                    'description': f"Comparison type: {file_parts[3]}",
                                    'mode': mode
                                }

                                plots_data.append(plot_data)

            # Also check for plots directly in mode directory
            for file in os.listdir(mode_dir):
                if file.endswith('.png') and (f"_{category}_" in file or file.startswith(f"{group.lower()}_{category}_")):
                    # Extract parameter and comparison info from filename
                    file_parts = file.replace('.png', '').split('_')

                    if len(file_parts) >= 4:
                        plot_data = {
                            'path': os.path.join(mode_dir, file),
                            'title': f"{file_parts[0].capitalize()} Plot: {file_parts[1]} vs {file_parts[2]}",
                            'category': file_parts[1],  # Parameter ID (e.g., S10)
                            'group': file_parts[0].capitalize(),  # Plot type as group
                            'description': f"Comparison type: {file_parts[3]}",
                            'mode': mode
                        }

                        plots_data.append(plot_data)

        return jsonify(plots_data)

    except Exception as e:
        logger.error(f"Error retrieving sensitivity plots: {str(e)}")
        return jsonify({
            "error": f"Error retrieving sensitivity plots: {str(e)}"
        }), 500

@sensitivity_routes.route('/api/sensitivity-summary/<version>', methods=['GET'])
def get_sensitivity_summary(version):
    """Returns a summary of sensitivity analysis for a specific version."""
    try:
        # Define paths
        base_dir_results = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity'
        )

        if not os.path.exists(base_dir_results):
            return jsonify({
                "version": version,
                "parameters": [],
                "plots": [],
                "status": "not_found"
            })

        # Get parameters
        parameters = []
        for item in os.listdir(base_dir_results):
            item_path = os.path.join(base_dir_results, item)

            # Look for parameter directories (starting with S)
            if os.path.isdir(item_path) and item.startswith('S'):
                param_id = item

                # Determine mode from subdirectories
                modes = []
                if os.path.exists(os.path.join(item_path, 'percentage')):
                    modes.append('percentage')
                if os.path.exists(os.path.join(item_path, 'directvalue')):
                    modes.append('directvalue')
                if os.path.exists(os.path.join(item_path, 'absolutedeparture')):
                    modes.append('absolutedeparture')
                if os.path.exists(os.path.join(item_path, 'montecarlo')):
                    modes.append('montecarlo')

                parameters.append({
                    'id': param_id,
                    'modes': modes
                })

        # Get plot counts
        plot_counts = {
            'waterfall': 0,
            'bar': 0,
            'point': 0,
            'total': 0
        }

        for mode in ['Percentage', 'DirectValue', 'AbsoluteDeparture', 'MonteCarlo']:
            mode_dir = os.path.join(base_dir_results, mode)

            if not os.path.exists(mode_dir):
                continue

            for plot_type in ['waterfall', 'bar', 'point']:
                plot_type_dir = os.path.join(mode_dir, plot_type)

                if not os.path.exists(plot_type_dir):
                    continue

                # Count PNG files
                for root, _, files in os.walk(plot_type_dir):
                    plot_files = [f for f in files if f.endswith('.png')]
                    plot_counts[plot_type] += len(plot_files)
                    plot_counts['total'] += len(plot_files)

                # Also check mode directory directly
                for file in os.listdir(mode_dir):
                    if file.endswith('.png') and file.startswith(f"{plot_type}_"):
                        plot_counts[plot_type] += 1
                        plot_counts['total'] += 1

        # Get reports
        reports_dir = os.path.join(
            base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Reports'
        )

        reports = []
        if os.path.exists(reports_dir):
            for file in os.listdir(reports_dir):
                if file.startswith('sensitivity_analysis_') and file.endswith('.html'):
                    report_path = os.path.join(reports_dir, file)
                    timestamp = datetime.fromtimestamp(os.path.getmtime(report_path))

                    reports.append({
                        'name': file,
                        'path': os.path.relpath(report_path, base_dir),
                        'timestamp': timestamp.isoformat(),
                        'size': os.path.getsize(report_path)
                    })

        summary = {
            "version": version,
            "parameters": parameters,
            "plot_counts": plot_counts,
            "reports": reports,
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }

        return jsonify(summary)

    except Exception as e:
        logger.error(f"Error retrieving sensitivity summary: {str(e)}")
        return jsonify({
            "error": f"Error retrieving sensitivity summary: {str(e)}",
            "version": version,
            "status": "error"
        }), 500

@sensitivity_routes.route('/generate-report', methods=['POST'])
def generate_sensitivity_report():
    """
    Generate a comprehensive report for sensitivity analysis.

    Expected JSON payload:
    {
        "version": 1,
        "parameters": ["S10", "S11", "S12"]  # Optional, if not provided all parameters will be included
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        version = data.get('version')
        param_ids = data.get('parameters', [])

        if not version:
            return jsonify({"error": "Version number is required"}), 400

        # Get all parameters if none specified
        if not param_ids:
            # Get all parameter directories
            sensitivity_dir = os.path.join(
                base_dir,
                f'Batch({version})',
                f'Results({version})',
                'Sensitivity'
            )

            if not os.path.exists(sensitivity_dir):
                return jsonify({"error": "No sensitivity data found"}), 404

            # Get all parameter directories
            for item in os.listdir(sensitivity_dir):
                item_path = os.path.join(sensitivity_dir, item)
                if os.path.isdir(item_path) and item.startswith('S'):
                    param_ids.append(item)

        if not param_ids:
            return jsonify({"error": "No parameters found"}), 404

        # Collect data for each parameter
        report_data = {}

        for param_id in param_ids:
            # Check which modes are available for this parameter
            param_dir = os.path.join(
                base_dir,
                f'Batch({version})',
                f'Results({version})',
                'Sensitivity',
                param_id
            )

            if not os.path.exists(param_dir):
                continue

            # Find available modes
            available_modes = []
            for mode in ['percentage', 'directvalue', 'absolutedeparture', 'montecarlo']:
                mode_dir = os.path.join(param_dir, mode)
                if os.path.exists(mode_dir):
                    available_modes.append(mode)

            if not available_modes:
                continue

            # Use first available mode for this parameter
            selected_mode = available_modes[0]

            # Get compare_to_key for this parameter
            compare_to_key = 'S13'  # Default

            # Get results file
            mode_dir = get_mode_directory(selected_mode)
            result_file = os.path.join(
                base_dir,
                f'Batch({version})',
                f'Results({version})',
                'Sensitivity',
                mode_dir,
                f"{param_id}_vs_{compare_to_key}_{selected_mode.lower()}_results.json"
            )

            # Try alternate result file if first one not found
            if not os.path.exists(result_file):
                result_file = os.path.join(
                    base_dir,
                    f'Batch({version})',
                    f'Results({version})',
                    'Sensitivity',
                    mode_dir,
                    f"{param_id}_results.json"
                )

            if not os.path.exists(result_file):
                continue

            # Load results
            with open(result_file, 'r') as f:
                results = json.load(f)

            # Get plots
            plots = {}
            for plot_type in ['waterfall', 'bar', 'point']:
                plot_file = os.path.join(
                    base_dir,
                    f'Batch({version})',
                    f'Results({version})',
                    'Sensitivity',
                    mode_dir,
                    plot_type,
                    f"{plot_type}_{param_id}_{compare_to_key}_primary.png"
                )

                if os.path.exists(plot_file):
                    plots[plot_type] = os.path.relpath(plot_file, base_dir)

            # Add parameter data
            report_data[param_id] = {
                'mode': selected_mode,
                'compareToKey': compare_to_key,
                'results': results,
                'plots': plots,
                'variations': results.get('variations', [])
            }

        # Generate report using file manager
        if not report_data:
            return jsonify({"error": "No valid parameter data found"}), 404

        report_path = file_manager.create_analysis_report(
            version=version,
            analysis_data=report_data
        )

        # Return relative path
        relative_path = os.path.relpath(report_path, base_dir)

        return jsonify({
            "status": "success",
            "message": "Sensitivity report generated successfully",
            "report_path": relative_path,
            "parameter_count": len(report_data)
        })

    except Exception as e:
        logger.error(f"Error generating sensitivity report: {str(e)}")
        return jsonify({
            "error": f"Error generating sensitivity report: {str(e)}"
        }), 500

# Backward compatibility routes (redirect to unified endpoint)
@sensitivity_routes.route('/sensitivity/percentage', methods=['POST'])
def handle_percentage_analysis():
    """Legacy endpoint for percentage analysis."""
    try:
        # Get the original request data
        data = request.json

        # Log that we're using the legacy endpoint
        logger.info("Using legacy /percentage endpoint - redirecting to unified analysis endpoint")

        # Add or update mode in the data
        if data:
            data['mode'] = 'percentage'

        # Call the unified endpoint
        return handle_sensitivity_analysis()

    except Exception as e:
        error_msg = f"Error in legacy percentage endpoint: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

@sensitivity_routes.route('/sensitivity/directvalue', methods=['POST'])
def handle_directvalue_analysis():
    """Legacy endpoint for directvalue analysis."""
    try:
        # Get the original request data
        data = request.json

        # Log that we're using the legacy endpoint
        logger.info("Using legacy /directvalue endpoint - redirecting to unified analysis endpoint")

        # Add or update mode in the data
        if data:
            data['mode'] = 'directvalue'

        # Call the unified endpoint
        return handle_sensitivity_analysis()

    except Exception as e:
        error_msg = f"Error in legacy directvalue endpoint: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500