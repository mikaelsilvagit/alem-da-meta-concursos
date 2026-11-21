@echo off
title QAP Concursos v2.0 - Restaurar Backup Tatico
color 0E

echo ======================================================================
echo           QAP CONCURSOS v2.0 - RESTAURAR BACKUP TATICO
echo ======================================================================
echo.

python backup_manager.py restore

echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
