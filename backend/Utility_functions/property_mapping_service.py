# backend/property_mapping_service.py
from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes in the application

# Define the blueprint
property_mapping_bp = Blueprint('property_mapping', __name__)

@property_mapping_bp.route('/update_property_mapping', methods=['POST'])
def update_property_mapping():
    try:
        data = request.get_json()
        new_mapping = data.get('property_mapping')
        
        if not new_mapping:
            return jsonify({'error': 'No property mapping provided'}), 400

        file_path = os.path.join(os.path.dirname(__file__), 'common_utils.py')
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        start_marker = 'property_mapping = {'
        start_idx = content.find(start_marker)
        if start_idx == -1:
            return jsonify({'error': 'Could not find property_mapping in file'}), 500
            
        brace_count = 1
        end_idx = start_idx + len(start_marker)
        while brace_count > 0 and end_idx < len(content):
            if content[end_idx] == '{':
                brace_count += 1
            elif content[end_idx] == '}':
                brace_count -= 1
            end_idx += 1

        if brace_count != 0:
            return jsonify({'error': 'Invalid file format'}), 500

        new_mapping_str = 'property_mapping = ' + json.dumps(new_mapping, indent=4)
        updated_content = content[:start_idx] + new_mapping_str + content[end_idx:]
        
        with open(file_path + '.backup', 'w', encoding='utf-8') as backup_file:
            backup_file.write(content)
            
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            
        return jsonify({'message': 'Property mapping updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@property_mapping_bp.route('/update_frontend_mapping', methods=['POST'])
def update_frontend_mapping():
    try:
        data = request.get_json()
        new_mapping = data.get('property_mapping')
        file_path = data.get('file_path')
        
        if not new_mapping or not file_path:
            return jsonify({'error': 'Missing required data'}), 400

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Find the propertyMapping object in the content
        start_marker = 'const propertyMapping = {'
        start_idx = content.find(start_marker)
        if start_idx == -1:
            return jsonify({'error': 'Could not find propertyMapping in file'}), 500
            
        brace_count = 1
        end_idx = start_idx + len(start_marker)
        while brace_count > 0 and end_idx < len(content):
            if content[end_idx] == '{':
                brace_count += 1
            elif content[end_idx] == '}':
                brace_count -= 1
            end_idx += 1

        if brace_count != 0:
            return jsonify({'error': 'Invalid file format'}), 500

        # Create backup of the frontend file
        with open(file_path + '.backup', 'w', encoding='utf-8') as backup_file:
            backup_file.write(content)

        # Create the new mapping string
        new_mapping_str = 'const propertyMapping = ' + json.dumps(new_mapping, indent=2)
        
        # Replace the old mapping with the new one
        updated_content = content[:start_idx] + new_mapping_str + content[end_idx:]
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            
        return jsonify({'message': 'Frontend property mapping updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# Register the blueprint with the app
app.register_blueprint(property_mapping_bp)

if __name__ == '__main__':
    app.run(port=5010)  # Using a new port