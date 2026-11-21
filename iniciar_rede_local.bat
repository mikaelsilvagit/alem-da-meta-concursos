@echo off
title QAP Concursos - Servidor de Rede Local (LAN)
color 0B

echo ======================================================================
echo           QAP CONCURSOS - CENTRO TATICO DE ESTUDOS POLICIAIS
echo                  MODO REDE LOCAL (ACESSO CELULAR E WI-FI)
echo ======================================================================
echo.
echo [1/2] Verificando ambiente Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao foi encontrado no sistema!
    pause
    exit /b
)

echo.
echo [2/2] Configuracao de Porta Operacional:
echo Pressione ENTER para usar a porta padrao (8000)
echo Ou digite a porta que deseja utilizar (ex: 8080, 5000, 3000):
set /p CHOSEN_PORT="> Porta desejada [Padrao: 8000]: "

if "%CHOSEN_PORT%"=="" (
    set PORT=8000
) else (
    set PORT=%CHOSEN_PORT%
)

echo.
echo [+] Iniciando Centro de Operacoes na porta %PORT% (host: 0.0.0.0)...
echo.

python run_lan.py %PORT%

pause
