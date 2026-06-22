@echo off
echo ========================================
echo Executando Pipeline Completo
echo ========================================
cd /d "%~dp0"
python run_pipeline.py
echo.
echo ========================================
echo Pipeline concluído! Pressione qualquer tecla para continuar.
echo ========================================
pause
