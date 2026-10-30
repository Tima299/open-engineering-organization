"""Unit tests for the OEO plugin tooling (scripts/oeo.py, guard.py, finops_hook.py).

Stdlib unittest only. Run from the repository root:
    python3 -m unittest discover -s tests -t .
The tests never write inside the repository: bytecode writing is disabled and every
test works on a temporary directory (see tests/_common.py).
"""
import sys

sys.dont_write_bytecode = True
