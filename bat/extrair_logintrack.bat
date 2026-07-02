@echo off
echo ========================================
echo Extraindo apenas LOGINTRACKING
echo ========================================
echo.
echo Origem: 7 ambientes (BASE, ODN1, ODN2, N06, N08, N09, HTQ)
echo Query: logintracking
echo Total: 7 extrações (1 query x 7 ambientes)
echo Progresso: 0%% - Iniciando extração de logintracking...
echo.
cd /d "%~dp0.."
python scripts\run_db2cli_queries.py --queries logintracking
echo.
echo ========================================
echo LOGINTRACKING extraído com sucesso! (7/7 extrações)
echo Progresso: 100%% - Concluído
echo ========================================
pause
