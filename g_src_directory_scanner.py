"""Directory structure analyzer using established core utilities"""
import os
from typing import Dict, Any
import json
from datetime import datetime
# Import using a proper relative import syntax
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.Data_processors_and_transformers.file_utils import find_versions, find_files

def analyze_directory_structure(base_path: str) -> Dict[str, Any]:
    # Initialize structure with metadata
    structure = {
        "project_name": "src",
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": 6,
        "directories": {}
    }
    
    # Process root directory
    structure["directories"]["."] = {
        "files": [f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f))],
        "import_count": len([f for f in os.listdir(base_path) if f.endswith('.js')])
    }
    
    # Process subdirectories
    for root, dirs, files in os.walk(base_path):
        rel_path = os.path.relpath(root, base_path)
        if rel_path != ".":
            js_files = [f for f in files if f.endswith('.js')]
            structure["directories"][rel_path] = {
                "files": [os.path.join(rel_path, f) for f in files],
                "import_count": len(js_files)
            }

    # Add file details by extension
    structure["files_by_extension"] = {}
    for ext in ['.js', '.css', '.jsx']:
        structure["files_by_extension"][ext.lstrip('.')] = []
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith(ext):
                    rel_path = os.path.relpath(root, base_path)
                    structure["files_by_extension"][ext.lstrip('.')].append({
                        "name": file,
                        "path": os.path.join(rel_path, file),
                        "size": os.path.getsize(os.path.join(root, file))
                    })

    return structure

def save_structure(structure: Dict[str, Any], output_file: str) -> None:
    with open(output_file, 'w') as f:
        json.dump(structure, f, indent=2)

def main():
    # Use relative paths
    current_dir = os.path.dirname(__file__)
    output_file = os.path.join(current_dir, "g_src_directory_scanner.json")
    Base_dir = os.path.join(current_dir, "src")

    if not os.path.exists(Base_dir):
        print(f"Directory not found: {Base_dir}")
        return
        
    structure = analyze_directory_structure(Base_dir)
    save_structure(structure, output_file)
    print(f"Directory structure analysis saved to: {output_file}")
    
    # Summary statistics
    total_files = sum(len(d["files"]) for d in structure["directories"].values())
    total_dirs = len(structure["directories"])
    print(f"\nAnalysis Summary:")
    print(f"Total directories: {total_dirs}")
    print(f"Total files: {total_files}")
    print(f"File types found: {', '.join(structure['files_by_extension'].keys())}")

if __name__ == "__main__":
    main()
