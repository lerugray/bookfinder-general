@echo off
echo.
echo  =============================================
echo    Bookfinder General - Starting...
echo  =============================================
echo.
echo  Opening in your browser at http://localhost:5000
echo  (Keep this window open while using Bookfinder General)
echo.
echo  Press Ctrl+C to stop.
echo.

timeout /t 2 /nobreak >nul
start http://localhost:5000

cd /d "%~dp0"
python app.py

pause
