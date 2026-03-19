import os
import json
import argparse
import sys
import re

# Hardcoded property mapping
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
    "vAmount55": "v55",
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
}

# Economic metrics list
metrics_list = [
    'Internal Rate of Return',
    'Average Selling Price (Project Life Cycle)',
    'Total Overnight Cost (TOC)',
    'Average Annual Revenue',
    'Average Annual Operating Expenses',
    'Average Annual Depreciation',
    'Average Annual State Taxes',
    'Average Annual Federal Taxes',
    'Average Annual After-Tax Cash Flow',
    'Cumulative NPV',
    'Calculation Mode'
]

def calculate_modified_value(original_value, mode, variation_value):
    """
    Calculate the modified value based on the variation mode and original value.

    Args:
        original_value (float): The original parameter value
        mode (str): The variation mode (percentage, directvalue, absolutedeparture)
        variation_value (float): The variation value

    Returns:
        float: The modified parameter value
    """
    if mode.lower() == 'percentage':
        # For percentage mode, apply percentage change
        return original_value * (1 + variation_value/100)
    elif mode.lower() == 'directvalue':
        # For direct value mode, use variation value directly
        return variation_value
    elif mode.lower() == 'absolutedeparture':
        # For absolute departure mode, add variation to the original value
        return original_value + variation_value
    elif mode.lower() == 'montecarlo':
        # For Monte Carlo mode, use percentage mode logic for now
        return original_value * (1 + variation_value/100)
    else:
        # Default to percentage mode for unknown modes
        return original_value * (1 + variation_value/100)

def format_value(value):
    """Format the value for display in axis labels"""
    if isinstance(value, float):
        # Format as currency for values over 100
        if abs(value) >= 100:
            return f"${value:,.0f}"
        # Format with 2 decimal places for smaller values
        return f"${value:.2f}"
    return str(value)

def get_property_key_for_s_param(s_param):
    """
    Dynamically determine the property key for an S parameter.

    Args:
        s_param (str): S parameter (e.g., "S34")

    Returns:
        str: Property key or None if not found
    """
    # Extract the number part of the S parameter
    match = re.match(r"S(\d+)", s_param)
    if not match:
        return None

    param_num = match.group(1)

    # Special case for S80-S90 parameters (economic metrics)
    if 80 <= int(param_num) <= 90:
        idx = int(param_num) - 80
        if 0 <= idx < len(metrics_list):
            return f"economicMetric{idx}"

    # Special case for S13/S82 equivalence
    if param_num == "13":
        # Map S13 to the same as S82 (special case)
        return get_property_key_for_s_param("S82")

    # Look for matching property keys
    for key in property_mapping.keys():
        if key.endswith(f"Amount{param_num}"):
            return key

    return None

def add_compare_to_key_label(s_param, compare_to_key, property_mapping, datapoints):
    """
    Generate a label for the compareToKey parameter.

    Args:
        s_param (str): The parameter ID (e.g. "S34")
        compare_to_key (str): The comparison key (e.g. "S13")
        property_mapping (dict): Dictionary of property names
        datapoints (dict): Datapoints dictionary

    Returns:
        str: The compareToKey label
    """
    # Special case for economic parameters (S80-S90)
    match = re.match(r"S(\d+)", compare_to_key)
    if match and 80 <= int(match.group(1)) <= 90:
        idx = int(match.group(1)) - 80
        if 0 <= idx < len(metrics_list):
            return metrics_list[idx]
        return compare_to_key

    # Get the property key for the compareToKey
    property_key = get_property_key_for_s_param(compare_to_key)
    if property_key is None or property_key not in property_mapping:
        return compare_to_key

    # Get the presentable name
    presentable_name = property_mapping[property_key]

    # Get baseline value if available
    combined_key = f"{s_param},{compare_to_key}"
    baseline_value = None

    if combined_key in datapoints:
        baseline_data = datapoints[combined_key].get("baseline", {})
        if baseline_data and len(baseline_data) > 0:
            baseline_key = next(iter(baseline_data))
            baseline_value = float(baseline_key)

    # If baseline value is available, include it in the label
    if baseline_value is not None:
        return f"{presentable_name} ({format_value(baseline_value)})"
    else:
        return presentable_name

def add_axis_labels(version):
    """
    Add axis labels to the JSON file based on parameter names and modified values.

    Args:
        version (str): Version number
    """
    # Try different possible locations for the codebase root
    possible_roots = [
        # Current directory method
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        # Hard-coded path as seen in the error
        r"C:\Users\Mohse\IdeaProjects2\codebase",
        # Alternative with backend included
        r"C:\Users\Mohse\IdeaProjects2\codebase\backend"
    ]

    code_files_path = None
    calsen_paths_file = None
    datapoints_file = None

    # Try each possible root until we find the calsen_paths.json file
    for root in possible_roots:
        test_path = os.path.join(root, "Original")
        test_calsen_path = os.path.join(
            test_path,
            f"Batch({version})",
            f"Results({version})",
            "Sensitivity",
            "Reports",
            "calsen_paths.json"
        )

        test_datapoints_path = os.path.join(
            test_path,
            f"Batch({version})",
            f"Results({version})",
            f"SensitivityPlotDatapoints_{version}.json"
        )

        if os.path.exists(test_calsen_path) and os.path.exists(test_datapoints_path):
            code_files_path = test_path
            calsen_paths_file = test_calsen_path
            datapoints_file = test_datapoints_path
            print(f"Found calsen_paths.json at: {calsen_paths_file}")
            print(f"Found datapoints file at: {datapoints_file}")
            break

    if calsen_paths_file is None or datapoints_file is None:
        print("Error: Could not find required files in any of the expected locations")
        return

    # Load calsen_paths.json
    try:
        with open(calsen_paths_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading calsen_paths.json: {e}")
        return

    # Load datapoints file to get baseline values
    try:
        with open(datapoints_file, 'r') as f:
            datapoints = json.load(f)
    except Exception as e:
        print(f"Error loading datapoints file: {e}")
        return

    # Keep track of processed parameters
    processed_params = 0
    skipped_params = 0

    # Group parameters by their compareToKey for plot organization
    param_groups = {}

    # First pass: collect all parameters and their compareToKeys
    for s_param, param_data in data["path_sets"].items():
        compare_to_key = param_data.get("compareToKey", "S13")
        if compare_to_key not in param_groups:
            param_groups[compare_to_key] = []
        param_groups[compare_to_key].append(s_param)

    # Process each key in path_sets
    for s_param, param_data in data["path_sets"].items():
        # Get the compare to key
        compare_to_key = param_data.get("compareToKey", "S13")
        combined_key = f"{s_param},{compare_to_key}"

        # Check if this is an economic parameter (S80-S90)
        is_economic_param = False
        match = re.match(r"S(\d+)", s_param)
        if match and 80 <= int(match.group(1)) <= 90:
            is_economic_param = True
            idx = int(match.group(1)) - 80
            if 0 <= idx < len(metrics_list):
                presentable_name = metrics_list[idx]
            else:
                print(f"Warning: Economic index out of range for {s_param}")
                skipped_params += 1
                continue
        else:
            # Get the parameter name from mapping
            property_key = get_property_key_for_s_param(s_param)
            if property_key is None:
                print(f"Warning: Could not determine property key for {s_param}")
                skipped_params += 1
                continue

            if property_key not in property_mapping:
                print(f"Warning: No property mapping found for {property_key}")
                skipped_params += 1
                continue

            # Get the presentable name
            presentable_name = property_mapping[property_key]

        # Get the mode
        mode = param_data["mode"]

        # Get baseline value from datapoints file
        baseline_value = None
        if combined_key in datapoints:
            baseline_data = datapoints[combined_key].get("baseline", {})
            if baseline_data and len(baseline_data) > 0:
                baseline_key = next(iter(baseline_data))
                baseline_value = float(baseline_key)
                print(f"Found baseline value {baseline_value} for {s_param}")

        if baseline_value is None:
            print(f"Warning: No baseline value found for {s_param}. Using fallback.")
            # Fallback value
            baseline_value = 1000

        # Check if compareToKey is an economic parameter (S80-S90)
        compare_to_key_is_economic = False
        match = re.match(r"S(\d+)", compare_to_key)
        if match and 80 <= int(match.group(1)) <= 90:
            compare_to_key_is_economic = True

        # Special handling for different plot types
        if is_economic_param or compare_to_key_is_economic:
            # For economic parameters, the axis labels will be the metric names
            # The plot coordinates will be (metric value, variation value) pairs

            # Process for economic parameter as Y-axis
            if is_economic_param:
                axis_label = presentable_name

                # Create a list of coordinate pairs separately - not part of the label
                plot_coordinates = []

                # We need to use the variations as defined in the path_sets, in their original order
                variation_values = []
                for var_str, var_data in param_data["variations"].items():
                    variation_value = var_data["variation"]

                    # Calculate the modified value
                    modified_value = calculate_modified_value(baseline_value, mode, variation_value)

                    # Add to variations list
                    variation_values.append(format_value(modified_value))

                    # Save this for plot coordinates
                    if "metrics" in var_data:
                        # Use the metric corresponding to this S param if available
                        if presentable_name in var_data["metrics"]:
                            metric_value = var_data["metrics"][presentable_name]
                            # Remove currency symbols and commas
                            if isinstance(metric_value, str):
                                metric_value = metric_value.replace('$', '').replace(',', '')
                                # Convert percentage to decimal
                                if '%' in metric_value:
                                    metric_value = float(metric_value.replace('%', '')) / 100
                                else:
                                    try:
                                        metric_value = float(metric_value)
                                    except ValueError:
                                        continue

                            # Add coordinate pair (modified_value, metric_value)
                            plot_coordinates.append({
                                "x": modified_value,
                                "y": metric_value,
                                "label": var_str
                            })

                # Create the axis label string without the values in parentheses
                # since this will be a Y-tick label with discrete levels
                axis_label = presentable_name

                # Store the plot coordinates separately
                param_data["plotCoordinates"] = plot_coordinates

            # Process for economic parameter as compareToKey (X-axis)
            elif compare_to_key_is_economic:
                # Get the metric name from the compareToKey
                idx = int(match.group(1)) - 80
                metric_name = metrics_list[idx] if 0 <= idx < len(metrics_list) else compare_to_key

                # Create a list of coordinate pairs separately
                plot_coordinates = []

                # We need to use the variations as defined in the path_sets, in their original order
                variation_values = []
                for var_str, var_data in param_data["variations"].items():
                    variation_value = var_data["variation"]

                    # Calculate the modified value for this variation
                    modified_value = calculate_modified_value(baseline_value, mode, variation_value)

                    # Format and add to variations list
                    variation_values.append(format_value(modified_value))

                    # For each variation, find the corresponding metric value
                    if "metrics" in var_data:
                        if metric_name in var_data["metrics"]:
                            metric_value = var_data["metrics"][metric_name]
                            # Remove currency symbols and commas
                            if isinstance(metric_value, str):
                                metric_value = metric_value.replace('$', '').replace(',', '')
                                # Convert percentage to decimal
                                if '%' in metric_value:
                                    metric_value = float(metric_value.replace('%', '')) / 100
                                else:
                                    try:
                                        metric_value = float(metric_value)
                                    except ValueError:
                                        continue

                            # Add coordinate pair (metric_value, modified_value)
                            plot_coordinates.append({
                                "x": metric_value,
                                "y": modified_value,
                                "label": var_str
                            })

                # Create the axis label with variations in parentheses
                axis_label = presentable_name + " (" + ", ".join(variation_values) + ")"

                # Store the plot coordinates separately
                param_data["plotCoordinates"] = plot_coordinates
        else:
            # Traditional S-parameters (up to S79)
            # Create the variations list in the order they appear in the JSON
            variation_values = []

            # Get data points to determine the actual modified values
            data_points = {}
            if combined_key in datapoints:
                data_points = datapoints[combined_key].get("data", {})

            # We need to use the variations as defined in the path_sets, in their original order
            for var_str, var_data in param_data["variations"].items():
                variation_value = var_data["variation"]

                # Find the modified value in the datapoints or calculate it
                modified_value = None

                # Try to find in datapoints
                for point_key in data_points:
                    # Convert both to float for comparison
                    try:
                        calculated_value = calculate_modified_value(baseline_value, mode, variation_value)
                        point_value = float(point_key)
                        # Use a small epsilon for float comparison
                        if abs(calculated_value - point_value) < 0.001 * abs(point_value):
                            modified_value = point_value
                            break
                    except (ValueError, TypeError):
                        continue

                # If not found, calculate it
                if modified_value is None:
                    modified_value = calculate_modified_value(baseline_value, mode, variation_value)

                # Add to variations list
                variation_values.append(format_value(modified_value))

                # Store coordinates separately for plotting
                if "metrics" in var_data:
                    # For standard parameters, coordinates are (modified_value, metric_value) pairs
                    # where metric_value is the appropriate economic metric
                    # This allows plotting the economic impact of parameter variations
                    coords = []
                    for metric_name, metric_value in var_data["metrics"].items():
                        # Clean the metric value
                        if isinstance(metric_value, str):
                            clean_value = metric_value.replace('$', '').replace(',', '')
                            # Convert percentage to decimal
                            if '%' in clean_value:
                                clean_value = float(clean_value.replace('%', '')) / 100
                            else:
                                try:
                                    clean_value = float(clean_value)
                                except ValueError:
                                    continue

                            coords.append({
                                "x": modified_value,
                                "y": clean_value,
                                "metric": metric_name,
                                "label": var_str
                            })

                    if not hasattr(var_data, "plotCoordinates"):
                        var_data["plotCoordinates"] = []
                    var_data["plotCoordinates"] = coords

            # Create the axis label string with variations in parentheses
            axis_label = presentable_name + " (" + ", ".join(variation_values) + ")"

        # Generate compareToKey label
        compare_to_key_label = add_compare_to_key_label(s_param, compare_to_key, property_mapping, datapoints)

        # Add the axis_label to the parameter data, right before compareToKey
        ordered_keys = list(param_data.keys())
        compare_to_key_index = ordered_keys.index("compareToKey") if "compareToKey" in ordered_keys else 0

        # Create a new ordered dictionary with axisLabel inserted at the right position
        new_param_data = {}
        for i, key in enumerate(ordered_keys):
            if i == compare_to_key_index:
                new_param_data["axisLabel"] = axis_label
                new_param_data["compareToKeyLabel"] = compare_to_key_label
            new_param_data[key] = param_data[key]

        # Replace the original parameter data with the new one
        data["path_sets"][s_param] = new_param_data
        processed_params += 1
        print(f"Added axis label for {s_param}: {axis_label}")

    # Add plot grouping information based on compareToKey relationships
    data["plotGroups"] = param_groups

    # Save the updated JSON
    try:
        with open(calsen_paths_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully updated {calsen_paths_file}")
        print(f"Processed {processed_params} parameters, skipped {skipped_params} parameters")
    except Exception as e:
        print(f"Error saving {calsen_paths_file}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add axis labels to JSON file')
    parser.add_argument('version', type=str, help='Version number (e.g. "4")')

    args = parser.parse_args()
    add_axis_labels(args.version)