"""Test select script that always fails, like a missing tool."""

import sys

sys.stderr.write("serena not installed\n")
sys.exit(3)
