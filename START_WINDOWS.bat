@echo off
cd /d "%~dp0"
title AlgoVista - Python Algorithm Studio
python server.py
if errorlevel 1 (
  echo.
  echo Python 3.10 or later is required. Ensure Python is on PATH.
  pause
)
