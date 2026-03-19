@echo off
echo Running Python Active Files Analyzer...
python backend\Python-Active-Inactive-Marking\analyze_python_files.py
echo.
echo Analysis complete. Report generated at python-active-files-report.json
echo.
pause