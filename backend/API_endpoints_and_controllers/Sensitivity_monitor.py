import os
import json
import time
import threading
import logging
from datetime import datetime
from queue import Queue

# Configure logger
logger = logging.getLogger('sensitivity')

# Dictionary to store active monitoring threads
active_monitors = {}

class SensitivityLogMonitor:
    """
    Class to monitor the SENSITIVITY.log file and emit SSE events.
    This class is designed to be used with the /stream_sensitivity endpoint.
    """
    def __init__(self, version):
        """Initialize the monitor for a specific version."""
        self.version = version
        self.log_file_path = self._get_log_file_path()
        self.running = False
        self.clients = []
        self.last_data = None
        self.last_position = 0
        self.last_check_time = 0
        logger.info(f"Initialized sensitivity monitor for version {version}, log file: {self.log_file_path}")

    def _get_log_file_path(self):
        """Get the path to the SENSITIVITY.log file."""
        # Base directory is two levels up from this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, 'backend', 'Logs', 'SENSITIVITY.log')

    def add_client(self, client_queue):
        """Add a client to the monitor."""
        self.clients.append(client_queue)
        logger.info(f"Client added to sensitivity monitor for version {self.version}. Total clients: {len(self.clients)}")

        # If we already have data, send it to the new client immediately
        if self.last_data:
            client_queue.put(self.last_data)

        # Start the monitoring thread if not already running
        if not self.running:
            self.start()

    def remove_client(self, client_queue):
        """Remove a client from the monitor."""
        if client_queue in self.clients:
            self.clients.remove(client_queue)
            logger.info(f"Client removed from sensitivity monitor for version {self.version}. Remaining clients: {len(self.clients)}")

        # Stop the monitoring thread if no clients remain
        if not self.clients and self.running:
            self.stop()

    def start(self):
        """Start the monitoring thread."""
        self.running = True
        thread = threading.Thread(target=self._monitor_loop)
        thread.daemon = True
        thread.start()
        logger.info(f"Sensitivity monitoring thread started for version {self.version}")

    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        logger.info(f"Sensitivity monitoring stopped for version {self.version}")

        # Remove this monitor from the global active monitors
        if self.version in active_monitors:
            del active_monitors[self.version]

    def _monitor_loop(self):
        """Main monitoring loop to check for file changes and notify clients."""
        check_interval = 0.5  # Check every half second
        consecutive_errors = 0
        max_errors = 20  # Stop monitoring after this many consecutive errors

        # Initialize the last position to the end of the file
        try:
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    f.seek(0, os.SEEK_END)
                    self.last_position = f.tell()
        except Exception as e:
            logger.error(f"Error initializing log monitor: {str(e)}")
            self.last_position = 0

        while self.running and consecutive_errors < max_errors:
            try:
                # Check if the log file exists
                if os.path.exists(self.log_file_path):
                    # Get the current file size
                    file_size = os.path.getsize(self.log_file_path)

                    # If the file has new content
                    if file_size > self.last_position:
                        with open(self.log_file_path, 'r', encoding='utf-8') as f:
                            # Seek to the last position we read
                            f.seek(self.last_position)
                            
                            # Read new lines
                            new_lines = f.readlines()
                            
                            # Update the last position
                            self.last_position = f.tell()

                        # Process new lines
                        if new_lines:
                            # Parse log lines to extract relevant information
                            log_data = self._parse_log_lines(new_lines)
                            
                            if log_data:
                                # Prepare the event data
                                event_data = {
                                    'version': self.version,
                                    'timestamp': datetime.now().isoformat(),
                                    'logEntries': log_data,
                                    'calculationStep': self._extract_calculation_step(new_lines),
                                    'payloadDetails': self._extract_payload_details(new_lines),
                                    'progressPercentage': self._calculate_progress_percentage(log_data)
                                }

                                # Store the last data for new clients
                                self.last_data = event_data

                                # Send the data to all clients
                                for client in self.clients[:]:  # Copy the list to avoid modification during iteration
                                    try:
                                        client.put(event_data)
                                    except Exception as e:
                                        logger.error(f"Error sending data to client: {str(e)}")
                                        # Remove the client if we can't send data to it
                                        self.remove_client(client)

                                # Reset consecutive errors counter
                                consecutive_errors = 0
                    
                    # Check if the file has been truncated (restarted)
                    elif file_size < self.last_position:
                        logger.info(f"Log file has been truncated, resetting position")
                        self.last_position = 0
                        consecutive_errors = 0
                
                # Sleep for the check interval
                time.sleep(check_interval)
            
            except Exception as e:
                logger.error(f"Error in sensitivity monitor loop: {str(e)}")
                consecutive_errors += 1
                time.sleep(check_interval)  # Still sleep to avoid tight loop on errors

        # If we exit due to too many errors, log it
        if consecutive_errors >= max_errors:
            logger.error(f"Stopping sensitivity monitor due to too many consecutive errors")

    def _parse_log_lines(self, lines):
        """Parse log lines to extract relevant information."""
        log_entries = []
        
        for line in lines:
            try:
                # Basic parsing of log line format: timestamp level message
                parts = line.strip().split(' ', 2)
                if len(parts) >= 3:
                    timestamp = ' '.join(parts[0:2])
                    level = parts[2]
                    message = ' '.join(parts[3:]) if len(parts) > 3 else ""
                    
                    # Only include INFO, WARNING, and ERROR messages
                    if any(level_type in level for level_type in ['INFO', 'WARNING', 'ERROR']):
                        log_entries.append({
                            'timestamp': timestamp,
                            'level': level,
                            'message': message
                        })
            except Exception as e:
                logger.error(f"Error parsing log line: {str(e)}")
                continue
        
        return log_entries

    def _extract_calculation_step(self, lines):
        """Extract the current calculation step from log lines."""
        for line in reversed(lines):  # Start from the most recent line
            if "Calculation step:" in line:
                try:
                    return line.split("Calculation step:", 1)[1].strip()
                except Exception:
                    pass
        return None

    def _extract_payload_details(self, lines):
        """Extract payload details from log lines."""
        for line in reversed(lines):  # Start from the most recent line
            if "Payload details:" in line:
                try:
                    payload_json = line.split("Payload details:", 1)[1].strip()
                    return json.loads(payload_json)
                except Exception:
                    pass
        return {}

    def _calculate_progress_percentage(self, log_data):
        """Calculate an approximate progress percentage based on log entries."""
        # This is a simplified implementation
        # In a real implementation, you would need to analyze the log entries
        # to determine the progress based on known steps in the process
        
        # For now, just return a fixed value or None
        return None

# Function to create a new endpoint in Flask
def create_sensitivity_stream_endpoint(app):
    """
    Create a new endpoint to stream SENSITIVITY.log messages.
    
    Args:
        app: The Flask application instance
    """
    @app.route('/stream_sensitivity/<version>', methods=['GET'])
    def stream_sensitivity(version):
        """
        Stream real-time sensitivity analysis updates for a specific version using Server-Sent Events (SSE).
        This endpoint connects to a SensitivityLogMonitor that watches the SENSITIVITY.log file for changes.
        """
        def generate():
            """Generator function for the SSE stream."""
            # Create a queue for this client
            client_queue = Queue()

            # Get or create a monitor for this version
            if version not in active_monitors:
                active_monitors[version] = SensitivityLogMonitor(version)

            # Add this client to the monitor
            active_monitors[version].add_client(client_queue)

            try:
                # Send initial connection message
                yield f"data: {json.dumps({'status': 'connected', 'version': version, 'timestamp': datetime.now().isoformat()})}\n\n"

                while True:
                    # Wait for data from the monitor with a timeout
                    try:
                        data = client_queue.get(timeout=30)  # 30 second timeout
                        yield f"data: {json.dumps(data)}\n\n"
                    except Exception:
                        # Send a heartbeat after timeout to keep connection alive
                        yield f"data: {json.dumps({'heartbeat': True, 'timestamp': datetime.now().isoformat()})}\n\n"
            except GeneratorExit:
                # Client disconnected
                logger.info(f"Client disconnected from sensitivity stream for version {version}")
                pass
            finally:
                # Remove this client from the monitor
                if version in active_monitors:
                    active_monitors[version].remove_client(client_queue)
                    logger.info(f"Client removed from sensitivity monitor for version {version}")

        return app.response_class(generate(), mimetype='text/event-stream')