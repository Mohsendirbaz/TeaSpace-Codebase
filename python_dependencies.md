# Python Dependencies Used in the Project

This document lists Python packages that are used in the codebase but are not explicitly included in the package.json file.

## Standard Library Packages
These are part of the Python standard library and don't need to be installed separately:

- os
- sys
- json
- time
- logging
- subprocess
- pathlib (Path)
- re
- threading
- queue (Queue)
- datetime
- uuid
- shutil
- importlib.util
- copy
- functools

## Third-Party Packages
These packages need to be installed via pip:

1. **Flask and Extensions**
   - flask
   - flask_cors

2. **Data Processing**
   - pandas
   - numpy
   - tabulate

3. **CSS Processing**
   - cssutils

## Usage Context

- **Flask and Extensions**: Used in backend API endpoints and controllers for creating web services
- **pandas**: Used extensively in data processing and configuration management
- **numpy**: Used in utility functions for numerical operations
- **tabulate**: Used for formatting tabular data in logs
- **cssutils**: Used in theme_routes.py for CSS parsing

## Recommendation

These Python dependencies should be documented in a requirements.txt file or similar to ensure consistent environment setup. Consider adding a script in package.json that installs these Python dependencies when setting up the project.

Example requirements.txt content:
```
flask
flask-cors
pandas
numpy
tabulate
cssutils
```

You could then add a script to package.json:
```json
{
  "scripts": {
    "install-python-deps": "pip install -r requirements.txt"
  }
}
```
