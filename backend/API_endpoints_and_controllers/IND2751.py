from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import json
import re
import importlib.util
import sys
import copy

# Setup Flask app
app = Flask(__name__)
CORS(app)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('standalone_sensitivity_namer')

# Constants
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
UTILITY_FUNCTIONS_DIR = os.path.join(BACKEND_DIR, 'Utility_functions')
ORIGINAL_BASE_DIR = os.path.join(BACKEND_DIR, 'Original')

# Import helpers from sensitivity module
sys.path.append(BACKEND_DIR)
from Sen_Config import apply_sensitivity_variation, find_parameter_by_id

def extract_property_mapping():
    path = os.path.join(UTILITY_FUNCTIONS_DIR, 'common_utils.py')
    property_mapping = {}
    try:
        with open(path, 'r') as f:
            content = f.read()
        match = re.search(r'property_mapping\s*=\s*{([^}]*)}', content, re.DOTALL)
        if match:
            entries = re.findall(r'"([^"]+)":\s*"([^"]+)"', match.group(1))
            for k, v in entries:
                property_mapping[k] = v
    except Exception as e:
        logger.warning(f"Failed to read property_mapping: {e}")
    return property_mapping

def generate_display_names(version):
    reports_dir = os.path.join(ORIGINAL_BASE_DIR, f'Batch({version})', f'Results({version})', 'Sensitivity', 'Reports')
    calsen_path = os.path.join(reports_dir, 'calsen_paths.json')

    if not os.path.exists(calsen_path):
        return {"error": f"Missing calsen_paths.json at {calsen_path}"}

    try:
        with open(calsen_path, 'r') as f:
            data = json.load(f)

        path_sets = data.get("path_sets", {})
        property_mapping = extract_property_mapping()

        parameter_names = {}

        for param_id, info in path_sets.items():
            if not param_id.startswith('S') or not param_id[1:].isdigit():
                continue

            num = param_id[1:]
            name = property_mapping.get(f"vAmount{num}", property_mapping.get(f"rAmount{num}", f"Parameter {num}"))
            mode = info.get('mode', 'percentage')
            variations = info.get('variations', {})
            variation_labels = {}
            var_strs = []

            config_path = next((v.get('config_file') for v in variations.values() if v.get('config_file')), None)
            config_dict = {}
            if config_path and os.path.exists(config_path):
                spec = importlib.util.spec_from_file_location("config", config_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                config_dict = {k: getattr(mod, k) for k in dir(mod) if not k.startswith("__")}

            for k, v in variations.items():
                delta = v.get("variation")
                var_str = v.get("variation_str", f"{delta:+.2f}")
                var_strs.append(var_str)

                try:
                    if config_dict:
                        temp = copy.deepcopy(config_dict)
                        key = find_parameter_by_id(temp, param_id)
                        temp = apply_sensitivity_variation(temp, param_id, delta, mode)
                        mod_val = temp[key]
                        mod_str = f"{mod_val:.2f}" if isinstance(mod_val, (int, float)) else str(mod_val)
                        variation_labels[var_str] = f"{name} ({var_str}, {mod_str})"
                    else:
                        variation_labels[var_str] = f"{name} ({var_str})"
                except Exception as e:
                    variation_labels[var_str] = f"{name} ({var_str})"
                    logger.warning(f"Failed to modify value for {param_id}: {e}")

            full_name = f"{name} ({', '.join(var_strs)})"
            parameter_names[param_id] = {
                "display_name": full_name,
                "base_name": name,
                "variations": variation_labels
            }

        data["parameter_names"] = parameter_names
        with open(calsen_path, 'w') as f:
            json.dump(data, f, indent=2)

        return {"status": "success", "parameter_names": parameter_names}

    except Exception as e:
        logger.error(f"Failed processing version {version}: {e}")
        return {"error": str(e)}

@app.route('/inject-names', methods=['POST'])
def inject_names():
    req = request.get_json()
    version = req.get("version")
    if not version:
        return jsonify({"error": "Missing 'version' field"}), 400
    return jsonify(generate_display_names(version))

if __name__ == "__main__":
    app.run(port=2751, debug=True)
