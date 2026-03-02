@echo off
color 0A
title CyberCTF Project

echo ===============================
echo      CyberCTF Launcher
echo ===============================
echo.

echo [1/2] Starting Server...
start "CyberCTF Server" cmd /k "python -m server.server"

timeout /t 2 >nul

echo [2/2] Starting Client...
start "CyberCTF Client" cmd /k "python -m client.client"

echo.
echo System is running.
echo Close the server window to stop everything.
pause