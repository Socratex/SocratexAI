@echo off
rem Set SOCRATEX_PYTHON (see local/profile.md) to a stable python; falls back to `python` on PATH.
if defined SOCRATEX_PYTHON (
  "%SOCRATEX_PYTHON%" "%~dp0sox" %*
) else (
  python "%~dp0sox" %*
)
