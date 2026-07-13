@echo off
echo ========================================
echo Extraindo dados de Seguranca (Grupos x Permissoes)
echo ========================================
echo.
echo Origem: 7 ambientes (BASE, ODN1, ODN2, N06, N08, N09, HTQ)
echo Queries: applicationauth (PLUSGPR, PLUSGPO, CREATEDR) + pr_sod_evidence (casos reais documentados) + siteauth (site x grupo)
echo Total: 21 extracoes (3 queries x 7 ambientes)
echo Aviso: pr_sod_evidence pode levar ~1min por ambiente (cruza milhoes de registros de workflow)
echo Progresso: 0%% - Iniciando extracao de seguranca...
echo.
cd /d "%~dp0.."
python scripts\run_db2cli_queries.py --queries applicationauth,pr_sod_evidence,siteauth
echo.
echo ========================================
echo Seguranca extraida com sucesso! (21/21 extracoes)
echo Progresso: 100%% - Concluido
echo ========================================
pause
