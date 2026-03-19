from flask import Flask, request, jsonify
import os
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Original")

def medieval_parse_and_sanitize(content):
    filtered_values_json = []
    filtered_value_objects = []

    # Locate and parse all `filteredValues` and `filteredValue` sections
    filtered_values_matches = list(re.finditer(r'"filteredValues":\s*\[', content))
    filtered_value_matches = list(re.finditer(r'"filteredValue":\s*{', content))
    
    # If neither exists, return empty
    if not filtered_values_matches and not filtered_value_matches:
        return {"filteredValues": filtered_values_json, "filteredValue": filtered_value_objects}

    # Parse all filteredValues arrays if present
    for match in filtered_values_matches:
        filtered_values_start = match.end()
        filtered_values_end = content.find(']', filtered_values_start)
        if filtered_values_end == -1:
            continue

        # Extract the content of this `filteredValues` array
        filtered_values_content = content[filtered_values_start:filtered_values_end]

    # Process all entries within all `filteredValues` arrays
    for match in filtered_values_matches:
        filtered_values_start = match.end()
        filtered_values_end = content.find(']', filtered_values_start)
        if filtered_values_end == -1:
            continue
            
        filtered_values_content = content[filtered_values_start:filtered_values_end]
        
        while True:
            # Parse `id`
            id_start = filtered_values_content.find('"id":"')
            if id_start == -1:
                break
            id_start += len('"id":"')
            id_end = filtered_values_content.find('"', id_start)
            id_value = filtered_values_content[id_start:id_end]

            # Parse `value`
            value_start = filtered_values_content.find('"value":', id_end)
            if value_start == -1:
                break
            value_start += len('"value":')
            value_end = filtered_values_content.find(',', value_start)
            if filtered_values_content[value_start] == '"':
                value_end = filtered_values_content.find('"', value_start + 1) + 1
                value_value = filtered_values_content[value_start:value_end].strip('"')
            else:
                value_end = filtered_values_content.find(',', value_start)
                if value_end == -1:
                    value_end = filtered_values_content.find('}', value_start)
                value_value = filtered_values_content[value_start:value_end].strip()

            # Convert value to number if possible
            try:
                value_value = float(value_value) if '.' in value_value else int(value_value)
            except ValueError:
                pass  # Keep as string if conversion fails

            # Parse `remarks` to capture both "remarks":"" and missing `remarks`
            remarks_match = re.search(r'"remarks":"(.*?)"', filtered_values_content[id_end:])
            if remarks_match:
                remarks_value = remarks_match.group(1).replace("\\\\", "\\")  # Replace double backslashes with single backslash
            else:
                remarks_value = None  # Explicitly set to None if `remarks` is missing

            # Parse start/end times if present, handling both number and string formats
            start_time = None
            end_time = None
            time_match = re.search(r'"start":\s*(["\d]+).*?"end":\s*(["\d]+)', filtered_values_content[id_end:])
            if time_match:
                start_time = int(time_match.group(1).strip('"'))
                end_time = int(time_match.group(2).strip('"'))

            # Append entry to appropriate collection
            if start_time is not None and end_time is not None:
                filtered_value_objects.append({
                    "id": id_value.strip('"'),
                    "value": value_value,
                    "remarks": remarks_value,
                    "start": start_time,
                    "end": end_time
                })
            else:
                filtered_values_json.append({
                    "id": id_value.strip('"'),
                    "value": value_value,
                    "remarks": remarks_value
                })

            # Move to the next item in `filteredValues`
            filtered_values_content = filtered_values_content[value_end:]
    
    # Parse all filteredValue objects (customized parameters with time segments)
    for match in filtered_value_matches:
        # Find the start of the object
        obj_start = match.end()
        # Find the end of the object (the closing brace)
        obj_end = content.find('}', obj_start)
        if obj_end == -1:
            continue
            
        # Extract the content of this filteredValue object
        filtered_value_content = content[obj_start:obj_end]
        
        # Parse id
        id_match = re.search(r'"id":\s*"(.*?)"', filtered_value_content)
        if not id_match:
            continue
        id_value = id_match.group(1)
        
        # Parse value
        value_match = re.search(r'"value":\s*([\d".]+|true|false)', filtered_value_content)
        if not value_match:
            continue
        
        value_str = value_match.group(1)
        # Convert to appropriate type
        if value_str == 'true':
            value_value = True
        elif value_str == 'false':
            value_value = False
        else:
            try:
                value_value = float(value_str) if '.' in value_str else int(value_str.strip('"'))
            except ValueError:
                value_value = value_str.strip('"')
        
        # Parse remarks
        remarks_match = re.search(r'"remarks":\s*"(.*?)"', filtered_value_content)
        remarks_value = remarks_match.group(1) if remarks_match else None
        
        # Parse start and end times
        start_match = re.search(r'"start":\s*(\d+)', filtered_value_content)
        end_match = re.search(r'"end":\s*(\d+)', filtered_value_content)
        
        if start_match and end_match:
            start_time = int(start_match.group(1))
            end_time = int(end_match.group(1))
            
            # Add to the customized parameters collection
            filtered_value_objects.append({
                "id": id_value,
                "value": value_value,
                "remarks": remarks_value,
                "start": start_time,
                "end": end_time
            })
    
    return {"filteredValues": filtered_values_json, "filteredValue": filtered_value_objects}

@app.route('/load_configuration', methods=['POST'])
def load_configuration():
    data = request.get_json()
    version = data.get('version')
    
    if not version:
        return jsonify({"error": "Version is required"}), 400

    original_file_path = os.path.join(UPLOAD_DIR, f'Batch({version})/ConfigurationPlotSpec({version})/U_configurations({version}).py')
    
    try:
        with open(original_file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    except Exception as e:
        return jsonify({"error": f"Error reading from original file: {str(e)}"}), 500

    # Parse and sanitize the content
    parsed_data = medieval_parse_and_sanitize(raw_content)

    # Return both filteredValues and filteredValue collections
    return jsonify(parsed_data)

if __name__ == '__main__':
    app.run(port=5000, debug=True)