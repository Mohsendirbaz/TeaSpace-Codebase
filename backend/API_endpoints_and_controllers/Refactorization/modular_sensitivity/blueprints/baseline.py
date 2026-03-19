from flask import Blueprint, jsonify, request
import time
import os
import json
import subprocess
from config import LOGS_DIR, BASELINE_LOCK_FILE, COMMON_PYTHON_SCRIPTS, CALCULATION_SCRIPTS
from state import GLOBAL_BASELINE_LOCK, BASELINE_COMPLETED, PAYLOAD_REGISTERED
from decorators import with_file_lock, with_memory_lock, with_pipeline_check
from utils import atomic_read_json, atomic_write_json

baseline_bp = Blueprint('baseline', __name__)

@baseline_bp.route('/baseline_calculation', methods=['POST'])
@with_file_lock(BASELINE_LOCK_FILE, "baseline calculation")
@with_memory_lock(GLOBAL_BASELINE_LOCK, "baseline calculation")
@with_pipeline_check(required_event=PAYLOAD_REGISTERED, next_event=BASELINE_COMPLETED, operation_name="baseline calculation")
def baseline_calculation():
    """Perform baseline calculation without sensitivity variations"""
    try:
        data = request.get_json()
        run_id = data.get('runId')

        # If no runtime data provided but runId is present, try to load from stored payload
        if run_id and (not data.get('selectedVersions') or not data.get('selectedCalculationOption')):
            payload_path = os.path.join(LOGS_DIR, f"payload_{run_id}.json")
            if os.path.exists(payload_path):
                stored_data = atomic_read_json(payload_path)
                if stored_data:
                    data.update(stored_data)

        # Extract configuration
        version = data.get('selectedVersions', [1])[0]
        selectedV = data.get('selectedV', {f'V{i+1}': 'off' for i in range(10)})
        selectedF = data.get('selectedF', {f'F{i+1}': 'off' for i in range(5)})
        calculation_option = data.get('selectedCalculationOption', 'freeFlowNPV')
        target_row = int(data.get('targetRow', 20))

        # Get calculation script
        calculation_script_func = CALCULATION_SCRIPTS.get(calculation_option)
        if not calculation_script_func:
            BASELINE_COMPLETED.clear()  # Reset baseline completion flag
            return jsonify({
                "error": f"No script found for calculation mode: {calculation_option}",
                "status": "error"
            }), 400

        calculation_script = calculation_script_func(version)

        # Execute configuration management scripts first
        for script in COMMON_PYTHON_SCRIPTS:
            script_name = os.path.basename(script)

            result = subprocess.run(
                ['python', script, str(version)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = f"Script execution failed: {script_name}\nError: {result.stderr}"
                BASELINE_COMPLETED.clear()  # Reset baseline completion flag
                return jsonify({
                    "error": error_msg,
                    "status": "error"
                }), 500

            time.sleep(0.5)  # Ensure proper sequencing

        # Run baseline calculation
        start_time = time.time()
        result = subprocess.run(
            [
                'python',
                calculation_script,
                str(version),
                json.dumps(selectedV),
                json.dumps(selectedF),
                str(target_row),
                calculation_option,
                '{}'  # Empty SenParameters for baseline
            ],
            capture_output=True,
            text=True
        )

        execution_time = time.time() - start_time

        if result.returncode != 0:
            error_msg = f"Baseline calculation failed: {result.stderr}"
            BASELINE_COMPLETED.clear()  # Reset baseline completion flag
            return jsonify({
                "error": error_msg,
                "status": "error"
            }), 500

        # Store calculation result
        result_path = os.path.join(LOGS_DIR, f"baseline_result_{run_id}.json")
        atomic_write_json(result_path, {
            "version": version,
            "calculationOption": calculation_option,
            "targetRow": target_row,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "executionTime": execution_time,
            "stdout": result.stdout,
            "returnCode": result.returncode
        })

        # BASELINE_COMPLETED event is set by the decorator

        return jsonify({
            "status": "success",
            "message": "Baseline calculation completed successfully",
            "runId": run_id,
            "version": version,
            "executionTime": f"{execution_time:.2f}s",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "next_step": "/sensitivity/configure"
        }), 200
    except Exception as e:
        # Don't clear event flag here - let the decorator handle it
        return jsonify({
            "error": f"Error during baseline calculation: {str(e)}",
            "status": "error"
        }), 500
