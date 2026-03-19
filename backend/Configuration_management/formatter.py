import os
import sys
import re
from pathlib import Path

# =====================================================================
# FORMATTER MODULE
# =====================================================================
# This module is responsible for processing and sanitizing configuration files.
# It reads raw configuration data, processes it into a standardized format,
# and writes sanitized configuration files that can be used by other modules.
#
# The module handles:
# 1. Reading raw configuration files with unprocessed data
# 2. Parsing and extracting filtered values and their properties
# 3. Formatting values according to their data types
# 4. Processing vector assignments for special properties
# 5. Writing sanitized configuration files with proper formatting
# =====================================================================

# Configuration and Setup
# Determine the script directory and set up the upload directory path
script_dir = Path(__file__).resolve().parent.parent
UPLOAD_DIR = script_dir.parent / "Original"

def check_write_permissions(directory):
    """Verify write permissions for the target directory.

    This function checks if the script has write permissions to the specified directory.
    It's important to verify permissions before attempting to write files to avoid
    runtime errors during file operations.

    Args:
        directory (Path or str): The directory path to check for write permissions

    Returns:
        None: Results are printed to console

    Raises:
        Exception: Catches and prints any exceptions that occur during permission checking
    """
    try:
        if os.access(directory, os.W_OK):
            print(f"Write permission granted for directory: {directory}")
        else:
            print(f"No write permission for directory: {directory}")
    except Exception as e:
        print(f"Error checking permissions for {directory}: {e}")

# Initialize permissions check
# This is executed when the module is loaded to ensure the upload directory is writable
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

    This function performs the core processing of raw configuration content.
    It extracts filtered values, processes them according to their data types,
    handles special cases like boolean values and vector assignments, and
    generates both sanitized configuration lines and JSON representations
    of filtered values.

    The function name "medieval" refers to the somewhat archaic parsing approach
    used, which relies on string manipulation rather than modern JSON parsing,
    due to the specific format requirements of the configuration files.

    Args:
        content (str): Raw configuration content to process, typically read from a file

    Returns:
        tuple: A tuple containing:
            - sanitized_lines (str): Processed configuration content as a string with newlines
            - filtered_values_json (list): List of JSON strings representing filtered values

    Processing Steps:
        1. Initialize output containers and vector storage
        2. Extract and process the filteredValues section
        3. Parse individual filtered values and their properties
        4. Format values according to their types and special cases
        5. Handle vector assignments for Amount4 and Amount5
        6. Generate sanitized configuration lines
        7. Process filteredValue entries using regex
        8. Append vector values to the output
    """
    # Initialize output containers for processed configuration lines and JSON values
    sanitized_lines = []
    filtered_values_json = []

    # Vector Initialization
    # These vectors store special values that need to be collected and processed together
    # Each vector has 10 slots that will be filled with values from the configuration
    variable_costsAmount4 = [None] * 10  # Storage for variable costs values
    amounts_per_unitAmount5 = [None] * 10  # Storage for amounts per unit values
    variable_RevAmount6 = [None] * 10  # Storage for revenue quantities
    amounts_per_unitRevAmount7 = [None] * 10  # Storage for revenue prices

    # Process FilteredValues Section
    # First, locate the filteredValues array in the content using string search
    # This approach is used instead of JSON parsing due to the specific format requirements
    filtered_values_start = content.find('"filteredValues":[')
    if filtered_values_start != -1:
        # Move the start position to after the opening bracket
        filtered_values_start += len('"filteredValues":[')
        # Find the closing bracket of the filteredValues array
        filtered_values_end = content.find(']', filtered_values_start)
        # Extract the content between the brackets
        filtered_values_content = content[filtered_values_start:filtered_values_end]

        # Extract and Process Values
        # This loop iterates through the filtered values content, extracting each value's
        # ID and value using string manipulation techniques
        while True:
            # Find the start of the next ID field
            id_start = filtered_values_content.find('"id":"')
            if id_start == -1:  # No more IDs found, exit the loop
                break

            # Extract the ID value
            id_start += len('"id":"')  # Move past the opening quote
            id_end = filtered_values_content.find('"', id_start)  # Find the closing quote
            id_value = filtered_values_content[id_start:id_end]  # Extract the ID string

            # Find and extract the corresponding value
            value_start = filtered_values_content.find('"value":', id_end)
            if value_start == -1:  # No value field found, exit the loop
                break

            value_start += len('"value":')  # Move past the field name

            # Handle different value formats (quoted strings vs. numbers)
            if filtered_values_content[value_start] == '"':  # Value is a quoted string
                # Find the closing quote and include it in the extraction
                value_end = filtered_values_content.find('"', value_start + 1) + 1
                value_value = filtered_values_content[value_start:value_end]
            else:  # Value is a number or other non-quoted type
                # Find the end of the value (comma or closing brace)
                value_end = filtered_values_content.find(',', value_start)
                if value_end == -1:  # No comma found, look for closing brace
                    value_end = filtered_values_content.find('}', value_start)
                value_value = filtered_values_content[value_start:value_end]

            # Value Formatting
            # Handle special cases for different value types
            if id_value == "use_direct_operating_expensesAmount18":
                # Special handling for boolean values - convert quoted strings to Python booleans
                if value_value == '"True"':
                    value_value = "True"  # Convert to Python True boolean
                elif value_value == '"False"':
                    value_value = "False"  # Convert to Python False boolean
            elif "Amount4" in id_value or "Amount5" in id_value:
                # For vector values, just strip whitespace
                value_value = value_value.strip()
            else:
                # For other quoted strings, convert double quotes to single quotes
                # This is needed for Python syntax compatibility
                if value_value.startswith('"') and value_value.endswith('"'):
                    value_value = f"'{value_value[1:-1]}'"  # Replace double quotes with single quotes

            # Value Processing
            # Convert string values to appropriate numeric types when possible
            stripped_value = value_value.strip()
            if stripped_value.isdigit():
                # Convert to integer if the value is a whole number
                stripped_value = int(stripped_value)
            else:
                try:
                    # Try to convert to float if it's a decimal number
                    stripped_value = float(stripped_value)
                except ValueError:
                    # Keep as string if it can't be converted to a number
                    pass

            # Vector Assignment
            # Special handling for vector values (Amount4, Amount5, Amount6, Amount7)
            # These values are collected into arrays for later processing
            if "Amount4" in id_value:
                # Find the first empty slot in the variable_costsAmount4 array
                for i in range(len(variable_costsAmount4)):
                    if variable_costsAmount4[i] is None:
                        variable_costsAmount4[i] = stripped_value  # Assign the value
                        break  # Stop after finding the first empty slot
            elif "Amount5" in id_value:
                # Find the first empty slot in the amounts_per_unitAmount5 array
                for i in range(len(amounts_per_unitAmount5)):
                    if amounts_per_unitAmount5[i] is None:
                        amounts_per_unitAmount5[i] = stripped_value  # Assign the value
                        break  # Stop after finding the first empty slot
            elif "Amount6" in id_value:
                # Find the first empty slot in the variable_RevAmount6 array
                for i in range(len(variable_RevAmount6)):
                    if variable_RevAmount6[i] is None:
                        variable_RevAmount6[i] = stripped_value  # Assign the value
                        break  # Stop after finding the first empty slot
            elif "Amount7" in id_value:
                # Find the first empty slot in the amounts_per_unitRevAmount7 array
                for i in range(len(amounts_per_unitRevAmount7)):
                    if amounts_per_unitRevAmount7[i] is None:
                        amounts_per_unitRevAmount7[i] = stripped_value  # Assign the value
                        break  # Stop after finding the first empty slot

            # Line Generation
            # Create sanitized configuration lines for the output
            if "Amount4" in id_value or "Amount5" in id_value or "Amount6" in id_value or "Amount7" in id_value:
                # For vector values, use the stripped numeric value
                sanitized_lines.append(f'{id_value}={stripped_value}')
            else:
                # For other values, use the formatted value
                sanitized_lines.append(f'{id_value}={value_value}')

            # Move to the next value in the filtered values content
            filtered_values_content = filtered_values_content[value_end:]

    # Process FilteredValue Entries
    # This section processes filteredValue entries using regex to extract their components
    # These entries have a different format than the ones processed above
    content_lines = content.splitlines()
    for line in content_lines:
        if '"filteredValue":{' in line:
            # Use regex to extract the components of each filteredValue entry
            # These regex patterns match the specific JSON structure of filteredValue entries
            start_match = re.search(r'"start":\s*([^,]+)', line)  # Extract start year
            end_match = re.search(r'"end":\s*([^,]+)', line)      # Extract end year
            value_match = re.search(r'"value":\s*([^,]+)', line)  # Extract value
            id_match = re.search(r'"id":"([^"]+)"', line)         # Extract ID
            remarks_match = re.search(r'"remarks":"([^"]+)"', line)  # Extract remarks

            # Format the extracted components
            # Use the format_value function to properly format the value
            formatted_value = format_value(value_match.group(1)) if value_match else ''
            # Ensure start and end years are properly quoted
            formatted_start = f'"{start_match.group(1)}"' if start_match else ''
            formatted_end = f'"{end_match.group(1)}"' if end_match else ''
            # Extract ID and remarks as plain strings
            formatted_id = id_match.group(1) if id_match else ''
            formatted_remarks = remarks_match.group(1) if remarks_match else ''

            # Construct a properly formatted JSON string for the filteredValue entry
            filtered_value_line = f'{{"filteredValue":{{"id":"{formatted_id}","value":{formatted_value},"start":{formatted_start},"end":{formatted_end},"remarks":"{formatted_remarks}"}}}}'
            filtered_values_json.append(filtered_value_line.strip())

    # Vector Output
    # Add the collected vector values to the sanitized lines
    # These vectors contain values that were collected throughout the processing
    sanitized_lines.append(f"variable_costsAmount4={variable_costsAmount4}")  # Add variable costs vector
    sanitized_lines.append(f"amounts_per_unitAmount5={amounts_per_unitAmount5}")  # Add amounts per unit vector
    sanitized_lines.append(f"variable_RevAmount6={variable_RevAmount6}")  # Add revenue quantities vector
    sanitized_lines.append(f"amounts_per_unitRevAmount7={amounts_per_unitRevAmount7}")  # Add revenue prices vector

    # Return the processed results
    # - sanitized_lines is joined into a single string with newlines
    # - filtered_values_json is returned as a list of JSON strings
    return '\n'.join(sanitized_lines), filtered_values_json

def sanitize_file(version):
    """Process and sanitize configuration files for a specific version.

    This function is the main entry point for the configuration sanitization process.
    It handles the entire workflow of reading an original configuration file,
    processing its content using medieval_parse_and_sanitize, and writing the
    sanitized content to a new file.

    The function follows these steps:
    1. Construct file paths for the original and sanitized configuration files
    2. Create necessary directories if they don't exist
    3. Read the content of the original file
    4. Process the content using medieval_parse_and_sanitize
    5. Write the sanitized content and filtered values to the output file

    Args:
        version (str or int): Version number for configuration processing,
                             used to determine file paths

    Returns:
        dict: Result status of the operation with either:
            - {"message": "success message"} for successful operations
            - {"error": "error message"} for failed operations

    Raises:
        No exceptions are raised directly; all exceptions are caught and
        returned as error messages in the result dictionary
    """
    # Path Configuration
    original_file_path = UPLOAD_DIR / f'Batch({version})/ConfigurationPlotSpec({version})/U_configurations({version}).py'
    sanitized_file_path = UPLOAD_DIR / f'Batch({version})/ConfigurationPlotSpec({version})/configurations({version}).py'

    print(f"Sanitizing file for version: {version}")
    print(f"Original file path: {original_file_path}")
    print(f"Sanitized file path: {sanitized_file_path}")

    # Directory Creation
    try:
        original_file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating directories: {e}")
        return {"error": "Error creating directories"}

    # File Reading
    try:
        raw_content = original_file_path.read_text(encoding='utf-8')
        print(f"Raw content read from file: {raw_content}")
    except Exception as e:
        print(f"Error reading from original file at {original_file_path}: {e}")
        return {"error": "Error reading from original file"}

    # Content Processing
    sanitized_content, filtered_values_json = medieval_parse_and_sanitize(raw_content)
    print(f"Sanitized content: {sanitized_content}")
    print(f"Filtered values JSON: {filtered_values_json}")

    # File Writing
    try:
        with open(sanitized_file_path, 'w', encoding='utf-8') as f:
            f.write(sanitized_content)
            f.write("\n\nfiltered_values_json=[\n")
            for entry in filtered_values_json:
                f.write(f"   '{entry}',\n")
            f.write("]\n")
        print("Sanitized file written successfully")
        return {"message": "Sanitized file written successfully"}
    except Exception as e:
        print(f"Error writing to sanitized file at {sanitized_file_path}: {e}")
        return {"error": "Error writing to sanitized file"}

# Main Execution Block
if __name__ == '__main__':
    # Get the version from command line arguments or use default value 1
    # The version is used to determine which configuration files to process
    version = sys.argv[1] if len(sys.argv) > 1 else 1

    # Call the sanitize_file function with the specified version
    # This will process the configuration files for that version
    sanitize_file(version)
