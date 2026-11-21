@echo off
title QAP Concursos - Liberar Firewall do Windows
color 0A

echo ======================================================================
echo           QAP CONCURSOS - LIBERAR PORTA NO FIREWALL DO WINDOWS
echo ======================================================================
echo.
echo Este script adiciona uma regra no Firewall do Windows permitindo
echo conexoes de entrada para o servidor do QAP Concursos na sua rede local.
echo.

set /p PORT="Digite a porta a liberar [Padrao: 8000]: "
if "%PORT%"=="" set PORT=8000

echo.
echo [+] Liberando porta TCP %PORT% no Firewall...
netsh advfirewall firewall add rule name="QAP Concursos (Porta %PORT%)" dir=in action=allow protocol=TCP localport=%PORT%

if %errorlevel% equ 0 (
    echo.
    echo [SUCESSO] Porta %PORT% liberada com sucesso no Firewall!
    echo Dispositivos na sua rede Wi-Fi agora podem acessar livremente.
) else (
    echo.
    echo [AVISO] Se ocorreu erro de permissao, clique com o botao direito
    echo neste arquivo e selecione "Executar como Administrador".
)

echo.
pause
