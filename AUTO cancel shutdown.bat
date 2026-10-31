@echo off
setlocal EnableExtensions DisableDelayedExpansion
if /I "%~1"=="-Help" goto help
if /I "%~1"=="--help" goto help
if /I "%~1"=="/?" goto help
if not "%~1"=="" exit /b 2
set "AUTO_CANCEL_ROOT=%~dp0"
set "AUTO_CANCEL_PYTHON=%AUTO_CANCEL_ROOT%Tools\Python312\python.exe"
if not exist "%AUTO_CANCEL_PYTHON%" set "AUTO_CANCEL_PYTHON=python"
set "AUTO_CANCEL_SCRIPT=%AUTO_CANCEL_ROOT%Tools\automation\auto.py"
if not exist "%AUTO_CANCEL_SCRIPT%" set "AUTO_CANCEL_SCRIPT=%AUTO_CANCEL_ROOT%SocratexAI\tools\automation\auto.py"
"%AUTO_CANCEL_PYTHON%" -B "%AUTO_CANCEL_SCRIPT%" cancel-shutdown
set "AUTO_CANCEL_CODE=%ERRORLEVEL%"
if not "%AUTO_CANCEL_CODE%"=="0" pause
exit /b %AUTO_CANCEL_CODE%

:help
echo Cancels pending AUTO computer shutdowns locally, without using an AI account.
echo Does not stop AUTO work. Run without arguments to cancel.
exit /b 0
