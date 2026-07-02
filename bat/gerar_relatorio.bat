@echo off
echo ========================================
echo Gerando Relatório HTML e Excel
echo ========================================
echo.
echo Este processo ira:
echo   - Gerar dashboard HTML interativo
echo   - Gerar workbook Excel com múltiplas abas
echo   - Abrir o relatório automaticamente
echo.
cd /d "%~dp0.."
python scripts\generate_risk_report.py
echo.
echo ========================================
echo Relatório gerado! Abrindo...
echo ========================================
start output\reports\maximo_identity_sanity_report.html
pause
