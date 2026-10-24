@echo off
setlocal
title Veilshard - Fractured Oath

echo ========================================================
echo               VEILSHARD - FRACTURED OATH
echo ========================================================
echo.

:: 1. Find Python executable (prefer local .venv if present)
set PY_CMD=
if exist ".venv\Scripts\python.exe" (
    set PY_CMD=".venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set PY_CMD=python
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 (
            set PY_CMD=py
        )
    )
)

if "%PY_CMD%"=="" (
    echo [ERROR] Python was not detected on your system.
    echo Please install Python 3.11 or newer from: https://www.python.org/
    echo Be sure to check the box: "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check if pygame is installed; install if missing
%PY_CMD% -c "import pygame" >nul 2>nul
if %errorlevel% neq 0 (
    echo Required library "pygame-ce" not found. Installing automatically...
    echo.
    %PY_CMD% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies automatically.
        echo Please run: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Installation complete!
)

:: 3. Launch game
echo Launching Veilshard...
echo.
%PY_CMD% main.py

if %errorlevel% neq 0 (
    echo.
    echo Game closed with code %errorlevel%.
    pause
)
