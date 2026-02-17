#!/usr/bin/env python3
"""Seed mock challenges, hints, demo players, and submissions so the UI looks populated."""
import os
import sys

backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend)
os.chdir(backend)

from ctf.database import SessionLocal, init_db
from ctf.models import User, Challenge, Hint, Submission
from ctf.auth_utils import hash_password

# Challenge name -> plain flag (for submissions)
FLAGS = {
    "Welcome flag": "flag{welcome_to_ctf}",
    "Cookie jar": "flag{c00k13_m0n5t3r}",
    "Base64 secret": "flag{b64_1s_fun}",
    "Hidden in the image": "flag{st3g0_h1dd3n}",
    "SQL injection": "flag{sqli_4_d4ys}",
}

CHALLENGES = [
    {
        "name": "Welcome flag",
        "description": "Your first flag. Submit the flag in the format flag{something}.",
        "category": "warmup",
        "difficulty": "easy",
        "points": 50,
        "hints": [
            {"order": 1, "content": "The flag format is flag{...}.", "cost": 0},
            {"order": 2, "content": "Look at the page title or source.", "cost": 0},
        ],
    },
    {
        "name": "Cookie jar",
        "description": "This web app stores a secret in a cookie. Find it and submit the value.",
        "category": "web",
        "difficulty": "easy",
        "points": 100,
        "hints": [
            {"order": 1, "content": "Open Developer Tools (F12) and check Application > Cookies.", "cost": 0},
            {"order": 2, "content": "The cookie name contains 'secret'.", "cost": 5},
        ],
    },
    {
        "name": "Base64 secret",
        "description": "A message was encoded with Base64. Decode it to find the flag.",
        "category": "crypto",
        "difficulty": "easy",
        "points": 100,
        "hints": [
            {"order": 1, "content": "Use an online Base64 decoder or Python's base64 module.", "cost": 0},
            {"order": 2, "content": "The decoded string starts with 'flag{'.", "cost": 0},
        ],
    },
    {
        "name": "Hidden in the image",
        "description": "A flag is hidden inside this image file. Extract it.",
        "category": "forensics",
        "difficulty": "medium",
        "points": 150,
        "hints": [
            {"order": 1, "content": "Try reading the file as text or using strings/tools for metadata.", "cost": 10},
            {"order": 2, "content": "Steganography tools might help.", "cost": 15},
        ],
    },
    {
        "name": "SQL injection",
        "description": "The login form is vulnerable. Bypass it and retrieve the admin flag.",
        "category": "web",
        "difficulty": "medium",
        "points": 200,
        "hints": [
            {"order": 1, "content": "Try entering a single quote in the username field.", "cost": 10},
            {"order": 2, "content": "Classic pattern: ' OR '1'='1", "cost": 20},
        ],
    },
]

PLAYERS = [
    ("alice", "alice@example.com", "player1"),
    ("bob", "bob@example.com", "player2"),
    ("charlie", "charlie@example.com", "player3"),
]

# (player_index 0-based, challenge_name) -> will create correct submission
SOLVES = [
    (0, "Welcome flag"), (0, "Cookie jar"), (0, "Base64 secret"),
    (1, "Welcome flag"), (1, "Cookie jar"),
    (2, "Welcome flag"),
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        if db.query(Challenge).count() > 0:
            print("Challenges already exist; skipping seed. (Delete ctf.db and run init_db + seed to reseed.)")
            return

        for c in CHALLENGES:
            hints = c.pop("hints")
            plain_flag = FLAGS[c["name"]]
            ch = Challenge(
                name=c["name"],
                description=c["description"],
                category=c["category"],
                difficulty=c["difficulty"],
                points=c["points"],
                flag_hash=hash_password(plain_flag),
                grading_mode="auto",
            )
            db.add(ch)
            db.flush()
            for h in hints:
                db.add(Hint(challenge_id=ch.id, order=h["order"], content=h["content"], cost=h["cost"]))
        db.commit()

        name_to_ch = {c.name: c for c in db.query(Challenge).all()}

        for username, email, password in PLAYERS:
            if db.query(User).filter(User.username == username).first():
                continue
            db.add(User(username=username, email=email, hashed_password=hash_password(password), role="player"))
        db.commit()

        players = db.query(User).filter(User.role == "player").order_by(User.id).all()
        # Assume first 3 players are alice, bob, charlie (or match by username)
        by_username = {u.username: u for u in players}
        for player_idx, cname in SOLVES:
            username = PLAYERS[player_idx][0]
            u = by_username.get(username)
            ch = name_to_ch.get(cname)
            if not u or not ch:
                continue
            if db.query(Submission).filter(Submission.user_id == u.id, Submission.challenge_id == ch.id, Submission.correct == True).first():
                continue
            plain = FLAGS.get(cname)
            if not plain:
                continue
            db.add(Submission(
                user_id=u.id,
                challenge_id=ch.id,
                submitted_flag=plain,
                correct=True,
                status="accepted",
                assigned_points=ch.points,
            ))
        db.commit()
        print("Mock data seeded: 5 challenges with hints, 3 demo players (alice/bob/charlie, password player1/player2/player3), and sample submissions for leaderboard.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
