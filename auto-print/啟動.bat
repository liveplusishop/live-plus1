@echo off
chcp 65001 >nul
title 直播加1 - 自動列印

echo ====================================
echo    直播加1 自動列印小程式
echo ====================================
echo.

:: 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未安裝 Python！
    echo 請先安裝 Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python 已安裝
echo.

:: 檢查必要模組
echo 檢查必要模組...
python -c "import tkinter; import json; import urllib.request" 2>nul
if errorlevel 1 (
    echo [錯誤] 缺少必要模組！
    echo 正在嘗試安裝...
    pip install plyer >nul 2>&1
)

:: 啟動程式
echo.
echo 啟動自動列印程式...
echo.
python "%~dp0auto_print.py"

pause
