"""One-off script to insert a random Indian user into the Spendly DB.

Uses the same get_db() pattern as database/db.py — i.e. runs inside a
Flask app context so flask.g / current_app are populated. Picks a
realistic Indian first + last name across regions, builds an email
with a 2–3 digit numeric suffix, and retries until the email is unique.
"""

import random
import sys

from flask import Flask

from database.db import init_db, get_db


# Realistic Indian first + last names spanning regions
# (North, South, East, West). Picked by random.choice, so any pair is plausible.
FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali",
    "Arjun", "Kavya", "Rohit", "Meera", "Karthik", "Divya",
    "Aditya", "Pooja", "Sandeep", "Neha", "Ravi", "Ananya",
    "Suresh", "Lakshmi", "Manish", "Rina", "Deepak", "Aishwarya",
    "Nikhil", "Shreya", "Vivek", "Tanya", "Arun", "Ishita",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Iyer", "Nair",
    "Gupta", "Khan", "Singh", "Das", "Menon", "Pillai",
    "Joshi", "Kapoor", "Bose", "Mukherjee", "Rao", "Chatterjee",
    "Trivedi", "Banerjee", "Kulkarni", "Desai", "Bhat", "Saxena",
    "Mehta", "Agarwal", "Chauhan", "Srinivasan", "Bajaj", "Tiwari",
]


def generate_user() -> tuple[str, str, str, str]:
    """Return (first, last, email, password_hash)."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    # 2 or 3 digit suffix — match the rahul.sharma91 style.
    suffix_digits = random.choice([2, 3])
    suffix = str(random.randint(10 ** (suffix_digits - 1), 10 ** suffix_digits - 1))
    email = f"{first.lower()}.{last.lower()}{suffix}@gmail.com"
    password_hash = generate_password_hash("password123")
    return first, last, email, password_hash


def main() -> int:
    app = Flask(__name__)
    with app.app_context():
        # Mirror app.py's startup sequence so the DB file + tables exist.
        init_db(app)
        db = get_db()

        # Loop until we land an email that isn't already taken.
        while True:
            first, last, email, password_hash = generate_user()
            existing = db.execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing is None:
                break
            print(f"  (collision on {email}, regenerating)")

        cur = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (f"{first} {last}", email, password_hash),
        )
        db.commit()
        user_id = cur.lastrowid

        # Read back the row so we print exactly what was persisted,
        # including the created_at default the DB fills in.
        row = db.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        print("Seeded user:")
        print(f"  id:    {row['id']}")
        print(f"  name:  {row['name']}")
        print(f"  email: {row['email']}")
        return 0


if __name__ == "__main__":
    # generate_password_hash is imported lazily so the import error message
    # is friendlier than a NameError if werkzeug isn't installed.
    from werkzeug.security import generate_password_hash
    sys.exit(main())
