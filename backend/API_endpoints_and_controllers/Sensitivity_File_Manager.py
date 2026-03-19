import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional

class SensitivityFileManager:
    _instance = None

    @classmethod
    def get_instance(cls, base_dir: str = None):
        if cls._instance is None:
            if base_dir is None:
                raise ValueError("base_dir must be provided for first initialization")
            cls._instance = cls.__new__(cls)
            cls._instance.__init__(base_dir)
        return cls._instance

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.logger = logging.getLogger('sensitivity_file_manager')

        # Define standard directory structure
        self.directory_structure = {
            'configurations': 'ConfigurationPlotSpec',
            'results': 'Results',
            'sensitivity': {
                'symmetrical': 'Symmetrical',
                'multipoint': 'Multipoint'
            },
            'reports': 'Analysis_Reports',
            'cache': 'Calculation_Cache'
        }

        # Initialize directory structure
        self._initialize_directories()

    def _initialize_directories(self):
        """Creates the standard directory structure if it doesn't exist."""
        try:
            batch_path = os.path.join(self.base_dir, 'Batch(1)')

            # Create main directories
            for dir_type, dir_name in self.directory_structure.items():
                if isinstance(dir_name, dict):
                    # Handle nested directories (like sensitivity)
                    parent_dir = os.path.join(batch_path, 'Results(1)', 'Sensitivity')
                    os.makedirs(parent_dir, exist_ok=True)

                    for subdir_type, subdir_name in dir_name.items():
                        os.makedirs(os.path.join(parent_dir, subdir_name), exist_ok=True)

                        # Create plot type subdirectories
                        for plot_type in ['waterfall', 'bar', 'point', 'Configuration']:
                            os.makedirs(os.path.join(parent_dir, subdir_name, plot_type), exist_ok=True)
                else:
                    os.makedirs(os.path.join(batch_path, f'{dir_name}(1)'), exist_ok=True)

            # Create reports directory
            reports_dir = os.path.join(batch_path, 'Results(1)', 'Reports')
            os.makedirs(reports_dir, exist_ok=True)

            # Create additional directories
            cache_dir = os.path.join(batch_path, 'Results(1)', 'Calculation_Cache')
            os.makedirs(cache_dir, exist_ok=True)

        except Exception as e:
            self.logger.error(f"Error initializing directory structure: {str(e)}")
            raise

    def ensure_directories_exist(self, version: int):
        """Ensures all required directories exist for the specified version."""
        try:
            batch_path = os.path.join(self.base_dir, f'Batch({version})')

            # Create main directories
            for dir_type, dir_name in self.directory_structure.items():
                if isinstance(dir_name, dict):
                    # Handle nested directories (like sensitivity)
                    parent_dir = os.path.join(batch_path, f'Results({version})', 'Sensitivity')
                    os.makedirs(parent_dir, exist_ok=True)

                    for subdir_type, subdir_name in dir_name.items():
                        os.makedirs(os.path.join(parent_dir, subdir_name), exist_ok=True)

                        # Create plot type subdirectories
                        for plot_type in ['waterfall', 'bar', 'point', 'Configuration']:
                            os.makedirs(os.path.join(parent_dir, subdir_name, plot_type), exist_ok=True)
                else:
                    os.makedirs(os.path.join(batch_path, f'{dir_name}({version})'), exist_ok=True)

            # Create reports directory
            reports_dir = os.path.join(batch_path, f'Results({version})', 'Reports')
            os.makedirs(reports_dir, exist_ok=True)

            # Create additional directories
            cache_dir = os.path.join(batch_path, f'Results({version})', 'Calculation_Cache')
            os.makedirs(cache_dir, exist_ok=True)

        except Exception as e:
            self.logger.error(f"Error ensuring directories exist for version {version}: {str(e)}")
            raise

    def get_plot_path(self, version: int, mode: str, plot_type: str, param_id: str,
                      compare_to_key: str, comparison_type: str) -> dict:
        """
        Constructs the full path for a plot file and returns its status.

        Args:
            version (int): Version number
            mode (str): Either 'symmetrical' or 'multipoint'
            plot_type (str): Plot type (waterfall, bar, point)
            param_id (str): Parameter ID
            compare_to_key (str): Comparison parameter ID
            comparison_type (str): Comparison type

        Returns:
            dict: Plot information including path and status
        """
        # Normalize mode
        mode_dir = 'Symmetrical' if mode.lower() in ['symmetrical', 'percentage', 'multiple'] else 'Multipoint'

        plot_name = f"{plot_type}_{param_id}_{compare_to_key}_{comparison_type}.png"
        full_path = os.path.join(
            self.base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Sensitivity',
            mode_dir,
            plot_type,
            plot_name
        )

        plot_info = {
            'name': plot_name,
            'full_path': full_path,
            'relative_path': None,
            'status': 'not_found',
            'error': None,
            'metadata': {
                'version': version,
                'mode': mode,
                'plot_type': plot_type,
                'param_id': param_id,
                'compare_to_key': compare_to_key,
                'comparison_type': comparison_type,
                'last_modified': None,
                'file_size': None
            }
        }

        try:
            if os.path.exists(full_path):
                plot_info.update({
                    'status': 'ready',
                    'relative_path': os.path.relpath(full_path, self.base_dir),
                    'error': None,
                    'metadata': {
                        **plot_info['metadata'],
                        'last_modified': os.path.getmtime(full_path),
                        'file_size': os.path.getsize(full_path)
                    }
                })
            else:
                # Try alternate location (directly in mode directory)
                alt_path = os.path.join(
                    self.base_dir,
                    f'Batch({version})',
                    f'Results({version})',
                    'Sensitivity',
                    mode_dir,
                    plot_name
                )

                if os.path.exists(alt_path):
                    plot_info.update({
                        'status': 'ready',
                        'full_path': alt_path,
                        'relative_path': os.path.relpath(alt_path, self.base_dir),
                        'error': None,
                        'metadata': {
                            **plot_info['metadata'],
                            'last_modified': os.path.getmtime(alt_path),
                            'file_size': os.path.getsize(alt_path)
                        }
                    })
                else:
                    plot_info['error'] = f"Plot file not found: {plot_name}"
        except Exception as e:
            plot_info.update({
                'status': 'error',
                'error': str(e)
            })
            self.logger.error(f"Error getting plot info for {plot_name}: {str(e)}")

        return plot_info

    def store_calculation_result(self, version: int, param_id: str,
                                 result_data: Dict, mode: str,
                                 compare_to_key: Optional[str] = None) -> dict:
        """
        Stores calculation results in JSON format with metadata.

        Args:
            version (int): Version number
            param_id (str): Parameter ID
            result_data (dict): Calculation results
            mode (str): Either 'symmetrical' or 'multipoint'
            compare_to_key (str, optional): Comparison parameter ID

        Returns:
            dict: Result information including path and status
        """
        # Normalize mode
        mode_dir = 'Symmetrical' if mode.lower() in ['symmetrical', 'percentage', 'multiple'] else 'Multipoint'

        result_info = {
            'path': None,
            'status': 'error',
            'error': None,
            'metadata': {
                'version': version,
                'param_id': param_id,
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'size': 0
            }
        }

        try:
            # Standard result file for parameter
            result_path = os.path.join(
                self.base_dir,
                f'Batch({version})',
                f'Results({version})',
                'Sensitivity',
                mode_dir,
                f"{param_id}_results.json"
            )

            # Ensure directory exists
            os.makedirs(os.path.dirname(result_path), exist_ok=True)

            with open(result_path, 'w') as f:
                json.dump(result_data, f, indent=4)

            result_info.update({
                'path': result_path,
                'status': 'success',
                'metadata': {
                    **result_info['metadata'],
                    'size': os.path.getsize(result_path)
                }
            })

            self.logger.info(f"Stored calculation result for {param_id} at {result_path}")

            # If compare_to_key is provided, store comparison-specific result
            if compare_to_key:
                comparison_path = os.path.join(
                    self.base_dir,
                    f'Batch({version})',
                    f'Results({version})',
                    'Sensitivity',
                    mode_dir,
                    f"{param_id}_vs_{compare_to_key}_{mode.lower()}_results.json"
                )

                # Create a copy of result_data with comparison info
                comparison_data = {
                    **result_data,
                    'compareToKey': compare_to_key
                }

                with open(comparison_path, 'w') as f:
                    json.dump(comparison_data, f, indent=4)

                self.logger.info(f"Stored comparison result at {comparison_path}")
                result_info['comparison_path'] = comparison_path

        except Exception as e:
            error_msg = f"Error storing calculation result: {str(e)}"
            result_info['error'] = error_msg
            self.logger.error(error_msg)

        return result_info

    def create_analysis_report(self, version: int, analysis_data: Dict) -> str:
        """
        Creates an HTML report from analysis results.

        Args:
            version (int): Version number
            analysis_data (dict): Analysis data

        Returns:
            str: Path to generated report
        """
        report_dir = os.path.join(
            self.base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Reports'
        )
        os.makedirs(report_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(report_dir, f'sensitivity_analysis_{timestamp}.html')

        # Generate HTML content
        html_content = self._generate_html_report(analysis_data, version)

        with open(report_path, 'w') as f:
            f.write(html_content)

        return report_path

    def _generate_html_report(self, analysis_data: Dict, version: int) -> str:
        """
        Generates HTML content for the analysis report.

        Args:
            analysis_data (dict): Analysis data
            version (int): Version number

        Returns:
            str: HTML content
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sensitivity Analysis Report - Version {version}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .plot-container {{ margin: 20px 0; }}
                .result-table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                .result-table th, .result-table td {{ 
                    border: 1px solid #ddd; padding: 8px; text-align: left; 
                }}
                .parameter-section {{ margin-bottom: 40px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
                .variation-label {{ font-weight: bold; color: #333; }}
                .comparison-value {{ color: #0066cc; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Sensitivity Analysis Report</h1>
            <h2>Version {version}</h2>
        """

        # Add analysis sections
        for param_id, data in analysis_data.items():
            html += f"""
            <div class="parameter-section">
                <h3>Parameter: {param_id}</h3>
                <p>Analysis Mode: {data.get('mode', 'Not specified')}</p>
            """

            # Add plots if available
            if 'plots' in data and data['plots']:
                html += """<div class="plot-container">"""
                for plot_type, plot_path in data['plots'].items():
                    html += f"""
                    <div class="plot-item">
                        <h4>{plot_type.capitalize()} Plot</h4>
                        <img src="{plot_path}" alt="{plot_type} plot" style="max-width: 100%; margin: 10px 0;">
                    </div>
                    """
                html += """</div>"""

            # Add results table if available
            if 'results' in data and data['results']:
                html += """
                <h4>Analysis Results</h4>
                <table class="result-table">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                """

                for metric, value in data['results'].items():
                    html += f"""<tr><td>{metric}</td><td>{value}</td></tr>"""

                html += """</table>"""

            # Add variations if available
            if 'variations' in data and data['variations']:
                html += """
                <h4>Variations</h4>
                <table class="result-table">
                    <tr>
                        <th>Variation</th>
                        <th>Result</th>
                    </tr>
                """

                for variation in data['variations']:
                    var_str = variation.get('variation_str', str(variation.get('variation', 'N/A')))
                    result_value = variation.get('values', {}).get('price', 'N/A')
                    html += f"""<tr>
                        <td class="variation-label">{var_str}</td>
                        <td class="comparison-value">{result_value}</td>
                    </tr>"""

                html += """</table>"""

            html += """</div>"""

        html += """
        </body>
        </html>
        """

        return html

    def cache_calculation_data(self, version: int, param_id: str,
                               calculation_data: Dict) -> str:
        """
        Caches intermediate calculation results.

        Args:
            version (int): Version number
            param_id (str): Parameter ID
            calculation_data (dict): Calculation data

        Returns:
            str: Path to cache file
        """
        cache_dir = os.path.join(
            self.base_dir,
            f'Batch({version})',
            f'Results({version})',
            'Calculation_Cache'
        )
        os.makedirs(cache_dir, exist_ok=True)

        cache_path = os.path.join(cache_dir, f"{param_id}_cache.json")

        with open(cache_path, 'w') as f:
            json.dump(calculation_data, f, indent=4)

        self.logger.info(f"Cached calculation data for {param_id} at {cache_path}")
        return cache_path

    def cleanup_cache(self, version: int, older_than_days: int = 7) -> dict:
        """
        Cleans up cached calculation data older than specified days.

        Args:
            version (int): Version number
            older_than_days (int): Age threshold in days

        Returns:
            dict: Cleanup operation results
        """
        cleanup_info = {
            'files_removed': [],
            'errors': [],
            'total_space_freed': 0
        }

        try:
            cache_dir = os.path.join(
                self.base_dir,
                f'Batch({version})',
                f'Results({version})',
                'Calculation_Cache'
            )

            if not os.path.exists(cache_dir):
                return cleanup_info

            current_time = datetime.now()
            for file_name in os.listdir(cache_dir):
                try:
                    file_path = os.path.join(cache_dir, file_name)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

                    if (current_time - file_modified).days > older_than_days:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleanup_info['files_removed'].append({
                            'name': file_name,
                            'path': file_path,
                            'size': file_size,
                            'age_days': (current_time - file_modified).days
                        })
                        cleanup_info['total_space_freed'] += file_size

                except Exception as e:
                    cleanup_info['errors'].append({
                        'file': file_name,
                        'error': str(e)
                    })
                    self.logger.error(f"Error cleaning up {file_name}: {str(e)}")

            self.logger.info(
                f"Cache cleanup completed: removed {len(cleanup_info['files_removed'])} files, "
                f"freed {cleanup_info['total_space_freed']} bytes"
            )

        except Exception as e:
            error_msg = f"Error during cache cleanup: {str(e)}"
            cleanup_info['errors'].append({'error': error_msg})
            self.logger.error(error_msg)

        return cleanup_info

    def archive_analysis(self, version: int, archive_name: Optional[str] = None) -> str:
        """
        Archives analysis results and reports.

        Args:
            version (int): Version number
            archive_name (str, optional): Custom archive name

        Returns:
            str: Path to archive
        """
        if not archive_name:
            archive_name = f"sensitivity_analysis_v{version}_{datetime.now().strftime('%Y%m%d')}"

        source_dir = os.path.join(
            self.base_dir,
            f'Batch({version})',
            f'Results({version})'
        )

        archives_dir = os.path.join(self.base_dir, 'Archives')
        os.makedirs(archives_dir, exist_ok=True)

        archive_path = os.path.join(archives_dir, f"{archive_name}.zip")

        shutil.make_archive(
            os.path.splitext(archive_path)[0],
            'zip',
            source_dir
        )

        self.logger.info(f"Created archive at {archive_path}")
        return archive_path
