@echo off
setlocal
rem ---------------------------------------------------------------------------
rem  Lead list workflow - double-click to run on the sample file, or drag your
rem  own CSV file onto this icon to process that file instead.
rem  Set LEADFLOW_UNATTENDED=1 to skip opening Excel and pausing (for scheduling).
rem ---------------------------------------------------------------------------
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

if exist ".venv\.installed" goto run

echo First run: setting things up. This takes a minute and only happens once.
set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if defined PY goto havepy
where python >nul 2>nul
if not errorlevel 1 set "PY=python"
if not defined PY goto nopython

:havepy
if not exist "%VENV_PY%" %PY% -m venv .venv
if not exist "%VENV_PY%" goto nopython
"%VENV_PY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto installfail
echo ok> ".venv\.installed"

:run
set "INPUT=%~1"
if "%INPUT%"=="" set "INPUT=data\raw\sample_leads.csv"
echo Processing: %INPUT%
"%VENV_PY%" -m leadflow run --input "%INPUT%" --config icp.yaml --out output
if errorlevel 1 goto failed

if defined LEADFLOW_UNATTENDED exit /b 0
echo Opening the results...
start "" "output\ranked_leads.xlsx"
echo.
pause
exit /b 0

:nopython
echo.
echo Python 3 is not installed. Install it from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" during setup, then run this again.
if not defined LEADFLOW_UNATTENDED pause
exit /b 1

:installfail
echo.
echo Setup could not download what it needs. Check your internet connection
echo and run this again.
if not defined LEADFLOW_UNATTENDED pause
exit /b 1

:failed
echo.
echo Something went wrong - see the message above.
if not defined LEADFLOW_UNATTENDED pause
exit /b 1
