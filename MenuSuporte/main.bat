@echo off
title MENU DO SUPORTE TECNICO


:menu
cls
echo ======= MENU DO SUPORTE TECNICO =======
echo 1 - Reiniciar computador
echo 2 - Lentidao
echo 3 - Flush DNS
echo 4 - Verificar informacoes completas da rede
echo 5 - Ping Servidor
echo 6 - Fix erro 0x0000011b
echo 7 - Fix erro 0x00000bcb
echo 8 - Fix erro 0x00000709
echo 9 - Reiniciar spooler de impressao
echo ========================================
set /p opcao=Escolha uma opcao: 

if "%opcao%"=="1" goto reiniciar
if "%opcao%"=="2" goto lentidao
if "%opcao%"=="3" goto flushdns
if "%opcao%"=="4" goto ipall
if "%opcao%"=="5" goto pingserv
if "%opcao%"=="6" goto erro11b
if "%opcao%"=="7" goto erro0bcb
if "%opcao%"=="8" goto erro709
if "%opcao%"=="9" goto spooler,

echo Opcao inválida.
pause
goto menu

:reiniciar
shutdown /r /t 0
goto fim

:lentidao
cls
echo Etapa 1: Abrindo pastas temporarias...
start "" "%temp%"
start "" "%SystemRoot%\SoftwareDistribution\Download"
start "" "%LocalAppData%\Microsoft\Windows\Explorer"
start "" "C:\Windows\Prefetch"

echo.
echo Etapa 2: Executando SFC...
sfc /scannow

echo.
echo Etapa 3: Limpando arquivos temporarios...
del /f /s /q "%temp%\*.*"
del /f /s /q "%SystemRoot%\SoftwareDistribution\Download\*.*"
del /f /s /q "%LocalAppData%\Microsoft\Windows\Explorer\*.*"
del /f /s /q "C:\Windows\Prefetch\*.*"

echo.
echo Operação concluida.
pause
goto menu

:flushdns
ipconfig /flushdns
pause
goto menu

:ipall
ipconfig /all
pause
goto menu

:pingserv
set /p ipNome=Digite o nome ou IP do Servidor:
ping %ipNome%
pause
goto menu

:erro11b
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Print" /v RpcAuthnLevelPrivacyEnabled /t REG_DWORD /d 0 /f
echo Erro 0x0000011b corrigido.
pause
goto menu

:erro0bcb
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v RestrictDriverInstallationToAdministrators /t REG_DWORD /d 0 /f
echo Erro 0x00000bcb corrigido.
pause
goto menu

:erro709
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcUseNamedPipeProtocol /t REG_DWORD /d 1 /f
echo Erro 0x00000709 corrigido.
pause
goto menu

:spooler
net stop spooler
timeout /t 3 >nul
net start spooler
echo Spooler reiniciado com sucesso.
pause
goto menu

:fim


