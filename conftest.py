"""Pytest configuration.

Two jobs:

1. Put the project root on sys.path so tests can ``import logic_utils``.
   Without this, pytest inserts only the ``tests/`` directory and the import
   fails.
2. Keep pytest's doctest plugin away from ``test_results.txt``. That plugin
   collects files matching ``test*.txt`` by default, and our saved pytest
   output matches that pattern -- so pytest tries to parse its own previous
   output as a doctest file and aborts the whole run during collection.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

collect_ignore = ["test_results.txt", "lint_report.txt"]
