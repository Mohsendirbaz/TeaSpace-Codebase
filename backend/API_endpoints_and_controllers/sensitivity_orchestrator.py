# New module: sensitivity_orchestrator.py

"""
Sensitivity Analysis Orchestration Service

Provides sequential event processing for sensitivity analysis calculations.
Ensures proper ordering of operations and verification between steps.
"""

import os
import logging
import json
import time
import threading
import enum
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Callable
import flask

# Event States for the Orchestration Pipeline
class EventState(enum.Enum):
    IDLE = "idle"
    CONFIGURED = "configured"
    CONFIG_COPIED = "config_copied"
    BASELINE_COMPLETED = "baseline_completed"
    VARIATIONS_PROCESSED = "variations_processed"
    RESULTS_GENERATED = "results_generated"
    VISUALIZATIONS_CREATED = "visualizations_created"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessState:
    """Represents the current state of the sensitivity analysis process."""
    current_state: EventState = EventState.IDLE
    version: int = None
    run_id: str = None
    params: Dict[str, Any] = None
    start_time: float = None
    last_update: float = None
    error_message: str = None
    results: Dict[str, Any] = None

class SensitivityOrchestrator:
    """
    Orchestrates sensitivity analysis calculations in sequential phases.
    Manages state transitions and ensures proper completion of each phase.
    """

    def __init__(self, base_dir: str, logger: logging.Logger):
        self.base_dir = base_dir
        self.logger = logger
        self.state = ProcessState()
        self.state_lock = threading.Lock()
        self.event_handlers = {}
        self.register_default_handlers()

        self.logger.info(f"SensitivityOrchestrator initialized with base_dir: {base_dir}")

    def register_default_handlers(self):
        """Register default event handlers for state transitions."""
        # Define handlers for state transitions
        self.logger.info("Registering default event handlers")
        pass

    def register_handler(self, state: EventState, handler: Callable):
        """Register a custom handler for a specific state."""
        self.event_handlers[state] = handler
        self.logger.info(f"Registered custom handler for state: {state.value}")

    def transition_to(self, new_state: EventState, **kwargs):
        """
        Transition to a new state with validation and logging.
        Returns True if transition was successful.
        """
        with self.state_lock:
            old_state = self.state.current_state

            # Validate transition is allowed
            if not self._is_valid_transition(old_state, new_state):
                self.logger.error(f"Invalid state transition from {old_state.value} to {new_state.value}")
                return False

            # Update state
            self.state.current_state = new_state
            self.state.last_update = time.time()

            # Update additional properties if provided
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)

            self.logger.info(f"State transition: {old_state.value} -> {new_state.value}")

            # Run handler if available
            if new_state in self.event_handlers:
                try:
                    self.logger.info(f"Executing handler for state: {new_state.value}")
                    self.event_handlers[new_state](self.state)
                    self.logger.info(f"Handler for {new_state.value} completed successfully")
                except Exception as e:
                    self.logger.error(f"Error in handler for {new_state.value}: {str(e)}")
                    self.transition_to(EventState.FAILED, error_message=str(e))
                    return False

            return True

    def _is_valid_transition(self, from_state: EventState, to_state: EventState) -> bool:
        """Check if a state transition is valid."""
        # Define allowed transitions
        valid_transitions = {
            EventState.IDLE: [EventState.CONFIGURED, EventState.FAILED],
            EventState.CONFIGURED: [EventState.CONFIG_COPIED, EventState.FAILED],
            EventState.CONFIG_COPIED: [EventState.BASELINE_COMPLETED, EventState.FAILED],
            EventState.BASELINE_COMPLETED: [EventState.VARIATIONS_PROCESSED, EventState.FAILED],
            EventState.VARIATIONS_PROCESSED: [EventState.RESULTS_GENERATED, EventState.FAILED],
            EventState.RESULTS_GENERATED: [EventState.VISUALIZATIONS_CREATED, EventState.FAILED],
            EventState.VISUALIZATIONS_CREATED: [EventState.COMPLETED, EventState.FAILED],
            # Failed is a terminal state
            EventState.COMPLETED: [],
            EventState.FAILED: [],
        }

        return to_state in valid_transitions.get(from_state, [])

    def initialize_run(self, version: int, run_id: str, params: Dict[str, Any]) -> bool:
        """Initialize a new run and transition to CONFIGURED state."""
        self.logger.info(f"Initializing new sensitivity run: version={version}, run_id={run_id}")

        if self.state.current_state != EventState.IDLE:
            self.logger.warning(f"Cannot initialize new run - current state is {self.state.current_state.value}")
            return False

        # Initialize results dictionary
        results = {
            "version": version,
            "run_id": run_id,
            "enabled_parameters": [p for p, cfg in params.get('SenParameters', {}).items() if cfg.get('enabled')]
        }

        self.logger.info(f"Found {len(results['enabled_parameters'])} enabled parameters")

        return self.transition_to(
            EventState.CONFIGURED,
            version=version,
            run_id=run_id,
            params=params,
            start_time=time.time(),
            results=results
        )

    def get_state(self) -> Dict[str, Any]:
        """Get the current state as a dictionary."""
        with self.state_lock:
            elapsed = 0
            if self.state.start_time:
                elapsed = time.time() - self.state.start_time

            state_dict = {
                "state": self.state.current_state.value,
                "version": self.state.version,
                "run_id": self.state.run_id,
                "start_time": self.state.start_time,
                "last_update": self.state.last_update,
                "elapsed_seconds": elapsed,
                "elapsed_formatted": f"{int(elapsed // 60)}m {int(elapsed % 60)}s",
                "error": self.state.error_message,
            }

            # Add selected results if available
            if self.state.results:
                state_dict["enabled_parameters"] = self.state.results.get("enabled_parameters", [])
                state_dict["parameter_count"] = len(state_dict["enabled_parameters"])

                # Add completion status per phase if available
                for phase in ["config", "baseline", "variations", "results", "visualizations"]:
                    if f"{phase}_completed" in self.state.results:
                        state_dict[f"{phase}_completed"] = self.state.results[f"{phase}_completed"]

            return state_dict

    def reset(self) -> None:
        """Reset the orchestrator to IDLE state."""
        with self.state_lock:
            old_state = self.state.current_state.value
            self.logger.info(f"Resetting orchestrator from {old_state} to IDLE state")
            self.state = ProcessState()
            self.logger.info("Orchestrator reset complete - now in IDLE state")