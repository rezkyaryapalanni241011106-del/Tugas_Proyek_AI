"""
conftest.py — Konfigurasi pytest untuk AI Code Review Tutor.

Menambahkan project root ke sys.path agar import dari core/ berfungsi
tanpa perlu instalasi package.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
