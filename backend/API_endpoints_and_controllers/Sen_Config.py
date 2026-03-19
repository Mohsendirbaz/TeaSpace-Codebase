import json
import os
import pandas as pd
import importlib.util
import sys
import copy
import logging
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logger
logger = logging.getLogger('sensitivity')

def parse_filtered_values(filtered_values):
    """Parse filtered values from string to dictionary."""
    try:
        # Convert double-double quotes for strings to single double-quotes before parsing
        filtered_values_dict = json.loads(filtered_values.replace('""', '"'))
        return filtered_values_dict
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing filtered_values: {filtered_values}. Error: {e}")
        return []

def strip_value(value):
    """Strips quotes from numeric values and keeps strings quoted."""
    if isinstance(value, str):
        try:
            if '.' in value:
                return float(value)  # Handle floats
            return int(value)  # Handle integers
        except ValueError:
            return value  # Return string as is if conversion fails
    return value

def find_parameter_by_id(config_module, param_id):
    """
    Find the parameter name in config_module that corresponds to the param_id.
    Identifies parameters by matching the numeric portion of param_id with
    the last digits of parameter names in the configuration.

    Args:
        config_module (dict): Configuration module
        param_id (str): Parameter ID (e.g., 'S13')

    Returns:
        str: Parameter name found in config_module
    """
    # Extract the numerical part of the parameter ID
    if not param_id.startswith('S') or not param_id[1:].isdigit():
        raise ValueError(f"Invalid parameter ID format: {param_id}")

    param_digits = param_id[1:]  # Get just the numeric part
    logger.info(f"Searching for parameter with numeric identifier: {param_digits}")

    # Efficient search - just look for keys ending with the two-digit number
    for key in config_module:
        if key.endswith(param_digits):
            logger.info(f"Found parameter by numeric suffix match: {key} for {param_id}")
            return key

    # If not found, log warning and raise error
    logger.warning(f"Could not find parameter for {param_id} in config module")
    raise ValueError(f"Could not find parameter for {param_id} in config module")

def apply_sensitivity_variation(config_module, param_id, variation_value, mode='percentage'):
    """
    Applies sensitivity variation to the specified parameter.

    Args:
        config_module (dict): Configuration module
        param_id (str): Parameter ID (e.g., 'S13')
        variation_value (float): Variation value to apply
        mode (str): One of 'percentage', 'directvalue', 'absolutedeparture', or 'montecarlo'

    Returns:
        dict: Modified configuration module
    """
    try:
        # Find parameter in config module
        param_name = find_parameter_by_id(config_module, param_id)

        # Get original value
        original_value = config_module[param_name]

        # Apply variation based on mode
        if mode.lower() == 'percentage':
            # For percentage mode, apply percentage change
            if isinstance(original_value, (int, float)):
                modified_value = original_value * (1 + variation_value/100)
            elif isinstance(original_value, list):
                # For list values, apply to each element
                modified_value = [val * (1 + variation_value/100) for val in original_value]
            else:
                raise TypeError(f"Unsupported parameter type: {type(original_value)}")

        elif mode.lower() == 'directvalue':
            # For direct value mode, use variation value directly (no change to original)
            if isinstance(original_value, (int, float)):
                modified_value = variation_value
            elif isinstance(original_value, list):
                # For list values, replace with variation
                modified_value = [variation_value] * len(original_value)
            else:
                raise TypeError(f"Unsupported parameter type for direct value mode: {type(original_value)}")

        elif mode.lower() == 'absolutedeparture':
            # For absolute departure mode, add variation to the original value
            if isinstance(original_value, (int, float)):
                modified_value = original_value + variation_value
            elif isinstance(original_value, list):
                # For list values, add to each element
                modified_value = [val + variation_value for val in original_value]
            else:
                raise TypeError(f"Unsupported parameter type for absolute departure mode: {type(original_value)}")

        elif mode.lower() == 'montecarlo':
            # For Monte Carlo mode, use percentage mode logic for now
            # This will be expanded later with Monte Carlo specific logic
            logger.info("Using percentage mode logic for Monte Carlo (to be implemented)")
            if isinstance(original_value, (int, float)):
                modified_value = original_value * (1 + variation_value/100)
            elif isinstance(original_value, list):
                modified_value = [val * (1 + variation_value/100) for val in original_value]
            else:
                raise TypeError(f"Unsupported parameter type: {type(original_value)}")
        else:
            # Default to percentage mode for unknown modes
            logger.warning(f"Unknown variation mode: {mode}. Defaulting to percentage mode.")
            if isinstance(original_value, (int, float)):
                modified_value = original_value * (1 + variation_value/100)
            elif isinstance(original_value, list):
                modified_value = [val * (1 + variation_value/100) for val in original_value]
            else:
                raise TypeError(f"Unsupported parameter type: {type(original_value)}")

        # Update the config module
        config_module[param_name] = modified_value

        # Format log message based on mode
        if mode.lower() == 'percentage':
            log_msg = f"Applied {variation_value}% variation to {param_name} ({param_id})"
        elif mode.lower() == 'directvalue':
            log_msg = f"Applied direct value {variation_value} to {param_name} ({param_id})"
        elif mode.lower() == 'absolutedeparture':
            log_msg = f"Applied absolute departure of {variation_value} to {param_name} ({param_id})"
        elif mode.lower() == 'montecarlo':
            log_msg = f"Applied Monte Carlo variation of {variation_value} to {param_name} ({param_id})"
        else:
            log_msg = f"Applied variation {variation_value} to {param_name} ({param_id})"

        logger.info(log_msg)
        return config_module

    except Exception as e:
        logger.error(f"Error applying sensitivity variation: {str(e)}")
        raise
def generate_sensitivity_configs(config_received, config_matrix_df, results_folder, version,
                                 param_id, mode, variations):
    """
    Generates configuration modules for sensitivity analysis.

    Args:
        config_received: Original configuration
        config_matrix_df: DataFrame with configuration matrix
        results_folder (str): Path to results folder
        version (int): Version number
        param_id (str): Parameter ID
        mode (str): One of 'percentage', 'directvalue', 'absolutedeparture', or 'montecarlo'
        variations (list): List of variation values

    Returns:
        list: Paths to generated configuration files
    """
    logger.info(f"Generating sensitivity configs for {param_id} in {mode} mode")
    config_paths = []

    try:
        base_configs = []

        # First, generate base configurations
        for idx, row in config_matrix_df.iterrows():
            start_year = int(row['start'])
            filtered_values = row['filtered_values']

            # Create base config module
            config_module = {}

            # Verify config copy completion
            config_copy_complete = False
            retry_count = 0
            max_retries = 3

            while not config_copy_complete and retry_count < max_retries:
                try:
                    # Create config module
                    if not isinstance(config_received, dict):
                        for param in dir(config_received):
                            if not param.startswith('__'):
                                config_module[param] = copy.deepcopy(getattr(config_received, param))
                    else:
                        config_module = copy.deepcopy(config_received)

                    # Verify config copy
                    if len(config_module) > 0:
                        config_copy_complete = True
                        logger.info("Config copy verified successfully")
                    else:
                        raise ValueError("Empty config module after copy")
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"Config copy failed (attempt {retry_count}): {str(e)}")
                    if retry_count < max_retries:
                        time.sleep(10)  # Wait 10 seconds before retry
                    else:
                        raise RuntimeError("Failed to create config copy after multiple attempts")

            # Apply filtered values
            if isinstance(filtered_values, str):
                filtered_values = parse_filtered_values(filtered_values)

            # Wait for Flask to stabilize after config copy
            logger.info("Waiting for Flask to stabilize...")
            time.sleep(10)  # 10 sec delay
            logger.info("Flask stabilization period complete")

            for item in filtered_values:
                if item.get('remarks') != "Default entry":
                    config_module[item.get('id')] = strip_value(item.get('value'))

            base_configs.append((start_year, config_module))

        # Generate sensitivity variations based on mode
        if mode.lower() == 'percentage':
            # For percentage mode, we can use first value and create symmetric variations
            if len(variations) > 0:
                variation = variations[0]
                variations_list = [variation, -variation] if variation != 0 else [0]
            else:
                variations_list = []
        else:
            # For other modes, use all provided variations
            variations_list = variations

        # Apply variations and save configurations
        for variation in variations_list:
            for start_year, base_config in base_configs:
                # Create a fresh copy for this variation
                sensitivity_config = copy.deepcopy(base_config)

                # Apply sensitivity variation
                sensitivity_config = apply_sensitivity_variation(
                    sensitivity_config, param_id, variation, mode
                )

                # Save configuration
                config_path = save_sensitivity_config(
                    sensitivity_config,
                    results_folder,
                    version,
                    param_id,
                    mode,
                    variation,
                    start_year
                )
                config_paths.append(config_path)

        return config_paths

    except Exception as e:
        logger.error(f"Error generating sensitivity configurations: {str(e)}")
        raise

def save_sensitivity_config(config_module, results_folder, version, param_id,
                            mode, variation, start_year):
    """
    Saves sensitivity configuration with appropriate naming convention.

    Args:
        config_module (dict): Configuration module
        results_folder (str): Path to results folder
        version (int): Version number
        param_id (str): Parameter ID
        mode (str): One of 'percentage', 'directvalue', 'absolutedeparture', or 'montecarlo'
        variation (float): Variation value
        start_year (int): Start year

    Returns:
        str: Path to saved configuration file
    """
    try:
        # Convert config module to dictionary if it's not already
        if not isinstance(config_module, dict):
            config_dict = {
                param: getattr(config_module, param)
                for param in dir(config_module)
                if not param.startswith('__')
            }
        else:
            config_dict = config_module

        # Map mode to directory structure
        mode_dir_mapping = {
            'percentage': 'percentage',
            'directvalue': 'directvalue',
            'absolutedeparture': 'absolutedeparture',
            'montecarlo': 'montecarlo'
        }

        mode_dir = mode_dir_mapping.get(mode.lower(), 'percentage')  # Default to percentage

        # Create parameter-specific directory structure
        sensitivity_dir = os.path.join(results_folder, 'Sensitivity')
        param_var_dir = os.path.join(
            sensitivity_dir,
            param_id,
            mode_dir,  # Use mapped mode directory
            f"{variation:+.2f}"
        )
        os.makedirs(param_var_dir, exist_ok=True)

        # Generate simplified filename
        filename = f"{version}_config_module_{start_year}.json"
        filepath = os.path.join(param_var_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=4)

        logger.info(f"Saved sensitivity configuration: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error saving sensitivity configuration: {str(e)}")
        raise