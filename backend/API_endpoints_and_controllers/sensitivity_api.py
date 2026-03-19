# New module: sensitivity_api.py

"""
Sensitivity Analysis API with Sequential Event Processing
Provides endpoints for sequentially orchestrated sensitivity analysis.
"""

from flask import Flask, request, jsonify, Blueprint
import os
import logging
import json
import time
import threading
from .sensitivity_orchestrator import SensitivityOrchestrator, EventState

# Create blueprint for sensitivity routes
sensitivity_bp = Blueprint('sensitivity', __name__)

# Global orchestrator instance
orchestrator = None

def init_orchestrator(base_dir, logger):
    """Initialize the global orchestrator instance."""
    global orchestrator
    orchestrator = SensitivityOrchestrator(base_dir, logger)
    logger.info("Sensitivity orchestrator initialized and registered with API")
    return orchestrator

@sensitivity_bp.route('/status', methods=['GET'])
def get_status():
    """Get the current status of the sensitivity analysis process."""
    logger = logging.getLogger('sensitivity')
    logger.info("Status check requested")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    status = orchestrator.get_state()
    logger.info(f"Current orchestrator state: {status['state']}")
    return jsonify(status)

@sensitivity_bp.route('/configure', methods=['POST'])
def configure_sensitivity():
    """Configure sensitivity analysis and transition to CONFIGURED state."""
    logger = logging.getLogger('sensitivity')
    logger.info("Configure sensitivity request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    if orchestrator.state.current_state != EventState.IDLE:
        current_state = orchestrator.state.current_state.value
        logger.warning(f"Cannot configure - process already in progress (state: {current_state})")
        return jsonify({
            "error": "Process already in progress",
            "current_state": current_state
        }), 409

    data = request.get_json()
    if not data:
        logger.error("No data provided in configure request")
        return jsonify({"error": "No data provided"}), 400

    # Extract configuration
    run_id = time.strftime("%Y%m%d_%H%M%S")
    version = data.get('selectedVersions', [1])[0]
    logger.info(f"Configuring sensitivity analysis for version {version}, run_id {run_id}")

    # Log parameters count
    sen_parameters = data.get('SenParameters', {})
    enabled_count = len([p for p, cfg in sen_parameters.items() if cfg.get('enabled')])
    logger.info(f"Configuration contains {len(sen_parameters)} parameters, {enabled_count} enabled")

    # Initialize the run
    success = orchestrator.initialize_run(version, run_id, data)
    if not success:
        logger.error("Failed to initialize run")
        return jsonify({
            "error": "Failed to initialize run",
            "state": orchestrator.get_state()
        }), 500

    logger.info(f"Sensitivity configuration initiated successfully for run_id {run_id}")
    return jsonify({
        "status": "success",
        "message": "Sensitivity configuration initiated",
        "run_id": run_id,
        "version": version,
        "next_step": "/sensitivity/copy-configs"
    })

@sensitivity_bp.route('/copy-configs', methods=['POST'])
def copy_config_modules():
    """Copy configuration modules and transition to CONFIG_COPIED state."""
    logger = logging.getLogger('sensitivity')
    logger.info("Copy config modules request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    if orchestrator.state.current_state != EventState.CONFIGURED:
        current_state = orchestrator.state.current_state.value
        logger.warning(f"Cannot copy configs - process not in CONFIGURED state (current: {current_state})")
        return jsonify({
            "error": "Process not in CONFIGURED state",
            "current_state": current_state,
            "required_state": EventState.CONFIGURED.value
        }), 409

    # Start config copying in background
    def process_configs():
        logger.info("Starting configuration copying in background thread")
        try:
            # Get parameters from state
            version = orchestrator.state.version
            params = orchestrator.state.params

            # Implementation placeholder - will use actual function from existing code
            logger.info(f"Copying configurations for version {version} with {len(params.get('SenParameters', {}))} parameters")
            time.sleep(2)  # Simulate processing time

            # Update results with completion info
            if orchestrator.state.results is None:
                orchestrator.state.results = {}
            orchestrator.state.results["config_completed"] = True
            orchestrator.state.results["config_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Transition to next state
            logger.info("Configuration copy completed successfully")
            orchestrator.transition_to(EventState.CONFIG_COPIED)
        except Exception as e:
            logger.error(f"Error in configuration copying: {str(e)}")
            orchestrator.transition_to(EventState.FAILED, error_message=f"Failed to copy configurations: {str(e)}")

    # Start background thread
    logger.info("Launching background thread for config copying")
    thread = threading.Thread(target=process_configs)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "success",
        "message": "Configuration copying initiated",
        "next_step": "/sensitivity/status"
    })

@sensitivity_bp.route('/run-baseline', methods=['POST'])
def run_baseline():
    """Run baseline calculation and transition to BASELINE_COMPLETED state."""
    logger = logging.getLogger('sensitivity')
    logger.info("Run baseline calculation request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    if orchestrator.state.current_state != EventState.CONFIG_COPIED:
        current_state = orchestrator.state.current_state.value
        logger.warning(f"Cannot run baseline - process not in CONFIG_COPIED state (current: {current_state})")
        return jsonify({
            "error": "Process not in CONFIG_COPIED state",
            "current_state": current_state,
            "required_state": EventState.CONFIG_COPIED.value
        }), 409

    # Start baseline calculation in background
    def process_baseline():
        logger.info("Starting baseline calculation in background thread")
        try:
            # Get parameters from state
            version = orchestrator.state.version
            params = orchestrator.state.params

            # Implementation placeholder - will use actual function from existing code
            logger.info(f"Running baseline calculation for version {version}")
            logger.info(f"Using calculation option: {params.get('calculationOption', 'calculateForPrice')}")
            logger.info(f"Target row: {params.get('targetRow', 20)}")

            time.sleep(5)  # Simulate processing time

            # Update results with completion info
            if orchestrator.state.results is None:
                orchestrator.state.results = {}
            orchestrator.state.results["baseline_completed"] = True
            orchestrator.state.results["baseline_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Transition to next state
            logger.info("Baseline calculation completed successfully")
            orchestrator.transition_to(EventState.BASELINE_COMPLETED)
        except Exception as e:
            logger.error(f"Error in baseline calculation: {str(e)}")
            orchestrator.transition_to(EventState.FAILED, error_message=f"Failed to calculate baseline: {str(e)}")

    # Start background thread
    logger.info("Launching background thread for baseline calculation")
    thread = threading.Thread(target=process_baseline)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "success",
        "message": "Baseline calculation initiated",
        "next_step": "/sensitivity/status"
    })

@sensitivity_bp.route('/run-variations', methods=['POST'])
def run_variations():
    """Run all parameter variations and transition to VARIATIONS_PROCESSED state."""
    logger = logging.getLogger('sensitivity')
    logger.info("Run variations calculation request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    if orchestrator.state.current_state != EventState.BASELINE_COMPLETED:
        current_state = orchestrator.state.current_state.value
        logger.warning(f"Cannot run variations - process not in BASELINE_COMPLETED state (current: {current_state})")
        return jsonify({
            "error": "Process not in BASELINE_COMPLETED state",
            "current_state": current_state,
            "required_state": EventState.BASELINE_COMPLETED.value
        }), 409

    # Start variations processing in background
    def process_variations():
        logger.info("Starting variations processing in background thread")
        try:
            # Get parameters from state
            version = orchestrator.state.version
            params = orchestrator.state.params

            # Get enabled parameters
            sen_parameters = params.get('SenParameters', {})
            enabled_params = [(p, cfg) for p, cfg in sen_parameters.items() if cfg.get('enabled')]

            logger.info(f"Processing {len(enabled_params)} enabled parameters")
            variation_results = {}

            # Process each parameter
            for param_id, param_config in enabled_params:
                mode = param_config.get('mode', 'percentage')
                values = param_config.get('values', [])
                compare_to_key = param_config.get('compareToKey', 'S13')

                logger.info(f"Processing parameter {param_id} with {len(values)} variations in mode {mode}")
                logger.info(f"Comparison key for {param_id} is {compare_to_key}")

                # Process each variation
                param_results = {"variations": {}, "success": True}
                for variation in values:
                    var_str = f"{variation:+.2f}"
                    logger.info(f"Processing {param_id} variation {var_str}")

                    # Simulate variation calculation
                    time.sleep(1)  # Simulate processing time

                    # Record result
                    param_results["variations"][var_str] = {
                        "status": "success",
                        "message": "Variation processed successfully"
                    }
                    logger.info(f"Successfully processed {param_id} variation {var_str}")

                # Store parameter results
                variation_results[param_id] = param_results
                logger.info(f"Completed all variations for parameter {param_id}")

            # Update results with completion info
            if orchestrator.state.results is None:
                orchestrator.state.results = {}
            orchestrator.state.results["variations_completed"] = True
            orchestrator.state.results["variations_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            orchestrator.state.results["variation_results"] = variation_results

            # Transition to next state
            logger.info("All parameter variations processed successfully")
            orchestrator.transition_to(EventState.VARIATIONS_PROCESSED)
        except Exception as e:
            logger.error(f"Error in variations processing: {str(e)}")
            orchestrator.transition_to(EventState.FAILED, error_message=f"Failed to process variations: {str(e)}")

    # Start background thread
    logger.info("Launching background thread for variations processing")
    thread = threading.Thread(target=process_variations)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "success",
        "message": "Variations processing initiated",
        "next_step": "/sensitivity/status"
    })

@sensitivity_bp.route('/generate-results', methods=['POST'])
def generate_results():
    """Generate results and transition to RESULTS_GENERATED state."""
    logger = logging.getLogger('sensitivity')
    logger.info("Generate results request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    if orchestrator.state.current_state != EventState.VARIATIONS_PROCESSED:
        current_state = orchestrator.state.current_state.value
        logger.warning(f"Cannot generate results - process not in VARIATIONS_PROCESSED state (current: {current_state})")
        return jsonify({
            "error": "Process not in VARIATIONS_PROCESSED state",
            "current_state": current_state,
            "required_state": EventState.VARIATIONS_PROCESSED.value
        }), 409

    # Start results generation in background
    def process_results():
        logger.info("Starting results generation in background thread")
        try:
            # Get parameters from state
            version = orchestrator.state.version
            params = orchestrator.state.params
            variation_results = orchestrator.state.results.get("variation_results", {})

            logger.info(f"Generating results for {len(variation_results)} parameters")

            # Generate combined results for all parameters
            combined_results = {}
            for param_id, param_result in variation_results.items():
                logger.info(f"Processing results for parameter {param_id}")

                # Get parameter config
                param_config = params.get('SenParameters', {}).get(param_id, {})
                mode = param_config.get('mode', 'percentage')
                compare_to_key = param_config.get('compareToKey', 'S13')

                # Create results file path based on conventions
                mode_dir_mapping = {
                    'percentage': 'Percentage',
                    'directvalue': 'DirectValue',
                    'absolutedeparture': 'AbsoluteDeparture',
                    'montecarlo': 'MonteCarlo'
                }
                mode_dir = mode_dir_mapping.get(mode.lower(), 'Percentage')

                results_file = f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
                logger.info(f"Generating results file: {results_file}")

                # Simulate results generation
                # In real implementation, we would aggregate the data and write to file
                time.sleep(1)  # Simulate processing time

                # Add to combined results
                combined_results[param_id] = {
                    "file": results_file,
                    "compareToKey": compare_to_key,
                    "mode": mode,
                    "variations_count": len(param_result.get("variations", {}))
                }
                logger.info(f"Results for {param_id} generated with {combined_results[param_id]['variations_count']} variations")

            # Update results with completion info
            if orchestrator.state.results is None:
                orchestrator.state.results = {}
            orchestrator.state.results["results_completed"] = True
            orchestrator.state.results["results_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            orchestrator.state.results["combined_results"] = combined_results

            # Transition to next state
            logger.info("Results generation completed successfully")
            orchestrator.transition_to(EventState.RESULTS_GENERATED)
        except Exception as e:
            logger.error(f"Error in results generation: {str(e)}")
            orchestrator.transition_to(EventState.FAILED, error_message=f"Failed to generate results: {str(e)}")

    # Start background thread
    logger.info("Launching background thread for results generation")
    thread = threading.Thread(target=process_results)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "success",
        "message": "Results generation initiated",
        "next_step": "/sensitivity/status"
    })

@sensitivity_bp.route('/create-visualizations', methods=['POST'])
def create_visualizations():
    """Create visualizations and transition to VISUALIZATIONS_CREATED state."""
    logger = logging.getLogger('sensitivity')
    logger.info("Create visualizations request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    if orchestrator.state.current_state != EventState.RESULTS_GENERATED:
        current_state = orchestrator.state.current_state.value
        logger.warning(f"Cannot create visualizations - process not in RESULTS_GENERATED state (current: {current_state})")
        return jsonify({
            "error": "Process not in RESULTS_GENERATED state",
            "current_state": current_state,
            "required_state": EventState.RESULTS_GENERATED.value
        }), 409

    # Start visualization creation in background
    def process_visualizations():
        logger.info("Starting visualization creation in background thread")
        try:
            # Get parameters from state
            version = orchestrator.state.version
            combined_results = orchestrator.state.results.get("combined_results", {})

            logger.info(f"Creating visualizations for {len(combined_results)} parameters")

            # Create visualizations for each parameter
            visualization_results = {}
            for param_id, result_info in combined_results.items():
                logger.info(f"Creating visualizations for parameter {param_id}")

                # Get visualization parameters
                compare_to_key = result_info.get("compareToKey", "S13")
                mode = result_info.get("mode", "percentage")

                # Generate plots for each type
                plot_types = ["waterfall", "bar", "point"]
                param_plots = {}

                for plot_type in plot_types:
                    logger.info(f"Generating {plot_type} plot for {param_id}")

                    # Simulate plot generation
                    time.sleep(1)  # Simulate processing time

                    # Record plot file path
                    plot_file = f"{plot_type}_{param_id}_{compare_to_key}_primary.png"
                    param_plots[plot_type] = {
                        "status": "generated",
                        "file": plot_file
                    }
                    logger.info(f"Generated {plot_type} plot for {param_id}: {plot_file}")

                # Add to visualization results
                visualization_results[param_id] = {
                    "plots": param_plots,
                    "compareToKey": compare_to_key,
                    "mode": mode
                }
                logger.info(f"All visualizations for {param_id} created successfully")

            # Update results with completion info
            if orchestrator.state.results is None:
                orchestrator.state.results = {}
            orchestrator.state.results["visualizations_completed"] = True
            orchestrator.state.results["visualizations_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            orchestrator.state.results["visualization_results"] = visualization_results

            # Transition to next state
            logger.info("All visualizations created successfully")
            orchestrator.transition_to(EventState.VISUALIZATIONS_CREATED)
        except Exception as e:
            logger.error(f"Error in visualization creation: {str(e)}")
            orchestrator.transition_to(EventState.FAILED, error_message=f"Failed to create visualizations: {str(e)}")

    # Start background thread
    logger.info("Launching background thread for visualization creation")
    thread = threading.Thread(target=process_visualizations)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "success",
        "message": "Visualization creation initiated",
        "next_step": "/sensitivity/status"
    })

@sensitivity_bp.route('/complete', methods=['POST'])
def complete_process():
    """Complete the process and transition to COMPLETED state."""
    logger = logging.getLogger('sensitivity')
    logger.info("Complete process request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    if orchestrator.state.current_state != EventState.VISUALIZATIONS_CREATED:
        current_state = orchestrator.state.current_state.value
        logger.warning(f"Cannot complete process - not in VISUALIZATIONS_CREATED state (current: {current_state})")
        return jsonify({
            "error": "Process not in VISUALIZATIONS_CREATED state",
            "current_state": current_state,
            "required_state": EventState.VISUALIZATIONS_CREATED.value
        }), 409

    # Update final results
    if orchestrator.state.results is None:
        orchestrator.state.results = {}

    orchestrator.state.results["completion_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Calculate total duration
    start_time = orchestrator.state.start_time
    if start_time:
        duration_seconds = time.time() - start_time
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        orchestrator.state.results["total_duration"] = f"{minutes}m {seconds}s"
        logger.info(f"Total process duration: {minutes}m {seconds}s")

    # Finalize process
    logger.info("Completing sensitivity analysis process")
    success = orchestrator.transition_to(EventState.COMPLETED)
    if not success:
        logger.error("Failed to complete process")
        return jsonify({
            "error": "Failed to complete process",
            "state": orchestrator.get_state()
        }), 500

    logger.info("Sensitivity analysis process completed successfully")
    return jsonify({
        "status": "success",
        "message": "Process completed successfully",
        "final_state": orchestrator.get_state()
    })

@sensitivity_bp.route('/reset', methods=['POST'])
def reset_process():
    """Reset the orchestrator to IDLE state."""
    logger = logging.getLogger('sensitivity')
    logger.info("Reset process request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    orchestrator.reset()
    logger.info("Orchestrator reset to IDLE state")

    return jsonify({
        "status": "success",
        "message": "Process reset successfully",
        "state": orchestrator.get_state()
    })

@sensitivity_bp.route('/run-all', methods=['POST'])
def run_all():
    """
    Run all steps in sequence automatically.
    This is a convenience endpoint for running the entire process.
    """
    logger = logging.getLogger('sensitivity')
    logger.info("Run all steps request received")

    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return jsonify({"error": "Orchestrator not initialized"}), 500

    if orchestrator.state.current_state != EventState.IDLE:
        current_state = orchestrator.state.current_state.value
        logger.warning(f"Cannot run all steps - process already in progress (state: {current_state})")
        return jsonify({
            "error": "Process already in progress",
            "current_state": current_state
        }), 409

    data = request.get_json()
    if not data:
        logger.error("No data provided in run-all request")
        return jsonify({"error": "No data provided"}), 400

    logger.info("Starting full sequenced sensitivity analysis process")

    # Start the full process in background
    def run_full_process():
        logger.info("Starting full process in background thread")
        try:
            # Step 1: Configure
            run_id = time.strftime("%Y%m%d_%H%M%S")
            version = data.get('selectedVersions', [1])[0]

            logger.info(f"Step 1: Configuring sensitivity analysis for version {version}, run_id {run_id}")
            if not orchestrator.initialize_run(version, run_id, data):
                logger.error("Failed to initialize run")
                return

            # Step 2: Copy configs
            logger.info("Step 2: Starting configuration copying")
            time.sleep(1)  # Small delay between steps

            # In real implementation, this would call the actual config copying function
            time.sleep(2)  # Simulate processing time

            # Update results with completion info
            if orchestrator.state.results is None:
                orchestrator.state.results = {}
            orchestrator.state.results["config_completed"] = True
            orchestrator.state.results["config_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Transition to next state
            logger.info("Configuration copy completed successfully")
            if not orchestrator.transition_to(EventState.CONFIG_COPIED):
                logger.error("Failed to transition to CONFIG_COPIED state")
                return

            # Step 3: Run baseline
            logger.info("Step 3: Starting baseline calculation")
            time.sleep(1)  # Small delay between steps

            # In real implementation, this would call the actual baseline calculation function
            time.sleep(3)  # Simulate processing time

            # Update results with completion info
            orchestrator.state.results["baseline_completed"] = True
            orchestrator.state.results["baseline_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Transition to next state
            logger.info("Baseline calculation completed successfully")
            if not orchestrator.transition_to(EventState.BASELINE_COMPLETED):
                logger.error("Failed to transition to BASELINE_COMPLETED state")
                return

            # Step 4: Run variations
            logger.info("Step 4: Starting variations processing")
            time.sleep(1)  # Small delay between steps

            # Get enabled parameters
            sen_parameters = data.get('SenParameters', {})
            enabled_params = [(p, cfg) for p, cfg in sen_parameters.items() if cfg.get('enabled')]

            logger.info(f"Processing {len(enabled_params)} enabled parameters")
            variation_results = {}

            # Process each parameter
            for param_id, param_config in enabled_params:
                mode = param_config.get('mode', 'percentage')
                values = param_config.get('values', [])
                compare_to_key = param_config.get('compareToKey', 'S13')

                logger.info(f"Processing parameter {param_id} with {len(values)} variations in mode {mode}")

                # Process each variation
                param_results = {"variations": {}, "success": True}
                for variation in values:
                    var_str = f"{variation:+.2f}"
                    logger.info(f"Processing {param_id} variation {var_str}")

                    # Simulate variation calculation
                    time.sleep(0.5)  # Simulate processing time

                    # Record result
                    param_results["variations"][var_str] = {
                        "status": "success",
                        "message": "Variation processed successfully"
                    }

                # Store parameter results
                variation_results[param_id] = param_results

            # Update results with completion info
            orchestrator.state.results["variations_completed"] = True
            orchestrator.state.results["variations_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            orchestrator.state.results["variation_results"] = variation_results

            # Transition to next state
            logger.info("All parameter variations processed successfully")
            if not orchestrator.transition_to(EventState.VARIATIONS_PROCESSED):
                logger.error("Failed to transition to VARIATIONS_PROCESSED state")
                return

            # Step 5: Generate results
            logger.info("Step 5: Starting results generation")
            time.sleep(1)  # Small delay between steps

            # Generate combined results
            combined_results = {}
            for param_id, param_result in variation_results.items():
                param_config = sen_parameters.get(param_id, {})
                mode = param_config.get('mode', 'percentage')
                compare_to_key = param_config.get('compareToKey', 'S13')

                results_file = f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
                logger.info(f"Generating results file: {results_file}")

                # Simulate results generation
                time.sleep(0.5)  # Simulate processing time

                # Add to combined results
                combined_results[param_id] = {
                    "file": results_file,
                    "compareToKey": compare_to_key,
                    "mode": mode,
                    "variations_count": len(param_result.get("variations", {}))
                }

            # Update results with completion info
            orchestrator.state.results["results_completed"] = True
            orchestrator.state.results["results_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            orchestrator.state.results["combined_results"] = combined_results

            # Transition to next state
            logger.info("Results generation completed successfully")
            if not orchestrator.transition_to(EventState.RESULTS_GENERATED):
                logger.error("Failed to transition to RESULTS_GENERATED state")
                return

            # Step 6: Create visualizations
            logger.info("Step 6: Starting visualization creation")
            time.sleep(1)  # Small delay between steps

            # Create visualizations
            visualization_results = {}
            for param_id, result_info in combined_results.items():
                compare_to_key = result_info.get("compareToKey", "S13")
                mode = result_info.get("mode", "percentage")

                # Generate plots for each type
                plot_types = ["waterfall", "bar", "point"]
                param_plots = {}

                for plot_type in plot_types:
                    logger.info(f"Generating {plot_type} plot for {param_id}")

                    # Simulate plot generation
                    time.sleep(0.3)  # Simulate processing time

                    # Record plot file path
                    plot_file = f"{plot_type}_{param_id}_{compare_to_key}_primary.png"
                    param_plots[plot_type] = {
                        "status": "generated",
                        "file": plot_file
                    }

                # Add to visualization results
                visualization_results[param_id] = {
                    "plots": param_plots,
                    "compareToKey": compare_to_key,
                    "mode": mode
                }

            # Update results with completion info
            orchestrator.state.results["visualizations_completed"] = True
            orchestrator.state.results["visualizations_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            orchestrator.state.results["visualization_results"] = visualization_results

            # Transition to next state
            logger.info("All visualizations created successfully")
            if not orchestrator.transition_to(EventState.VISUALIZATIONS_CREATED):
                logger.error("Failed to transition to VISUALIZATIONS_CREATED state")
                return

            # Step 7: Complete
            logger.info("Step 7: Completing process")
            time.sleep(1)  # Small delay between steps

            # Update final results
            orchestrator.state.results["completion_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Calculate total duration
            start_time = orchestrator.state.start_time
            if start_time:
                duration_seconds = time.time() - start_time
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                orchestrator.state.results["total_duration"] = f"{minutes}m {seconds}s"
                logger.info(f"Total process duration: {minutes}m {seconds}s")

            # Transition to final state
            logger.info("Process completed successfully")
            if not orchestrator.transition_to(EventState.COMPLETED):
                logger.error("Failed to transition to COMPLETED state")
                return

            logger.info("Full sequenced sensitivity analysis process completed successfully")

        except Exception as e:
            logger.error(f"Error in full process execution: {str(e)}")
            orchestrator.transition_to(EventState.FAILED, error_message=f"Process failed: {str(e)}")

    # Start background thread
    logger.info("Launching background thread for full process execution")
    thread = threading.Thread(target=run_full_process)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "success",
        "message": "Full process initiated",
        "next_step": "/sensitivity/status"
    })
# Integration handlers for actual implementation

def configure_handler(state):
    """
    Handler for CONFIGURED state.
    Implements actual configuration logic from existing code.
    """
    logger = logging.getLogger('sensitivity')
    logger.info("Executing configure handler with actual implementation")

    try:
        # Extract configuration parameters
        version = state.version
        SenParameters = state.params.get('SenParameters', {})

        # Use existing create_sensitivity_directories and save_sensitivity_config_files
        logger.info(f"Creating sensitivity directories for version {version}")
        sensitivity_dir, reports_dir = create_sensitivity_directories(version, SenParameters)
        logger.info(f"Created directories: sensitivity_dir={sensitivity_dir}, reports_dir={reports_dir}")

        logger.info(f"Saving sensitivity configuration files for version {version}")
        saved_files = save_sensitivity_config_files(version, reports_dir, SenParameters)
        logger.info(f"Saved {len(saved_files)} configuration files")

        # Store paths for later use
        if state.results is None:
            state.results = {}

        state.results.update({
            "sensitivity_dir": sensitivity_dir,
            "reports_dir": reports_dir,
            "saved_files": saved_files,
            "config_completed": True,
            "config_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

        logger.info("Configuration handler completed successfully")

    except Exception as e:
        logger.error(f"Error in configure handler: {str(e)}")
        raise

def copy_config_handler(state):
    """
    Handler for CONFIG_COPIED state.
    Implements actual config copying logic from existing code.
    """
    logger = logging.getLogger('sensitivity')
    logger.info("Executing copy_config handler with actual implementation")

    try:
        # Extract parameters
        version = state.version
        sensitivity_dir = state.results.get("sensitivity_dir")
        SenParameters = state.params.get('SenParameters', {})

        if not sensitivity_dir:
            raise ValueError("sensitivity_dir not found in state results")

        # Use existing trigger_config_module_copy
        logger.info(f"Triggering config module copy for version {version}")
        result = trigger_config_module_copy(version, sensitivity_dir, SenParameters)
        logger.info(f"Config copy service result: {result}")

        # Verify that actual configuration files have been created
        logger.info("Verifying configuration files existence...")
        config_files_verified = False
        wait_duration = 180  # 3 minutes
        start_wait = time.time()

        while time.time() - start_wait < wait_duration:
            # Check for actual configuration files for each enabled parameter
            all_found = True

            for param_id, param_config in SenParameters.items():
                if not param_config.get('enabled'):
                    continue

                mode = param_config.get('mode', 'percentage')
                values = param_config.get('values', [])
                variation_list = values

                # Check if configuration files exist for each variation
                for variation in variation_list:
                    var_str = f"{variation:+.2f}"
                    config_path_pattern = os.path.join(
                        sensitivity_dir,
                        param_id,
                        mode.lower(),
                        var_str,
                        f"{version}_config_module_*.json"
                    )

                    if not glob.glob(config_path_pattern):
                        all_found = False
                        logger.info(f"Still waiting for config files for {param_id} variation {var_str}...")
                        break

                if not all_found:
                    break

            if all_found:
                config_files_verified = True
                logger.info("All required configuration files verified!")
                break

            # Log progress and wait
            elapsed = time.time() - start_wait
            logger.info(f"Still waiting for configuration files... ({elapsed:.0f}s elapsed)")
            time.sleep(15)  # Check every 15 seconds

        if not config_files_verified:
            logger.warning("Timed out waiting for all configuration files, proceeding anyway")

        # Update state results
        if state.results is None:
            state.results = {}

        state.results.update({
            "config_copy_result": result,
            "config_files_verified": config_files_verified,
            "copy_completed": True,
            "copy_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

        logger.info("Copy_config handler completed successfully")

    except Exception as e:
        logger.error(f"Error in copy_config handler: {str(e)}")
        raise

def baseline_handler(state):
    """
    Handler for BASELINE_COMPLETED state.
    Implements actual baseline calculation logic from existing code.
    """
    logger = logging.getLogger('sensitivity')
    logger.info("Executing baseline handler with actual implementation")

    try:
        # Extract parameters
        version = state.version
        selectedV = state.params.get('selectedV', {})
        selectedF = state.params.get('selectedF', {})
        targetRow = state.params.get('targetRow', 20)
        calculationOption = state.params.get('calculationOption', 'calculateForPrice')

        # Execute configuration management scripts
        logger.info("Executing configuration management scripts")
        for script in COMMON_PYTHON_SCRIPTS:
            script_name = os.path.basename(script)
            logger.info(f"Executing: {script_name}")

            result = subprocess.run(
                ['python', script, str(version)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = f"Script execution failed: {script_name}\nError: {result.stderr}"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.info(f"Completed {script_name}")
            time.sleep(0.5)  # Ensure proper sequencing

        # Get calculation script
        logger.info(f"Getting calculation script for {calculationOption}")
        calculation_script_func = CALCULATION_SCRIPTS.get(calculationOption)
        if not calculation_script_func:
            raise Exception(f"No script found for calculation mode: {calculationOption}")

        calculation_script = calculation_script_func(version)
        logger.info(f"Using calculation script: {os.path.basename(calculation_script)}")

        # Run baseline calculation
        logger.info("Executing baseline calculation")
        result = subprocess.run(
            [
                'python',
                calculation_script,
                str(version),
                json.dumps(selectedV),
                json.dumps(selectedF),
                str(targetRow),
                calculationOption,
                '{}'  # Empty SenParameters for baseline
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            error_msg = f"Baseline calculation failed: {result.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info("Baseline calculation completed successfully")

        # Update state results
        if state.results is None:
            state.results = {}

        state.results.update({
            "baseline_completed": True,
            "baseline_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "baseline_stdout": result.stdout,
            "baseline_script": os.path.basename(calculation_script)
        })

        logger.info("Baseline handler completed successfully")

    except Exception as e:
        logger.error(f"Error in baseline handler: {str(e)}")
        raise

def variations_handler(state):
    """
    Handler for VARIATIONS_PROCESSED state.
    Implements actual variation calculation logic from existing code.
    """
    logger = logging.getLogger('sensitivity')
    logger.info("Executing variations handler with actual implementation")

    try:
        # Extract parameters
        version = state.version
        SenParameters = state.params.get('SenParameters', {})
        selectedV = state.params.get('selectedV', {})
        selectedF = state.params.get('selectedF', {})
        targetRow = state.params.get('targetRow', 20)
        calculationOption = state.params.get('calculationOption', 'calculateForPrice')

        # Get CFA-b.py script path
        logger.info("Getting sensitivity calculation script (CFA-b.py)")
        cfa_b_script = get_sensitivity_calculation_script()
        logger.info(f"Using calculation script: {os.path.basename(cfa_b_script)}")

        # Process enabled sensitivity parameters
        enabled_params = [(param_id, param_config) for param_id, param_config
                          in SenParameters.items() if param_config.get('enabled')]

        if not enabled_params:
            logger.warning("No enabled sensitivity parameters found")
            return

        logger.info(f"Processing {len(enabled_params)} enabled parameters")

        # Results collection
        calculation_results = {}
        overall_success = True

        # Mode mapping for standardized directory names
        mode_dir_mapping = {
            'percentage': 'Percentage',
            'directvalue': 'DirectValue',
            'absolutedeparture': 'AbsoluteDeparture',
            'montecarlo': 'MonteCarlo'
        }

        # Process each parameter
        for param_id, param_config in enabled_params:
            mode = param_config.get('mode', 'percentage')
            values = param_config.get('values', [])
            compare_to_key = param_config.get('compareToKey', 'S13')

            if not values:
                logger.warning(f"No values specified for {param_id}, skipping")
                continue

            # Determine variations based on mode
            variations = []
            for value in values:
                if value is not None:
                    try:
                        variations.append(float(value))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid variation value in {param_id}: {value}")

            if not variations:
                logger.warning(f"No valid variation values for {param_id}, skipping")
                continue

            param_results = {"variations": {}, "success": True}
            logger.info(f"Processing {param_id} with {len(variations)} variations")

            # Process each variation
            for variation in variations:
                var_str = f"{variation:+.2f}"
                logger.info(f"Processing {param_id} variation {var_str}")

                try:
                    # Call CFA-b.py with CalSen paths
                    logger.info(f"Executing CFA-b.py for {param_id} variation {var_str}...")

                    # Prepare the environment variables to avoid division by zero errors
                    env = os.environ.copy()
                    env["PYTHONPATH"] = SCRIPT_DIR + os.pathsep + env.get("PYTHONPATH", "")

                    # Log the full command for debugging
                    command = [
                        'python',
                        cfa_b_script,
                        str(version),
                        json.dumps(selectedV),
                        json.dumps(selectedF),
                        str(targetRow),
                        calculationOption,
                        json.dumps({param_id: param_config}),
                        "--param_id", param_id,
                        "--variation", str(variation),
                        "--compare_to_key", compare_to_key,
                        "--mode", mode
                    ]
                    logger.info(f"Command: {' '.join(command)}")

                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=600,  # 10-minute timeout
                        env=env,
                        cwd=SCRIPT_DIR  # Set working directory to script directory
                    )

                    # Log the output for debugging
                    if result.stdout:
                        logger.info(f"Command stdout: {result.stdout[:200]}...")
                    if result.stderr:
                        logger.error(f"Command stderr: {result.stderr}")

                    if result.returncode == 0:
                        logger.info(f"Successfully calculated {param_id} variation {var_str}")
                        param_results["variations"][var_str] = {
                            "status": "success",
                            "message": "Calculation completed successfully"
                        }

                        # Extract economic summary info (similar to calculate_sensitivity)
                        # Keeping this part brief as it's similar to the existing code
                        try:
                            # Locate and extract economic summary
                            sensitivity_dir = state.results.get("sensitivity_dir")
                            mode_cap = mode_dir_mapping.get(mode.lower(), 'Percentage')

                            param_var_dir = os.path.join(
                                sensitivity_dir, param_id, mode.lower(), var_str
                            )
                            econ_summary_file = os.path.join(
                                param_var_dir, f"Economic_Summary({version}).csv"
                            )

                            # Extract information from summary if file exists
                            if os.path.exists(econ_summary_file):
                                logger.info(f"Found economic summary at {econ_summary_file}")
                            else:
                                logger.warning(f"Economic summary not found at: {econ_summary_file}")
                        except Exception as e:
                            logger.error(f"Error extracting economic summary: {str(e)}")

                    else:
                        error_msg = f"Calculation failed for {param_id} variation {var_str}: {result.stderr}"
                        logger.error(error_msg)
                        param_results["variations"][var_str] = {
                            "status": "error",
                            "message": error_msg
                        }
                        param_results["success"] = False
                        overall_success = False

                except subprocess.TimeoutExpired:
                    error_msg = f"Calculation timed out for {param_id} variation {var_str}"
                    logger.error(error_msg)
                    param_results["variations"][var_str] = {
                        "status": "error",
                        "message": error_msg
                    }
                    param_results["success"] = False
                    overall_success = False

                except Exception as e:
                    error_msg = f"Error processing {param_id} variation {var_str}: {str(e)}"
                    logger.error(error_msg)
                    param_results["variations"][var_str] = {
                        "status": "error",
                        "message": error_msg
                    }
                    param_results["success"] = False
                    overall_success = False

            # Add results for this parameter
            calculation_results[param_id] = param_results
            logger.info(f"Completed processing parameter {param_id}")

        # Log summary
        logger.info("\nSensitivity Calculation Summary:")
        for param_id, result in calculation_results.items():
            success_count = sum(1 for var in result["variations"].values() if var.get("status") == "success")
            total_count = len(result["variations"])
            logger.info(f"{param_id}: {success_count}/{total_count} variations successful")

        # Update state results
        if state.results is None:
            state.results = {}

        state.results.update({
            "variations_completed": True,
            "variations_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "variation_results": calculation_results,
            "overall_success": overall_success
        })

        logger.info("Variations handler completed successfully")

    except Exception as e:
        logger.error(f"Error in variations handler: {str(e)}")
        raise

def results_handler(state):
    """
    Handler for RESULTS_GENERATED state.
    Implements result generation and data aggregation.
    """
    logger = logging.getLogger('sensitivity')
    logger.info("Executing results handler with actual implementation")

    try:
        # Extract parameters
        version = state.version
        sensitivity_dir = state.results.get("sensitivity_dir")
        variation_results = state.results.get("variation_results", {})
        SenParameters = state.params.get('SenParameters', {})

        if not sensitivity_dir:
            raise ValueError("sensitivity_dir not found in state results")

        # Process and save results for each parameter
        logger.info(f"Generating results files for {len(variation_results)} parameters")
        combined_results = {}

        for param_id, param_result in variation_results.items():
            # Skip parameters with failed calculations
            if not param_result.get("success", False):
                logger.warning(f"Skipping results generation for {param_id} due to calculation failures")
                continue

            # Get parameter config
            param_config = SenParameters.get(param_id, {})
            mode = param_config.get('mode', 'percentage')
            compare_to_key = param_config.get('compareToKey', 'S13')

            # Mode mapping for standardized directory names
            mode_dir_mapping = {
                'percentage': 'Percentage',
                'directvalue': 'DirectValue',
                'absolutedeparture': 'AbsoluteDeparture',
                'montecarlo': 'MonteCarlo'
            }
            mode_dir = mode_dir_mapping.get(mode.lower(), 'Percentage')

            # Build results data structure
            results_data = {
                "parameter": param_id,
                "compareToKey": compare_to_key,
                "mode": mode,
                "version": version,
                "variations": param_result.get("variations", {}),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Define results file path
            results_file = os.path.join(
                sensitivity_dir,
                mode_dir,
                f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
            )

            # Save results to file
            try:
                with open(results_file, 'w') as f:
                    json.dump(results_data, f, indent=2)
                logger.info(f"Saved results file: {results_file}")

                # Add to combined results
                combined_results[param_id] = {
                    "file": results_file,
                    "compareToKey": compare_to_key,
                    "mode": mode,
                    "variations_count": len(param_result.get("variations", {}))
                }
            except Exception as e:
                logger.error(f"Error saving results file for {param_id}: {str(e)}")

        # Update state results
        if state.results is None:
            state.results = {}

        state.results.update({
            "results_completed": True,
            "results_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "combined_results": combined_results
        })

        logger.info("Results handler completed successfully")

    except Exception as e:
        logger.error(f"Error in results handler: {str(e)}")
        raise

def visualizations_handler(state):
    """
    Handler for VISUALIZATIONS_CREATED state.
    Implements visualization generation logic with unified plot capabilities.
    """
    logger = logging.getLogger('sensitivity')
    logger.info("Executing visualizations handler with actual implementation")

    try:
        # Extract parameters
        version = state.version
        combined_results = state.results.get("combined_results", {})
        sensitivity_dir = state.results.get("sensitivity_dir")
        SenParameters = state.params.get('SenParameters', {})

        if not sensitivity_dir:
            raise ValueError("sensitivity_dir not found in state results")

        logger.info(f"Creating visualizations for {len(combined_results)} parameters")

        # Get access to native functions for plotting if available
        try:
            # Try to import plot generation function
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from sensitivity_Routes import generate_plot_from_results
            have_plot_generator = True
            logger.info("Successfully imported generate_plot_from_results function")
        except ImportError:
            have_plot_generator = False
            logger.warning("Could not import generate_plot_from_results function, will use fallback plotting")

        # Mode mapping for standardized directory names
        mode_dir_mapping = {
            'percentage': 'Percentage',
            'directvalue': 'DirectValue',
            'absolutedeparture': 'AbsoluteDeparture',
            'montecarlo': 'MonteCarlo'
        }

        # Step 1: Identify unique combinations of plot type, compare-to-key, and comparison type
        logger.info("Identifying unique plot combinations")
        plot_combinations = {}

        for param_id, param_config in SenParameters.items():
            if not param_config.get('enabled'):
                continue

            # Get comparison parameters
            compare_to_key = param_config.get('compareToKey', 'S13')
            comparison_type = param_config.get('comparisonType', 'primary')
            mode = param_config.get('mode', 'percentage')

            # Check for plot types enabled
            plot_types = []
            if param_config.get('waterfall', False): plot_types.append('waterfall')
            if param_config.get('bar', False): plot_types.append('bar')
            if param_config.get('point', False): plot_types.append('point')

            # If no plot types specified, default to all
            if not plot_types:
                plot_types = ['waterfall', 'bar', 'point']

            logger.info(f"Parameter {param_id}: compare_to_key={compare_to_key}, comparison_type={comparison_type}, plot_types={plot_types}")

            # For each plot type, add to combinations
            for plot_type in plot_types:
                # Define the combination key: plot_type + compare_to_key + comparison_type
                combo_key = f"{plot_type}_{compare_to_key}_{comparison_type}"

                if combo_key not in plot_combinations:
                    plot_combinations[combo_key] = {
                        'plot_type': plot_type,
                        'compare_to_key': compare_to_key,
                        'comparison_type': comparison_type,
                        'parameters': []
                    }

                # Add this parameter to the combination
                plot_combinations[combo_key]['parameters'].append({
                    'param_id': param_id,
                    'mode': mode,
                    'values': param_config.get('values', [])
                })

        logger.info(f"Identified {len(plot_combinations)} unique plot combinations")

        # Step 2: Create individual plots for each parameter
        visualization_results = {}

        for param_id, result_info in combined_results.items():
            logger.info(f"Creating individual visualizations for parameter {param_id}")

            # Get visualization parameters
            compare_to_key = result_info.get("compareToKey", "S13")
            mode = result_info.get("mode", "percentage")
            mode_dir = mode_dir_mapping.get(mode.lower(), 'Percentage')

            # Get parameter config to check which plot types are enabled
            param_config = SenParameters.get(param_id, {})
            plot_types = []
            if param_config.get('waterfall', False): plot_types.append('waterfall')
            if param_config.get('bar', False): plot_types.append('bar')
            if param_config.get('point', False): plot_types.append('point')

            # If no plot types specified, default to all
            if not plot_types:
                plot_types = ['waterfall', 'bar', 'point']

            # Generate individual plots for each type
            param_plots = {}

            for plot_type in plot_types:
                logger.info(f"Generating individual {plot_type} plot for {param_id}")

                # Plot file naming convention
                plot_name = f"{plot_type}_{param_id}_{compare_to_key}_primary.png"
                plot_dir = os.path.join(sensitivity_dir, mode_dir, plot_type)
                plot_path = os.path.join(plot_dir, plot_name)

                # Ensure plot directory exists
                os.makedirs(plot_dir, exist_ok=True)

                # Check if plot exists or needs to be generated
                if os.path.exists(plot_path):
                    logger.info(f"Found existing {plot_type} plot at: {plot_path}")
                    plot_status = "available"
                    plot_found = True
                else:
                    logger.info(f"Need to generate {plot_type} plot...")
                    plot_found = False

                    # Path to results file
                    results_path = os.path.join(
                        sensitivity_dir,
                        mode_dir,
                        f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
                    )

                    if not os.path.exists(results_path):
                        logger.warning(f"Results file not found: {results_path}")
                        plot_status = "error"
                        continue

                    # Generate plot if we have the generator function
                    if have_plot_generator:
                        try:
                            logger.info(f"Generating {plot_type} plot from results at: {results_path}")
                            success = generate_plot_from_results(
                                version=version,
                                param_id=param_id,
                                compare_to_key=compare_to_key,
                                plot_type=plot_type,
                                mode=mode,
                                result_path=results_path
                            )

                            if success and os.path.exists(plot_path):
                                logger.info(f"Successfully generated {plot_type} plot at: {plot_path}")
                                plot_status = "generated"
                                plot_found = True
                            else:
                                logger.error(f"Failed to generate {plot_type} plot")
                                plot_status = "error"
                        except Exception as e:
                            logger.error(f"Error generating {plot_type} plot: {str(e)}")
                            plot_status = "error"
                    else:
                        logger.warning(f"No plot generator available, skipping plot generation")
                        plot_status = "not_generated"

                # Add plot info to results
                relative_path = os.path.relpath(plot_path, sensitivity_dir) if plot_found else None
                param_plots[plot_type] = {
                    "status": plot_status,
                    "path": relative_path,
                    "absolute_path": plot_path if plot_found else None,
                    "compare_to_key": compare_to_key
                }

            # Add to visualization results
            visualization_results[param_id] = {
                "plots": param_plots,
                "compareToKey": compare_to_key,
                "mode": mode
            }
            logger.info(f"Completed individual visualizations for parameter {param_id}")

        # Step 3: Create unified plots for each unique combination
        logger.info("Creating unified plots for parameter combinations")
        unified_plots = {}

        for combo_key, combo_info in plot_combinations.items():
            if len(combo_info['parameters']) <= 1:
                logger.info(f"Skipping unified plot for {combo_key} - only contains one parameter")
                continue

            plot_type = combo_info['plot_type']
            compare_to_key = combo_info['compare_to_key']
            comparison_type = combo_info['comparison_type']
            parameters = combo_info['parameters']

            logger.info(f"Creating unified {plot_type} plot for {len(parameters)} parameters with compare_to_key={compare_to_key}")

            # For each parameter in this combination, we need to extract economic_summary data
            param_data = []

            for param_info in parameters:
                param_id = param_info['param_id']
                mode = param_info['mode']
                values = param_info['values']

                logger.info(f"Extracting data for {param_id} with {len(values)} variations")

                # Mode directory with capitalized name
                mode_dir = mode_dir_mapping.get(mode.lower(), 'Percentage')

                # For each variation, extract economic summary data
                variation_data = {}

                for variation in values:
                    var_str = f"{variation:+.2f}"

                    # Look in the CONFIG_VAR_DIR (not param_var_dir) as specified
                    config_var_dir = os.path.join(
                        sensitivity_dir,
                        mode_dir,
                        "Configuration",
                        f"{param_id}_{var_str}"
                    )

                    # Economic summary file
                    econ_summary_file = os.path.join(
                        config_var_dir, f"Economic_Summary({version}).csv"
                    )

                    if os.path.exists(econ_summary_file):
                        logger.info(f"Found economic summary at {econ_summary_file}")

                        try:
                            # Read economic summary into DataFrame
                            econ_df = pd.read_csv(econ_summary_file)

                            # Extract metrics (first 9 rows as specified)
                            metrics = {}
                            for i in range(min(9, len(econ_df))):
                                metric_name = econ_df.iloc[i]['Metric']
                                metric_value = econ_df.iloc[i]['Value']

                                # Clean value (remove $ and commas)
                                if isinstance(metric_value, str):
                                    metric_value = metric_value.replace('$', '').replace(',', '')

                                    # Convert to numeric if possible
                                    try:
                                        if '%' in metric_value:
                                            # Parse percentage value
                                            metric_value = float(metric_value.replace('%', '')) / 100
                                        else:
                                            metric_value = float(metric_value)
                                    except ValueError:
                                        # Keep as string if not convertible
                                        pass

                                metrics[metric_name] = metric_value

                            # Add to variation data
                            variation_data[var_str] = metrics
                            logger.info(f"Extracted {len(metrics)} metrics for {param_id} variation {var_str}")

                        except Exception as e:
                            logger.error(f"Error reading economic summary for {param_id} variation {var_str}: {str(e)}")
                    else:
                        logger.warning(f"Economic summary not found at: {econ_summary_file}")

                # Add parameter data
                param_data.append({
                    'param_id': param_id,
                    'mode': mode,
                    'values': values,
                    'variation_data': variation_data
                })

            # Create unified plot filename
            unified_plot_name = f"unified_{plot_type}_{compare_to_key}_{comparison_type}.png"
            plot_dir = os.path.join(sensitivity_dir, "Unified")
            os.makedirs(plot_dir, exist_ok=True)
            unified_plot_path = os.path.join(plot_dir, unified_plot_name)

            # Generate unified plot
            logger.info(f"Generating unified {plot_type} plot at: {unified_plot_path}")

            # In a full implementation, we would call a function to generate the unified plot
            # For now, we'll just record that it would be generated
            unified_plots[combo_key] = {
                "status": "planned",
                "path": os.path.relpath(unified_plot_path, sensitivity_dir),
                "absolute_path": unified_plot_path,
                "parameters": [p['param_id'] for p in parameters],
                "plot_type": plot_type,
                "compare_to_key": compare_to_key,
                "comparison_type": comparison_type
            }

            logger.info(f"Planned unified plot for {combo_key} with {len(parameters)} parameters")

        # Update state results
        if state.results is None:
            state.results = {}

        state.results.update({
            "visualizations_completed": True,
            "visualizations_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "visualization_results": visualization_results,
            "unified_plots": unified_plots,
            "plot_combinations": plot_combinations
        })

        logger.info("Visualizations handler completed successfully")

    except Exception as e:
        logger.error(f"Error in visualizations handler: {str(e)}")
        raise