@echo off
chcp 65001 >nul
title Smart Breakpoint Resumer
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

set PYTHONIOENCODING=utf-8

echo ========================================
echo   Smart Breakpoint Resumer
echo ========================================
echo.
%PYTHON% breakpoint_resumer.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred, check log for details...
    pause >nul)