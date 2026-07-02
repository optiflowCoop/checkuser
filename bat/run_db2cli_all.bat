@echo off
echo ========================================
echo Validando Conexoes com os Ambientes DB2
echo ========================================
echo.
echo Total: 7 conexoes para validar
echo.
if not exist output mkdir output

echo [1/7] Validando BASE (10.119.246.24:50005/prdmax76)...
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.119.246.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_BASE.txt 2>&1
echo   → Resultado salvo em: output\validate_BASE.txt
echo.

echo [2/7] Validando ODN1 (10.120.216.24:50005/prdmax76)...
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.120.216.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_ODN1.txt 2>&1
echo   → Resultado salvo em: output\validate_ODN1.txt
echo.

echo [3/7] Validando ODN2 (10.118.6.24:50005/prdmax76)...
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.118.6.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_ODN2.txt 2>&1
echo   → Resultado salvo em: output\validate_ODN2.txt
echo.

echo [4/7] Validando N06 (10.120.148.24:50005/prdmax76)...
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.120.148.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_N06.txt 2>&1
echo   → Resultado salvo em: output\validate_N06.txt
echo.

echo [5/7] Validando N08 (10.120.148.240:50005/prdmax76)...
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.120.148.240;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_N08.txt 2>&1
echo   → Resultado salvo em: output\validate_N08.txt
echo.

echo [6/7] Validando N09 (10.120.149.24:50005/prdmax76)...
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.120.149.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_N09.txt 2>&1
echo   → Resultado salvo em: output\validate_N09.txt
echo.

echo [7/7] Validando HTQ (10.119.58.24:50005/prdmax76)...
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.119.58.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_HTQ.txt 2>&1
echo   → Resultado salvo em: output\validate_HTQ.txt
echo.

echo ========================================
echo Validacao concluida! 7 conexoes testadas.
echo ========================================
echo.
echo Verifique os arquivos output\validate_*.txt para detalhes de cada conexao.
pause
