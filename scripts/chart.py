#!/usr/bin/env python3
"""Backward-compat shim -- real code lives in cli_charts/chart.py.

Works with or without `pip install cli-charts`:
  python scripts/chart.py <type> [options]
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_charts.chart import main

main()
