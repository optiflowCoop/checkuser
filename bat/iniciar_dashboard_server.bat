@echo off
echo ========================================
echo Iniciando Servidor Local do Dashboard
echo ========================================
echo.
echo Isto habilita o icone de engrenagem no dashboard a disparar
echo os scripts desta pasta (extracao, pipeline, relatorio) com um clique.
echo.
echo NAO FECHE esta janela enquanto estiver usando o dashboard.
echo.
cd /d "%~dp0.."
python scripts\local_dashboard_server.py
pause
