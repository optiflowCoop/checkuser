@echo off
echo ========================================
echo Extraindo dados de Baseline Funcional
echo ========================================
echo.
echo Origem: 7 ambientes (BASE, ODN1, ODN2, N06, N08, N09, HTQ)
echo Queries: persongroupview, persongroup, persongroupteam
echo Total: 21 extrações (3 queries x 7 ambientes)
echo.
cd /d "%~dp0.."
python scripts\run_db2cli_queries.py --queries persongroupview,persongroup,persongroupteam
echo.
echo ========================================
echo Baseline extraída! Pressione qualquer tecla para continuar.
echo ========================================
pause
