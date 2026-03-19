import os
import json
import pandas as pd
import sys
import importlib.util
import shutil
import logging
from pathlib import Path
# Import using a proper relative import syntax
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utility_functions.common_utils import property_mapping

# Get the directory where this script is located
script_dir = Path(__file__).resolve().parent.parent
uploads_dir = script_dir.parent / "Original"
code_files_path = uploads_dir  # Maintain the same variable name for compatibility

# Initialize logging
log_file_path = Path(os.getcwd()) / 'module.log'
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s %(message)s')

# Rest of the code remains exactly the same as in the original file
def apply_property_mapping(filtered_value_intervals):
    mapped_intervals = []
    for interval in filtered_value_intervals:
        interval_id = interval[0]
        if interval_id in property_mapping:
            interval_list = list(interval)
            interval_list[0] = property_mapping[interval_id]
            mapped_intervals.append(tuple(interval_list))
        else:
            mapped_intervals.append(interval)
    return mapped_intervals

def apply_filtered_values_and_build_matrix(config_received, filtered_values_json):
    filtered_values = [json.loads(item) for item in filtered_values_json]
    filtered_value_intervals = []
    logging.info(f"filtered_values: {filtered_values}")

    start_end_points = set()
    start_end_points.update([1, config_received.plantLifetimeAmount10])
    general_year_sorted_list = list(range(1, config_received.plantLifetimeAmount10 + 2))
    logging.info(f"general_year_sorted_list: {general_year_sorted_list}")

    for value in filtered_values:
        if isinstance(value, dict) and 'filteredValue' in value:
            fv = value['filteredValue']
            if 'id' in fv and 'value' in fv and 'start' in fv and 'end' in fv:
                start_year = int(fv['start'])
                end_year = int(fv['end'])
                start_end_points.update([start_year, end_year])
                logging.info(f"start_end_points: {start_end_points}")
                if 'remarks' in fv:
                    filtered_value_intervals.append((fv['id'], start_year, end_year, fv['value'], fv['remarks']))
                else:
                    filtered_value_intervals.append((fv['id'], start_year, end_year, fv['value']))

    sorted_points = sorted(start_end_points)
    logging.info(f"sorted_points: {sorted_points}")
    intervals = [(sorted_points[i], sorted_points[i + 1]) for i in range(len(sorted_points) - 1)]
    general_intervals = [(general_year_sorted_list[i], general_year_sorted_list[i + 1]) for i in range(len(general_year_sorted_list) - 1)]
    logging.info(f"general_intervals: {general_intervals}")
    logging.info(f"intervals: {intervals}")

    config_matrix = []
    for start, end in intervals:
        length = end - start
        config_matrix.append({
            'start': start,
            'end': end,
            'length': length+1,
            'filtered_values': []
        })
    
    general_config_matrix = []
    for start, end in general_intervals:
        length = end - start
        general_config_matrix.append({
            'start': start,
            'end': end-1,
            'length': length,
            'filtered_values': []
        })

    # Keep the rest of the function exactly as it is in the original
    for fv_tuple in filtered_value_intervals:
        fv_id = fv_tuple[0]
        hs = fv_tuple[1]
        he = fv_tuple[2]
        value = fv_tuple[3]
        remarks = fv_tuple[4] if len(fv_tuple) > 4 else None
        logging.info(f"fv_tuple: {fv_tuple[1]}")
        for row in config_matrix:
            if hs > row['end']:
                continue
            if he < row['start']:
                continue
            item = {"id": fv_id, "value": value}
            if remarks:
                item["remarks"] = remarks
            row['filtered_values'].append(item)

    for fv_tuple in filtered_value_intervals:
        fv_id = fv_tuple[0]
        hs = fv_tuple[1]
        he = fv_tuple[2]
        value = fv_tuple[3]
        remarks = fv_tuple[4] if len(fv_tuple) > 4 else None
        logging.info(f"fv_tuple: {fv_tuple[1]}")
        for row in general_config_matrix:
            if hs > row['end']:
                continue
            if he < row['start']:
                continue
            item = {"id": fv_id, "value": value}
            if remarks:
                item["remarks"] = remarks
            row['filtered_values'].append(item)

    for row in config_matrix:
        row['filtered_values'] = json.dumps(row['filtered_values'], indent=None)
    
    for row in general_config_matrix:
        row['filtered_values'] = json.dumps(row['filtered_values'], indent=None)

    filtered_value_intervals = apply_property_mapping(filtered_value_intervals)
    return config_matrix, sorted_points, filtered_value_intervals, general_config_matrix

def empty_folder(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = Path(folder_path) / filename
            try:
                if file_path.is_file() or file_path.is_symlink():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

def test_list_building(version, extension, config_received):
    filtered_values_json = config_received.filtered_values_json
    config_matrix, sorted_points, filtered_value_intervals, general_config_matrix = apply_filtered_values_and_build_matrix(config_received, filtered_values_json)

    results_folder = code_files_path / f"Batch({version}.{extension})" / f"Results({version})"
    results_folder.mkdir(parents=True, exist_ok=True)

    empty_folder(results_folder)

    # Use Path for file paths
    config_matrix_file = results_folder / f"Configuration_Matrix({version}).csv"
    sorted_points_file = results_folder / f"Sorted_Points({version}).csv"
    filtered_value_intervals_file = results_folder / f"Filtered_Value_Intervals({version}).csv"
    general_config_matrix_file = results_folder / f"General_Configuration_Matrix({version}).csv"

    config_matrix_df = pd.DataFrame(config_matrix)
    config_matrix_df.to_csv(config_matrix_file, index=False)
    
    general_config_matrix_df = pd.DataFrame(general_config_matrix)
    general_config_matrix_df.to_csv(general_config_matrix_file, index=False)

    sorted_points_df = pd.DataFrame(sorted_points, columns=["Points"])
    sorted_points_df.to_csv(sorted_points_file, index=False)

    filtered_value_intervals_df = pd.DataFrame(filtered_value_intervals, columns=["ID", "Start", "End", "Value", "Remarks"])
    filtered_value_intervals_df.to_csv(filtered_value_intervals_file, index=False)

    print("Config Matrix:")
    print(config_matrix_df)
    print("Sorted Points:")
    print(sorted_points_df)
    print("Filtered Value Intervals:")
    print(filtered_value_intervals_df)

# Get version and extension from command line if provided
version = sys.argv[1] if len(sys.argv) > 1 else 1
extension = sys.argv[2] if len(sys.argv) > 2 else 1

if str(code_files_path) not in sys.path:
    sys.path.append(str(code_files_path))

config_file = code_files_path / f"Batch({version}.{extension})" / f"ConfigurationPlotSpec({version})" / f"configurations({version}).py"
spec = importlib.util.spec_from_file_location("config", str(config_file))
config_received = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_received)

test_list_building(version, extension, config_received)
