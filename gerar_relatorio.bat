@echo off
echo ========================================
echo Gerando Relatório HTML
echo ========================================
cd /d "%~dp0"
python scripts\generate_risk_report.py
echo.
echo ========================================
echo Relatório gerado! Abrindo...
echo ========================================
start output\reports\identity_risk_report.html
pause
