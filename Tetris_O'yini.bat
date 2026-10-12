@echo off
chcp 65001 >nul
title Tetris O'yini
echo Tetris o'yini ishga tushirilmoqda...
cd /d "%~dp0Tetris"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo O'yinni ishga tushirishda xatolik yuz berdi!
    pause
)
