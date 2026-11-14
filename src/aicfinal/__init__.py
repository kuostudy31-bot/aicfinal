"""Semiconductor earnings-update workflow: deterministic core.

Everything in this package is plain, testable Python. Agents call it through
``scripts/eu.py``; they never compute financial figures themselves.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
