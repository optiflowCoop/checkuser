@echo off
echo =======================================================
echo Maximo Identity Sanity - Start Pipeline
echo =======================================================

CALL .venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    echo ATENCAO: Virtual Environment .venv nao encontrado ou nao pode ser ativado!
    echo Tentando rodar com o Python do sistema...
)

python run_pipeline.py

echo.
pause