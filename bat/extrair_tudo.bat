@echo off
echo ========================================
echo Extraindo TODAS as consultas do DB2
echo ========================================
echo.
echo Origem: 7 ambientes (BASE, ODN1, ODN2, N06, N08, N09, HTQ)
echo Queries: 14 queries (maxuser, person, email, groupuser, maxgroup, persongroup, persongroupteam, persongroupview, maxlicusage, maslicusage, maxlicuserasc, maxlicappaccess, maxlicapps, maxrelationship)
echo Total: 98 extrações (14 queries x 7 ambientes)
echo.
cd /d "%~dp0.."
python scripts\run_db2cli_queries.py
echo.
echo ========================================
echo Extração completa! Pressione qualquer tecla para continuar.
echo ========================================
pause
