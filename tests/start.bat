@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python -m unittest discover tests
pause