# Active Files Tracker

This module helps you identify which files in your project are actively used (imported directly or indirectly from your entry point) and which files are inactive (not imported from the entry point).

## How to Produce a New active-files-report.json

The `active-files-report.json` file contains information about which files in your project are actively used and which are not. It also includes dependency information such as which files import each file and the dependency layers.

### Steps to Generate the Report

1. Make sure you have the module installed in your project:
   - The `eslint-plugin-active-files` directory should be in your project root
   - The `Active-Inactive-Marking` directory should be in your project root

2. Run the analysis script:
   ```
   node Active-Inactive-Marking\run-active-files-analysis.js
   ```

3. The script will:
   - Analyze your project starting from the entry point (default: src/index.js)
   - Trace all imports recursively
   - Generate a report file at `active-files-report.json` in your project root

### Command-Line Options

The `run-active-files-analysis.js` script supports several command-line options:

- `--skip-restore`: Skip restoring original filenames before analysis
- `--skip-config`: Skip updating ESLint configuration
- `--skip-graph`: Skip generating dependency graph visualization
- `--skip-mark`: Skip marking files with [A]_ or [I]_ prefixes
- `--force-restore`: Use force mode when restoring filenames
- `--verbose`: Display more detailed output
- `--help`, `-h`: Display help message

Example:
```
node Active-Inactive-Marking\run-active-files-analysis.js --skip-mark --verbose
```

## How to Use the Module

### Overall Workflow

1. **Generate the Report**: Run the analysis to identify active and inactive files
2. **Review the Report**: Examine the `active-files-report.json` file
3. **Mark Files** (Optional): Rename files with [A]_ or [I]_ prefixes
4. **Restore Filenames** (Optional): Remove the prefixes when needed

### Key Components

1. **run-active-files-analysis.js**: The main script that initiates the analysis
   - Sets up the environment for analysis
   - Runs ESLint with the active-files-tracker rule
   - Generates the report file

2. **active-files-tracker.js**: The ESLint rule that performs the analysis
   - Traces dependencies starting from the entry point
   - Builds the dependency graph
   - Identifies active and inactive files
   - Generates the report data

3. **mark-active-files.js**: Script to rename files with prefixes
   - Adds [A]_ prefix to active files
   - Adds [I]_ prefix to inactive files
   - Updates import statements in all files

4. **restore-filenames.js**: Script to restore original filenames
   - Removes [A]_ and [I]_ prefixes
   - Updates import statements

### Understanding the Report

The `active-files-report.json` file contains:

- `activeFiles`: Array of files that are imported (directly or indirectly) from the entry point
- `inactiveFiles`: Array of files that are not imported from the entry point
- `standaloneFiles`: Array of files that don't import any other files
- `dependencyLayers`: Object mapping layer numbers to arrays of files in that layer
  - Layer 0 contains the entry point
  - Layer 1 contains files directly imported by the entry point
  - Layer 2 contains files imported by layer 1 files, and so on
- `importedBy`: Object mapping file paths to arrays of files that import them

### Example Use Cases

#### Identifying Unused Files

```
node Active-Inactive-Marking\run-active-files-analysis.js
```

Then check the `inactiveFiles` section in the generated report to see which files are not being used.

#### Visualizing Project Structure

```
node Active-Inactive-Marking\run-active-files-analysis.js
```

Then examine the `dependencyLayers` section in the report to understand the structure of your project.

#### Marking Files for Better Visibility

```
node Active-Inactive-Marking\run-active-files-analysis.js
node Active-Inactive-Marking\mark-active-files.js
```

This will rename your files with [A]_ or [I]_ prefixes to make it easy to identify active and inactive files in your file explorer.

#### Restoring Original Filenames

```
node Active-Inactive-Marking\restore-filenames.js
```

This will remove the [A]_ and [I]_ prefixes from your files.

## Troubleshooting

- If the analysis doesn't find any active files, check that your entry point is correctly specified
- If import statements aren't being detected, check the supported import formats in the code
- If you encounter errors during the analysis, try running with the `--verbose` flag for more detailed output