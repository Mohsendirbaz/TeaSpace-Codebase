import os
import json
import argparse
import sys
import shutil
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

def create_png_plot(plot_data, output_path):
    """
    Create a PNG plot from the plot data.

    Args:
        plot_data (dict): The plot data
        output_path (str): The output path for the PNG file
    """
    # Extract plot data
    x_param = plot_data["x_param"]
    y_param = plot_data["y_param"]
    plot_type = plot_data["plot_type"]
    axis_label = plot_data["axis_label"]
    baseline_data = plot_data["datapoints"]["baseline"]
    variations_data = plot_data["datapoints"]["variations"]

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Set title and labels
    ax.set_title(f"{y_param} vs {x_param} ({plot_type})")
    ax.set_xlabel(x_param)
    ax.set_ylabel(axis_label)

    # Plot baseline data if available
    if baseline_data:
        x_values = [float(x) for x in baseline_data.keys()]
        y_values = [float(y) for y in baseline_data.values()]
        ax.plot(x_values, y_values, 'o-', label='Baseline', color='blue')

    # Plot variations data if available
    if variations_data:
        x_values = [float(x) for x in variations_data.keys()]
        y_values = [float(y) for y in variations_data.values()]

        # Different plot types
        if plot_type == "point":
            ax.scatter(x_values, y_values, label='Variations', color='red', s=50)
        elif plot_type == "bar":
            ax.bar(x_values, y_values, label='Variations', color='green', alpha=0.7)
        elif plot_type == "waterfall":
            # For waterfall, connect points with lines
            ax.plot(x_values, y_values, 's-', label='Variations', color='purple')
        else:
            # Default to line plot
            ax.plot(x_values, y_values, 'o-', label='Variations', color='red')

    # Add grid and legend
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()

    # Adjust layout
    plt.tight_layout()

    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"  Created PNG plot: {output_path}")

def generate_plots(version):
    """
    Generate plot algorithm for sensitivity analysis.

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

        if os.path.exists(test_calsen_path):
            code_files_path = test_path
            calsen_paths_file = test_calsen_path
            print(f"Found calsen_paths.json at: {calsen_paths_file}")
            break

    if calsen_paths_file is None:
        print("Error: Could not find calsen_paths.json in any of the expected locations")
        return

    # Load calsen_paths.json
    try:
        with open(calsen_paths_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading calsen_paths.json: {e}")
        return

    # Get SenParameters from payload
    sen_parameters = data["payload"]["SenParameters"]

    # Override all comparisonTypes to "primary (x axis)"
    for s_param, param_data in data["path_sets"].items():
        param_data["comparisonType"] = "primary (x axis)"

    # Group parameters by their compareToKey
    param_groups = {}

    # Process parameters in order to maintain proper plot sequence
    param_order = []
    for s_param, param_data in data["path_sets"].items():
        compare_to_key = param_data.get("compareToKey", "")
        if compare_to_key:
            if compare_to_key not in param_groups:
                param_groups[compare_to_key] = []
                param_order.append(compare_to_key)
            param_groups[compare_to_key].append(s_param)

    # Create plots based on parameter groups
    plots = []
    for i, compare_to_key in enumerate(param_order):
        group_params = param_groups[compare_to_key]

        # Create a plot for each group
        plot = {
            "plot_id": f"plot_{i+1}",
            "x_param": compare_to_key,
            "y_params": group_params,
            "plot_types": []
        }

        # Determine plot types for each parameter (bar, point, waterfall)
        for s_param in group_params:
            if s_param in sen_parameters:
                param_config = sen_parameters[s_param]
                if param_config.get("bar", False):
                    plot["plot_types"].append("bar")
                if param_config.get("point", False):
                    plot["plot_types"].append("point")
                if param_config.get("waterfall", False):
                    plot["plot_types"].append("waterfall")

        # Remove duplicates
        plot["plot_types"] = list(set(plot["plot_types"]))

        plots.append(plot)

    # Base output directory
    output_base_dir = os.path.join(
        code_files_path,
        f"Batch({version})",
        f"Results({version})",
        "Sensitivity"
    )

    # Create plot files
    created_plots = 0

    for plot in plots:
        plot_id = plot["plot_id"]
        x_param = plot["x_param"]
        y_params = plot["y_params"]
        plot_types = plot["plot_types"]

        print(f"\nGenerating {plot_id}:")
        print(f"  X-axis parameter: {x_param}")
        print(f"  Y-axis parameters: {', '.join(y_params)}")
        print(f"  Plot types: {', '.join(plot_types)}")

        # Get the data points for each parameter
        for plot_type in plot_types:
            # Capitalize plot type for directory
            plot_type_dir = plot_type.capitalize()

            for y_param in y_params:
                # Get the mode from the parameter data
                if y_param in data["path_sets"]:
                    param_data = data["path_sets"][y_param]
                    mode = param_data.get("mode", "")

                    # Capitalize mode for directory
                    mode_dir = mode.capitalize()

                    # Create directory path
                    plot_dir = os.path.join(output_base_dir, mode_dir, plot_type_dir)
                    os.makedirs(plot_dir, exist_ok=True)

                    # Create plot file name
                    plot_file_name = f"{y_param}_{x_param}_plot.json"
                    plot_file_path = os.path.join(plot_dir, plot_file_name)

                    # Create the plot data
                    plot_data = {
                        "x_param": x_param,
                        "y_param": y_param,
                        "plot_type": plot_type,
                        "mode": mode,
                        "axis_label": param_data.get("axisLabel", f"{y_param} vs {x_param}"),
                        "compare_to_key": x_param,
                        "comparison_type": "primary (x axis)",
                        "datapoints": {
                            "baseline": {},
                            "variations": {}
                        }
                    }

                    # Check if plotCoordinates are available in the parameter data
                    if "plotCoordinates" in param_data:
                        # Use plotCoordinates from calsen_paths.json
                        plot_coordinates = param_data["plotCoordinates"]

                        # Process coordinates for plot data
                        for coord in plot_coordinates:
                            if "x" in coord and "y" in coord:
                                # For variations, use the label if available
                                label = coord.get("label", "")
                                if label:
                                    # Add to variations
                                    plot_data["datapoints"]["variations"][str(coord["x"])] = coord["y"]
                                else:
                                    # Add to baseline if no label (assuming it's baseline)
                                    plot_data["datapoints"]["baseline"][str(coord["x"])] = coord["y"]

                        print(f"  Using plotCoordinates from calsen_paths.json for {y_param}")
                    else:
                        # Check if variations have plotCoordinates
                        has_coordinates = False
                        for var_str, var_data in param_data.get("variations", {}).items():
                            if "plotCoordinates" in var_data:
                                has_coordinates = True
                                # Process coordinates for this variation
                                for coord in var_data["plotCoordinates"]:
                                    if "x" in coord and "y" in coord:
                                        # Add to variations
                                        plot_data["datapoints"]["variations"][str(coord["x"])] = coord["y"]

                        if has_coordinates:
                            print(f"  Using variation plotCoordinates from calsen_paths.json for {y_param}")
                        else:
                            print(f"  Warning: No plotCoordinates found for {y_param}")

                            # If no plotCoordinates are available, create empty plot data
                            # This ensures the plot file is still created even without data
                            plot_data["datapoints"] = {
                                "baseline": {},
                                "variations": {}
                            }

                    # Save the plot data as JSON
                    try:
                        with open(plot_file_path, 'w') as f:
                            json.dump(plot_data, f, indent=2)
                        print(f"  Created JSON plot file: {plot_file_path}")
                        created_plots += 1

                        # Also create PNG plot
                        # Create PNG directory structure
                        png_dir = os.path.join(output_base_dir, mode_dir, plot_type_dir, "PNG")
                        os.makedirs(png_dir, exist_ok=True)

                        # Create PNG file name
                        png_file_name = f"{y_param}_{x_param}_plot.png"
                        png_file_path = os.path.join(png_dir, png_file_name)

                        # Generate PNG plot
                        create_png_plot(plot_data, png_file_path)
                        created_plots += 1
                    except Exception as e:
                        print(f"  Error saving plot files: {e}")

    # Save the updated calsen_paths.json with the comparisonType changes
    try:
        with open(calsen_paths_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nSuccessfully updated {calsen_paths_file} with comparisonType changes")
    except Exception as e:
        print(f"Error saving {calsen_paths_file}: {e}")

    # Calculate the number of JSON and PNG files (half of total created_plots)
    json_count = created_plots // 2
    png_count = created_plots // 2

    print(f"\nPlot generation complete. Created {json_count} JSON and {png_count} PNG plot files using coordinate points from calsen_paths.json.")
    print(f"PNG files are available in the PNG subdirectories and can be displayed in the plot gallery and sensitivity tabs.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate plots for sensitivity analysis')
    parser.add_argument('version', type=str, help='Version number (e.g. "4")')

    args = parser.parse_args()
    generate_plots(args.version)
