@echo off
chcp 65001 >nul
echo تشغيل نظام إدارة العنابر...
python main.py
if errorlevel 1 (
    echo.
    echo خطأ: تأكد من تثبيت Python
    echo قم بتحميله من: https://www.python.org/downloads/
    pause
)
