#!/usr/bin/env python3
"""DEPRECATED redirect to modules/stages/planning/planning_report.py: forwards argv and the exit code."""
# DEPRECATED redirect, removed in phase 6
import runpy
import sys
from pathlib import Path

NEW = Path(__file__).resolve().parents[2] / "modules/stages/planning/planning_report.py"
sys.argv[0] = str(NEW)
runpy.run_path(str(NEW), run_name="__main__")
