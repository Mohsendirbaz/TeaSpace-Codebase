@echo off
echo Running Frontend Port Groups Analyzer...
python backend\Python-Active-Inactive-Marking\analyze_frontend_ports.py
echo.
echo Analysis complete. Report generated at frontend-port-groups-report.json
echo.
pause