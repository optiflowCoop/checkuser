@echo off
echo Installing requirements in virtual environment...
CALL .venv\Scripts\activate.bat
pip install openpyxl pandas
echo Done!
pause