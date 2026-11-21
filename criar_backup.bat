@echo off
title QAP Concursos v2.0 - Criar Backup Operacional
color 0A

echo ======================================================================
echo           QAP CONCURSOS v2.0 - CRIAR BACKUP OPERACIONAL
echo ======================================================================
echo.

python backup_manager.py create

echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
