@echo off
chcp 65001 >nul
setlocal
title Poultry System Launcher - المحرك الذكي لنظام الدواجن

:: شعار البرنامج
echo ======================================================
echo    Welcome to Poultry Farm Management System v3.8
echo        نظام إدارة عنابر الدجاج اللاحم المتطور
echo ======================================================
echo.

:: التحقق من وجود بايثون
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH.
    echo [!] بايثون غير مثبت على هذا الجهاز. يرجى تثبيته أولاً.
    pause
    exit /b
)

:: إعداد البيئة الوهمية (venv) لضمان عدم الحاجة لتثبيت مكتبات يدوياً
if not exist "env" (
    echo [*] Creating virtual environment... (First time setup)
    echo [*] جاري إعداد البيئة البرمجية... (لأول مرة فقط)
    python -m venv env
)

:: تنشيط البيئة
call env\Scripts\activate

:: التحقق من تثبيت المكتبات وتثبيتها إذا كانت ناقصة
echo [*] Checking libraries...
echo [*] جاري التحقق من المكتبات المطلوبة...
pip install -r requirements.txt --quiet --disable-pip-version-check

:: خيار تشغيل النظام
echo.
echo [OK] System is ready!
echo [OK] النظام جاهز للتشغيل.
echo.

:: هل يريد المستخدم تشغيل موجه الأوامر للتتبع؟
set /p choice="Do you want to show console logs? (y/n) [n]: "
if /i "%choice%"=="y" (
    echo [*] Running in Console Mode...
    python main.py
) else (
    echo [*] Running in Silent Mode...
    start /b pythonw main.py
)

echo.
echo [Done]
pause
deactivate
