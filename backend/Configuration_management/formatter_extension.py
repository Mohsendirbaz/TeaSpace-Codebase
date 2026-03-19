import os
import sys
import re
from pathlib import Path

# Configuration and Setup
script_dir = Path(__file__).resolve().parent.parent
UPLOAD_DIR = script_dir.parent / "Original"

def check_write_permissions(directory):
    """Verify write permissions for the target directory."""
    try:
        if os.access(directory, os.W_OK):
            print(f"Write permission granted for directory: {directory}")
        else:
            print(f"No write permission for directory: {directory}")
    except Exception as e:
        print(f"Error checking permissions for {directory}: {e}")

# Initialize permissions check
check_write_permissions(UPLOAD_DIR)

# Value Processing Functions
def format_value(value, quote=True):
    """Format values according to configuration requirements.
    
    Args:
        value: The value to format
        quote: Boolean indicating if the value should be quoted
    Returns:
        Formatted value as string
    """
    if quote:
        return f'"{value.strip()}"'
    return value

def medieval_parse_and_sanitize(content):
    """Parse and sanitize configuration content.
    
    Args:
        content: Raw configuration content to process
    Returns:
        tuple: (sanitized_lines, filtered_values_json)
    """
    sanitized_lines = []
    filtered_values_json = []

    # Vector Initialization
    variable_costsAmount4 = [None] * 10
    amounts_per_unitAmount5 = [None] * 10
    
    # Process FilteredValues Section
    filtered_values_start = content.find('"filteredValues":[')
    if filtered_values_start != -1:
        filtered_values_start += len('"filteredValues":[')
        filtered_values_end = content.find(']', filtered_values_start)
        filtered_values_content = content[filtered_values_start:filtered_values_end]
        
        # Extract and Process Values
        while True:
            id_start = filtered_values_content.find('"id":"')
            if id_start == -1:
                break
            id_start += len('"id":"')
            id_end = filtered_values_content.find('"', id_start)
            id_value = filtered_values_content[id_start:id_end]
            
            value_start = filtered_values_content.find('"value":', id_end)
            if value_start == -1:
                break
            value_start += len('"value":')
            value_end = filtered_values_content.find(',', value_start)
            if filtered_values_content[value_start] == '"':
                value_end = filtered_values_content.find('"', value_start + 1) + 1
                value_value = filtered_values_content[value_start:value_end]
            else:
                value_end = filtered_values_content.find(',', value_start)
                if value_end == -1:
                    value_end = filtered_values_content.find('}', value_start)
                value_value = filtered_values_content[value_start:value_end]

            # Value Formatting
            if id_value == "use_direct_operating_expensesAmount18":
                if value_value == '"True"':
                    value_value = "True"
                elif value_value == '"False"':
                    value_value = "False"
            elif "Amount4" in id_value or "Amount5" in id_value:
                value_value = value_value.strip()
            else:
                if value_value.startswith('"') and value_value.endswith('"'):
                    value_value = f"'{value_value[1:-1]}'"
            
            # Value Processing
            stripped_value = value_value.strip()
            if stripped_value.isdigit():
                stripped_value = int(stripped_value)
            else:
                try:
                    stripped_value = float(stripped_value)
                except ValueError:
                    pass

            # Vector Assignment
            if "Amount4" in id_value:
                for i in range(len(variable_costsAmount4)):
                    if variable_costsAmount4[i] is None:
                        variable_costsAmount4[i] = stripped_value
                        break
            elif "Amount5" in id_value:
                for i in range(len(amounts_per_unitAmount5)):
                    if amounts_per_unitAmount5[i] is None:
                        amounts_per_unitAmount5[i] = stripped_value
                        break

            # Line Generation
            if "Amount4" in id_value or "Amount5" in id_value:
                sanitized_lines.append(f'{id_value}={stripped_value}')
            else:
                sanitized_lines.append(f'{id_value}={value_value}')

            filtered_values_content = filtered_values_content[value_end:]
    
    # Process FilteredValue Entries
    content_lines = content.splitlines()
    for line in content_lines:
        if '"filteredValue":{' in line:
            start_match = re.search(r'"start":\s*([^,]+)', line)
            end_match = re.search(r'"end":\s*([^,]+)', line)
            value_match = re.search(r'"value":\s*([^,]+)', line)
            id_match = re.search(r'"id":"([^"]+)"', line)
            remarks_match = re.search(r'"remarks":"([^"]+)"', line)

            formatted_value = format_value(value_match.group(1)) if value_match else ''
            formatted_start = f'"{start_match.group(1)}"' if start_match else ''
            formatted_end = f'"{end_match.group(1)}"' if end_match else ''
            formatted_id = id_match.group(1) if id_match else ''
            formatted_remarks = remarks_match.group(1) if remarks_match else ''

            filtered_value_line = f'{{"filteredValue":{{"id":"{formatted_id}","value":{formatted_value},"start":{formatted_start},"end":{formatted_end},"remarks":"{formatted_remarks}"}}}}'
            filtered_values_json.append(filtered_value_line.strip())

    # Vector Output
    sanitized_lines.append(f"variable_costsAmount4={variable_costsAmount4}")
    sanitized_lines.append(f"amounts_per_unitAmount5={amounts_per_unitAmount5}")
    
    return '\n'.join(sanitized_lines), filtered_values_json

def sanitize_file(version, extension):
    """Process and sanitize configuration files for a specific version.
    
    Args:
        version: Version number for configuration processing
        extension: Extension number for the batch
    Returns:
        dict: Result status of the operation
    """
    # Path Configuration
    original_file_path = UPLOAD_DIR / f'Batch({version}.{extension})/ConfigurationPlotSpec({version})/U_configurations({version}).py'
    sanitized_file_path = UPLOAD_DIR / f'Batch({version}.{extension})/ConfigurationPlotSpec({version})/configurations({version}).py'

    print(f"Sanitizing file for version: {version} extension: {extension}")
    print(f"Original file path: {original_file_path}")
    print(f"Sanitized file path: {sanitized_file_path}")

    # Directory Creation
    try:
        original_file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating directories: {e}")
        return {"error": f"Error creating directories: {e}"}

    # Check if original file exists
    if not original_file_path.exists():
        error_msg = f"Original file not found: {original_file_path}"
        print(error_msg)
        return {"error": error_msg}

    # File Reading
    try:
        raw_content = original_file_path.read_text(encoding='utf-8')
        print(f"Successfully read {len(raw_content)} characters from file")
    except Exception as e:
        error_msg = f"Error reading from original file at {original_file_path}: {e}"
        print(error_msg)
        return {"error": error_msg}

    # Content Processing
    try:
        sanitized_content, filtered_values_json = medieval_parse_and_sanitize(raw_content)
        print(f"Successfully processed content, generated {len(filtered_values_json)} filtered values")
    except Exception as e:
        error_msg = f"Error processing content: {e}"
        print(error_msg)
        return {"error": error_msg}

    # File Writing
    try:
        with open(sanitized_file_path, 'w', encoding='utf-8') as f:
            f.write(sanitized_content)
            f.write("\n\nfiltered_values_json=[\n")
            for entry in filtered_values_json:
                f.write(f"   '{entry}',\n")
            f.write("]\n")
        print(f"Successfully wrote sanitized file to {sanitized_file_path}")
        return {"message": "Sanitized file written successfully"}
    except Exception as e:
        error_msg = f"Error writing to sanitized file at {sanitized_file_path}: {e}"
        print(error_msg)
        return {"error": error_msg}

if __name__ == '__main__':
    version = sys.argv[1] if len(sys.argv) > 1 else 1
    extension = sys.argv[2] if len(sys.argv) > 2 else 1
    sanitize_file(version, extension)
