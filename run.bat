@echo off
chcp 65001 > nul
title Rafa Music Pro - Iniciando Bot...
color 0b

echo ========================================================
echo          RAFA MUSIC PRO - BOT DE DISCORD
echo            Desarrollado y Creado por Rafa
echo ========================================================
echo.

:: Verificar si python está instalado
python --version > nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python no está instalado o no se encuentra en el PATH.
    echo Descarga e instala Python desde: https://www.python.org/
    echo Recuerda marcar la casilla "Add Python to PATH" durante la instalación.
    pause
    exit /b
)

:: Verificar si existe .env
if not exist .env (
    echo [AVISO] Creando archivo .env desde plantilla...
    copy .env.example .env > nul
)

echo [1/2] Verificando dependencias...
python -m pip install -q -r requirements.txt

echo.
echo [2/2] Iniciando Rafa Music Pro...
echo ========================================================
python bot.py

if %errorlevel% neq 0 (
    echo.
    echo El bot se ha detenido con un error. Revisa la consola arriba.
    pause
)
