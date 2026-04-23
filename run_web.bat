@echo off
chcp 65001 >nul
setlocal
title Poultry Web Launcher

python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [!] Python is not installed or not available in PATH.
  pause
  exit /b 1
)

if not exist "env\Scripts\python.exe" (
  echo [*] Creating virtual environment...
  python -m venv env
)

if not exist "env\Scripts\python.exe" (
  echo [!] Failed to create virtual environment.
  pause
  exit /b 1
)

env\Scripts\python.exe -V >nul 2>&1
if %errorlevel% neq 0 (
  echo [!] Virtual environment Python is not runnable.
  pause
  exit /b 1
)

call env\Scripts\activate
env\Scripts\python.exe -m pip install -r requirements.txt --disable-pip-version-check

echo [*] Starting web server at http://127.0.0.1:5000
env\Scripts\python.exe web\main_web.py
