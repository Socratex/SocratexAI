@echo off
setlocal EnableExtensions DisableDelayedExpansion
title AUTO scheduler
set "AUTO_SCHEDULER_ROOT=%~dp0"
set "AUTO_PYTHON=%AUTO_SCHEDULER_ROOT%Tools\Python312\python.exe"
if not exist "%AUTO_PYTHON%" set "AUTO_PYTHON=python"
set "AUTO_SCRIPT=%AUTO_SCHEDULER_ROOT%Tools\automation\resume_auto.py"
if not exist "%AUTO_SCRIPT%" set "AUTO_SCRIPT=%AUTO_SCHEDULER_ROOT%SocratexAI\tools\automation\resume_auto.py"
if not "%~1"=="" if /i not "%~1"=="--once" (
    echo Usage: AUTO scheduler.bat [--once]
    exit /b 2
)
echo AUTO scheduler - sprawdzanie co 10 minut.
echo Zamknij to okno CMD, aby zatrzymac scheduler.
echo.
:check
"%AUTO_PYTHON%" -B "%AUTO_SCRIPT%" --human
set "AUTO_SCHEDULER_RESULT=%ERRORLEVEL%"
if /i "%~1"=="--once" exit /b %AUTO_SCHEDULER_RESULT%
echo.
echo Nastepne sprawdzenie za 10 minut.
"%SystemRoot%\System32\timeout.exe" /t 600 /nobreak >nul
if errorlevel 1 exit /b 2
goto check
