@echo off
title QAP Concursos v2.0 - Centro Tatico de Estudos Policiais
color 0B

echo ======================================================================
echo         QAP CONCURSOS v2.0 - CENTRO TATICO DE ESTUDOS POLICIAIS
echo                      MISSAO DADA E MISSAO CUMPRIDA!
echo ======================================================================
echo.
echo [1/2] Verificando ambiente Python...
python --version
if %errorlevel% neq 0 (
    echo [ERRO] Python nao foi encontrado no sistema!
    pause
    exit /b
)

echo.
echo [2/2] Iniciando Centro de Operacoes Tatico...
echo.

python run_lan.py 8000

pause
