@echo off
if not exist output mkdir output
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.119.246.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_BASE.txt 2>&1
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.120.216.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_ODN1.txt 2>&1
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.118.6.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_ODN2.txt 2>&1
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.120.148.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_N06.txt 2>&1
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.120.148.240;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_N08.txt 2>&1
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.120.149.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_N09.txt 2>&1
"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe" validate -connstring "DATABASE=prdmax76;HOSTNAME=10.119.58.24;PORT=50005;PROTOCOL=TCPIP;UID=maximo;PWD=M@x*2025#For3;" -connect > output\validate_HTQ.txt 2>&1
echo Done
