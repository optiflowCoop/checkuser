@echo off
echo ========================================
echo Extraindo apenas LOGINTRACKING
echo ========================================
cd /d "%~dp0"
python scripts\run_db2cli_queries.py --queries logintracking
echo.
echo ========================================
echo LOGINTRACKING extraído! Pressione qualquer tecla para continuar.
echo ========================================
pause
