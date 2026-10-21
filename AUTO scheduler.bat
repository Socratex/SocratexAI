@echo off
setlocal EnableExtensions DisableDelayedExpansion
title AUTO scheduler
set "AUTO_SCHEDULER_ROOT=%~dp0"
if not "%~1"=="" if /i not "%~1"=="--once" (
    echo Usage: AUTO scheduler.bat [--once]
    exit /b 2
)
echo AUTO scheduler - sprawdzanie co 10 minut.
echo Zamknij to okno CMD, aby zatrzymac scheduler.
echo.
:check
call "%AUTO_SCHEDULER_ROOT%AUTO resume.bat" --human
set "AUTO_SCHEDULER_RESULT=%ERRORLEVEL%"
if /i "%~1"=="--once" exit /b %AUTO_SCHEDULER_RESULT%
echo.
echo Nastepne sprawdzenie za 10 minut.
"%SystemRoot%\System32\timeout.exe" /t 600 /nobreak >nul
if errorlevel 1 exit /b 2
goto check
