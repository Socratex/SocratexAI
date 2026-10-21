@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "AUTO_ROOT=%~dp0"
set "AUTO_PYTHON=%AUTO_ROOT%Tools\Python312\python.exe"
if not exist "%AUTO_PYTHON%" set "AUTO_PYTHON=python"
set "AUTO_SCRIPT=%AUTO_ROOT%Tools\automation\resume_auto.py"
if not exist "%AUTO_SCRIPT%" set "AUTO_SCRIPT=%AUTO_ROOT%SocratexAI\tools\automation\resume_auto.py"
"%AUTO_PYTHON%" -B "%AUTO_SCRIPT%" %*
exit /b %ERRORLEVEL%
