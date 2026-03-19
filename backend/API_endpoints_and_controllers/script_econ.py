import os
import json
import csv
import argparse
import sys


def extract_metrics_to_json(version):
    """
    Extract metrics from Economic Summary CSV files based on selection vector
    and append them to calsen_paths.json.

    Args:
        version (str): Version number
    """
    # Define metric selection vector - 1 means select, 0 means ignore
    metrics_selection = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # Define your selection vector here

    # Define metrics list for reference
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

    # Calculate code_files_path based on the script's location
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    code_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))), "codebase",
                                   "backend", "Original")

    # Load calsen_paths.json
    sensitivity_dir = os.path.join(
        code_files_path,
        f"Batch({version})",
        f"Results({version})",
        "Sensitivity"
    )
    reports_dir = os.path.join(sensitivity_dir, "Reports")
    calsen_paths_file = os.path.join(reports_dir, "calsen_paths.json")

    try:
        with open(calsen_paths_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {calsen_paths_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not parse {calsen_paths_file} as JSON")
        return

    # Process each key in path_sets
    for s_param, param_data in data["path_sets"].items():
        mode_dir_name = param_data["mode"]

        # Process each variation
        for var_str, var_data in param_data["variations"].items():
            # Construct path to the Economic Summary CSV file
            economic_summary_file = os.path.join(
                code_files_path,
                f"Batch({version})",
                f"Results({version})",
                "Sensitivity",
                s_param,
                mode_dir_name,
                "Configuration",
                f"{s_param}_{var_str}",
                f"Economic_Summary({version}).csv"
            )

            # Check if file exists
            if not os.path.exists(economic_summary_file):
                print(f"Warning: File not found: {economic_summary_file}")
                continue

            # Read the CSV file
            try:
                with open(economic_summary_file, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    rows = list(reader)

                    # Extract selected metrics based on the selection vector
                    selected_metrics = {}
                    for i, selected in enumerate(metrics_selection):
                        if selected == 1 and i < len(rows):
                            if len(rows[i]) >= 2:  # Ensure row has at least two columns
                                metric_name = rows[i][0]
                                metric_value = rows[i][1]
                                selected_metrics[metric_name] = metric_value

                    # Add selected metrics to the JSON
                    if selected_metrics:
                        var_data["metrics"] = selected_metrics

            except Exception as e:
                print(f"Error processing {economic_summary_file}: {e}")

    # Save the updated JSON
    try:
        with open(calsen_paths_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully updated {calsen_paths_file}")
    except Exception as e:
        print(f"Error saving {calsen_paths_file}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=str, required=True, help='Version number')
    args = parser.parse_args()

    # Call the function with the version argument
    extract_metrics_to_json(args.version)


if __name__ == '__main__':
    main()
