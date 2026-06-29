@echo off
echo ========================================
echo Extraindo dados de Baseline Funcional
echo ========================================
cd /d "%~dp0"
python scripts\run_db2cli_queries.py --queries persongroupview,persongroup,persongroupteam
echo.
echo ========================================
echo Baseline extraída! Pressione qualquer tecla para continuar.
echo ========================================
pause
