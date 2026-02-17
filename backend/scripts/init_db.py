#!/usr/bin/env python3
"""Initialize CTF database (tables + default admin). Run from backend dir or set PYTHONPATH."""
import sys
import os

# Allow running from project root or backend
backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend not in sys.path:
    sys.path.insert(0, backend)
os.chdir(backend)

from ctf.database import init_db

if __name__ == "__main__":
    init_db()
    print("Database initialized: tables created, default admin ensured (username: admin).")
