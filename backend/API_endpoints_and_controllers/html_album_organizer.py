#!/usr/bin/env python
"""
Enhanced HTML Album Organizer

This script organizes HTML plot files into standardized album directories for
the DynamicSubPlot tab. It offers improved organization, metadata generation,
and consistency in file naming/structure.

Enhancements:
- Improved metadata for frontend integration
- Better organization by plot type and version
- Support for multiple version combinations
- Consistent naming conventions
- Better error handling and logging
"""

import os
import shutil
import logging
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("html_album_organizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def safe_json_dump(data: Any, file_path: Union[str, Path]) -> bool:
    """Safely write JSON data to a file with error handling

    Args:
        data: The data to serialize to JSON
        file_path: Path to the output file

    Returns:
        bool: True if successful, False on error
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON to {file_path}: {e}")
        return False

def ensure_directory_exists(directory_path: Union[str, Path]) -> None:
    """Ensure the specified directory exists, creating it if necessary

    Args:
        directory_path: Path to the directory
    """
    os.makedirs(directory_path, exist_ok=True)

def organize_html_albums(base_dir: Optional[Union[str, Path]] = None,
                         specified_versions: Optional[List[int]] = None) -> bool:
    """
    Organizes HTML plot files into standardized album directories that are compatible
    with the Front_Subtab_HTML.py server and enhances them for the DynamicSubPlot tab.

    Args:
        base_dir: Base directory containing batch folders (optional)
        specified_versions: List of version numbers to process (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    # Determine base directory
    if not base_dir:
        # Use same path logic as in the main scripts
        backend_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base_dir = backend_dir.parent / 'Original'

    if not os.path.exists(base_dir):
        logger.error(f"Base directory does not exist: {base_dir}")
        return False

    # Get all version directories
    logger.info(f"Scanning for version directories in {base_dir}")

    all_batches = [d for d in os.listdir(base_dir)
                   if d.startswith("Batch(") and d.endswith(")")]

    # Filter to specified versions if provided
    if specified_versions:
        batches = [f"Batch({v})" for v in specified_versions if f"Batch({v})" in all_batches]
        logger.info(f"Processing specified versions: {specified_versions}")
    else:
        batches = all_batches

    if not batches:
        logger.warning("No batch directories found")
        return False

    # Track all created albums for index generation
    all_created_albums = []

    # Process each batch directory
    for batch in batches:
        # Extract version number
        version_match = re.match(r"Batch\((\d+)\)", batch)
        if not version_match:
            logger.warning(f"Invalid batch directory format: {batch}")
            continue

        version = version_match.group(1)
        results_dir = os.path.join(base_dir, batch, f"Results({version})")

        if not os.path.exists(results_dir):
            logger.warning(f"Results directory not found: {results_dir}")
            continue

        # Find HTML plot directories (v*_*_Plot)
        plot_dirs = [d for d in os.listdir(results_dir)
                     if os.path.isdir(os.path.join(results_dir, d)) and
                     (d.startswith("v") and "_Plot" in d)]

        if not plot_dirs:
            logger.info(f"No HTML plot directories found for version {version}")
            continue

        # Categorize plot directories by type
        categorized_plots = {}  # Plot type -> list of directory names
        for plot_dir_name in plot_dirs:
            # Extract the metric name and versions identifier from directory name
            dir_match = re.match(r"v(\d+(?:_\d+)*)_(.+)_Plot", plot_dir_name)
            if not dir_match:
                dir_match = re.match(r"v(\d+(?:_\d+)*)_(.+)", plot_dir_name)
                if not dir_match:
                    logger.warning(f"Invalid plot directory format: {plot_dir_name}")
                    continue

            versions_id = dir_match.group(1)
            plot_type = dir_match.group(2)

            if plot_type not in categorized_plots:
                categorized_plots[plot_type] = []

            categorized_plots[plot_type].append((versions_id, plot_dir_name))

        # Process each plot type
        for plot_type, dirs in categorized_plots.items():
            # Create a mapping of versions_id -> directories
            versions_map = {}
            for versions_id, dir_name in dirs:
                if versions_id not in versions_map:
                    versions_map[versions_id] = []
                versions_map[versions_id].append(dir_name)

            # Process each version combination
            for versions_id, dir_names in versions_map.items():
                # Create standardized album name:
                # Format: HTML_v{versions_id}_{plot_type}
                album_name = f"HTML_v{versions_id}_{plot_type}"
                album_dir = os.path.join(results_dir, album_name)

                # Create album directory
                ensure_directory_exists(album_dir)
                logger.info(f"Created HTML album directory: {album_dir}")

                # Track created album
                all_created_albums.append({
                    "version": version,
                    "versions_id": versions_id,
                    "plot_type": plot_type,
                    "album_name": album_name,
                    "path": album_dir
                })

                # Copy files from all source directories to the album
                html_files = []
                for dir_name in dir_names:
                    source_dir = os.path.join(results_dir, dir_name)
                    for file_name in os.listdir(source_dir):
                        if file_name.lower().endswith('.html'):
                            html_files.append(file_name)
                            src_path = os.path.join(source_dir, file_name)
                            dest_path = os.path.join(album_dir, file_name)

                            # Only copy if file doesn't exist or is different
                            if not os.path.exists(dest_path) or os.path.getsize(src_path) != os.path.getsize(dest_path):
                                shutil.copy2(src_path, dest_path)
                                logger.info(f"Copied {file_name} to album {album_name}")
                            else:
                                logger.info(f"File {file_name} already exists in album {album_name}, skipping")

                # Create a metadata file to help with frontend rendering
                metadata_path = os.path.join(album_dir, "album_metadata.json")

                # Convert versions_id to a list of integers
                version_numbers = [int(v) for v in versions_id.split('_')]

                metadata = {
                    "album_id": album_name,
                    "version": version,
                    "versions": version_numbers,
                    "versions_identifier": versions_id,
                    "plot_type": plot_type,
                    "metric_name": plot_type,
                    "display_name": f"{plot_type.replace('_', ' ')} for versions [{versions_id.replace('_', ', ')}]",
                    "html_files": html_files,
                    "description": f"Interactive visualization of {plot_type.replace('_', ' ')} across multiple versions",
                    "category": "financial_analysis",
                    "created": True
                }

                safe_json_dump(metadata, metadata_path)
                logger.info(f"Created metadata file for album {album_name}")

    # Create index file with all albums
    if all_created_albums:
        index_path = os.path.join(base_dir, "html_albums_index.json")
        album_index = {
            "albums": all_created_albums,
            "count": len(all_created_albums),
            "types": list(set(album["plot_type"] for album in all_created_albums)),
            "versions": list(set(album["version"] for album in all_created_albums))
        }

        safe_json_dump(album_index, index_path)
        logger.info(f"Created HTML albums index at {index_path}")

    logger.info("HTML album organization completed successfully")
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Organize HTML albums for visualization')
    parser.add_argument('--base-dir', type=str, help='Base directory containing batch folders')
    parser.add_argument('--versions', type=str, help='Comma-separated list of versions to process')

    args = parser.parse_args()

    # Process versions argument
    specified_versions = None
    if args.versions:
        try:
            specified_versions = [int(v.strip()) for v in args.versions.split(',') if v.strip()]
            logger.info(f"Processing specified versions: {specified_versions}")
        except ValueError:
            logger.error(f"Invalid versions format: {args.versions}")
            specified_versions = None

    return args.base_dir, specified_versions

if __name__ == "__main__":
    # Parse command line arguments
    base_dir, specified_versions = parse_arguments()

    # Run the organization process
    organize_html_albums(base_dir, specified_versions)
