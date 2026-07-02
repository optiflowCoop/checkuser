@echo off
echo ========================================
echo Executando Pipeline Completo
echo ========================================
echo.
echo Esta pipeline executara 13 passos:
echo   1. Extracao de dados do DB2 (14 queries x 7 ambientes = 98 extracoes)
echo   2. Extracao de Logintracking
echo   3. Consolidacao de Textos Brutos
echo   4. Montagem de Base de Acessos
echo   5. Normalizacao e Tipificacao de Contas
echo   6. Deteccao de Reuso de USERID
echo   7. Deteccao de Conflitos de Login
echo   8. Classificacao de Identidades e Worklist
echo   9. Consolidacao de Licencas
echo  10. Analise de Historico de Uso (FASE 3)
echo  11. Detector de Otimizacao (FASE 3-B)
echo  12. Geracao de Uso Real
echo  13. Geracao de Dashboards e Excel de Risco
echo.
cd /d "%~dp0.."
python run_pipeline.py
echo.
echo ========================================
echo Pipeline concluida! Pressione qualquer tecla para continuar.
echo ========================================
pause
