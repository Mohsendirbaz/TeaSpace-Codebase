# Python Dependencies Documentation

## Overview

This project uses both JavaScript (Node.js) and Python. While JavaScript dependencies are managed through `package.json`, Python dependencies were previously undocumented. This documentation addresses that gap.

## Changes Made

1. **Identified Python Dependencies**: Analyzed the codebase to identify all Python packages used in the project.

2. **Created Documentation**: Created `python_dependencies.md` with a comprehensive list of all Python packages used, categorized by type and usage context.

3. **Added Requirements File**: Created `requirements.txt` with specific version requirements for all third-party Python packages.

4. **Updated package.json**: Added new scripts to simplify environment setup:
   - `npm run install-python-deps`: Installs all Python dependencies
   - `npm run setup`: Sets up both Node.js and Python environments in one command

## How to Use

### Setting Up the Complete Environment

To set up both Node.js and Python environments at once:

```bash
npm run setup
```

This will install all Node.js dependencies from package.json and all Python dependencies from requirements.txt.

### Installing Only Python Dependencies

If you only need to install or update the Python dependencies:

```bash
npm run install-python-deps
```

## Python Packages Used

The project uses the following third-party Python packages:

- **Flask and Extensions**: Web framework for the backend API
- **pandas and numpy**: Data processing and analysis
- **tabulate**: Formatting tabular data in logs
- **cssutils**: CSS parsing and manipulation

For a complete list including standard library packages, see `python_dependencies.md`.

## Maintenance

When adding new Python dependencies to the project:

1. Add them to `requirements.txt` with appropriate version constraints
2. Update `python_dependencies.md` with information about the new package
3. Run `npm run install-python-deps` to install the new dependencies