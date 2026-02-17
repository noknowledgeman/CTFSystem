#!/usr/bin/env python3
"""Update existing admin user email to admin@example.com so login response validates."""
import os
import sys

backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend)
os.chdir(backend)

from ctf.database import SessionLocal, init_db
from ctf.models import User

def main():
    init_db()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin", User.role == "admin").first()
        if admin and admin.email == "admin@ctf.local":
            admin.email = "admin@example.com"
            db.commit()
            print("Updated admin email to admin@example.com")
        else:
            print("Admin already has a valid email or not found.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
