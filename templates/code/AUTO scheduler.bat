@echo off
setlocal EnableExtensions DisableDelayedExpansion
title AUTO scheduler
set "AUTO_SCHEDULER_ROOT=%~dp0"
set "AUTO_PYTHON=%AUTO_SCHEDULER_ROOT%Tools\Python312\python.exe"
if not exist "%AUTO_PYTHON%" set "AUTO_PYTHON=python"
set "AUTO_SCRIPT=%AUTO_SCHEDULER_ROOT%Tools\automation\resume_auto.py"
if not exist "%AUTO_SCRIPT%" set "AUTO_SCRIPT=%AUTO_SCHEDULER_ROOT%SocratexAI\tools\automation\resume_auto.py"
set "AUTO_HOST=%AUTO_SCHEDULER_ROOT%Tools\automation\console_scheduler.py"
if not exist "%AUTO_HOST%" set "AUTO_HOST=%AUTO_SCHEDULER_ROOT%SocratexAI\tools\automation\console_scheduler.py"
if not "%~1"=="" if /i not "%~1"=="--once" if /i not "%~1"=="--loop" (
    echo Usage: AUTO scheduler.bat [--once]
    exit /b 2
)
if /i "%~1"=="--once" goto check
if /i "%~1"=="--loop" goto loop
"%AUTO_PYTHON%" -B "%AUTO_HOST%" --launcher "%~f0"
exit /b %ERRORLEVEL%
:loop
echo AUTO watchdog - kontrola co 5 minut, przy limicie co 10 minut.
echo Zamknij to okno CMD, aby zatrzymac scheduler.
echo.
:check
"%AUTO_PYTHON%" -B "%AUTO_SCRIPT%" --watchdog
set "AUTO_SCHEDULER_RESULT=%ERRORLEVEL%"
if /i "%~1"=="--once" exit /b %AUTO_SCHEDULER_RESULT%
set "AUTO_WAIT=300"
if "%AUTO_SCHEDULER_RESULT%"=="10" set "AUTO_WAIT=600"
"%SystemRoot%\System32\timeout.exe" /t %AUTO_WAIT% /nobreak >nul
if errorlevel 1 exit /b 2
goto check
