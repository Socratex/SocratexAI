@echo off
setlocal
python -B "%~dp0normalize_json_files.py" %*
exit /b %ERRORLEVEL%
