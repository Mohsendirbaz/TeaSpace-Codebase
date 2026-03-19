import json
import os
import argparse
from datetime import datetime

def analyze_backend_directory(backend_path, output_path):
    """
    Creates a JSON file representing the directory structure of the backend,
    excluding the Original folder.
    """
    directory_structure = {
        "project_name": "Backend Structure",
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": 1,
        "directories": {}
    }

    for root, dirs, files in os.walk(backend_path):

        # Get relative path from target directory
        rel_path = os.path.relpath(root, backend_path)
        if rel_path == ".":
            continue

        # Add directory to structure with absolute path references
        directory_structure["directories"][rel_path] = {
            "absolute_path": os.path.abspath(root),
            "files": [os.path.join(rel_path, f) for f in files],
            "import_count": len(files)
        }

    # Write the output JSON file
    with open(output_path, 'w') as f:
        json.dump(directory_structure, f, indent=2)

    return output_path

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Analyze backend directory structure')
    parser.add_argument('--backend_path', type=str, default=r"C:\Users\Mohse\IdeaProjects2\codebase\backend\Original",
                        help='Absolute path to the backend directory to analyze')
    parser.add_argument('--output_path', type=str,
                        help='Absolute path for the output JSON file. If not provided, will use the backend directory')

    args = parser.parse_args()
    current_script_path = os.path.dirname(os.path.abspath(__file__))

    # Use the provided paths
    backend_path = args.backend_path

    # If output path is not provided, create one in the backend directory
    if not args.output_path:
        output_path = os.path.join(current_script_path, "c_backend_directory_structure.json")
    else:
        output_path = args.output_path

    try:
        result_path = analyze_backend_directory(backend_path, output_path)
        print(f"Directory structure analysis complete. Output saved to {result_path}")
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    main()