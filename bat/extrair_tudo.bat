@echo off
echo ========================================
echo Extraindo TODAS as consultas do DB2
echo ========================================
cd /d "%~dp0"
python scripts\run_db2cli_queries.py
echo.
echo ========================================
echo Extração completa! Pressione qualquer tecla para continuar.
echo ========================================
pause
