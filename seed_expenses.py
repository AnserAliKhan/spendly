"""Seed <count> realistic Indian expenses for <user_id> across <months> months.

Reuses the same app-context + get_db() pattern as database/db.py so the DB
path is resolved the same way and FK enforcement / row_factory match the
rest of the app. Inserts in one transaction so a single bad row rolls
everything back.
"""

import random
import sys
from datetime import date, timedelta

# Force UTF-8 stdout so the ₹ symbol prints on Windows (cp1252 default).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from flask import Flask

from database.db import init_db, get_db


# (name, min ₹, max ₹, weight, [descriptions])
# Weight drives the rough distribution: Food dominates (everyday spend),
# Transport/Shopping/Other/Other are common, Bills routine, Entertainment
# and Health are occasional.
CATEGORIES = [
    ("Food",          50,  800, 30, [
        "Chai and samosa", "Lunch thali", "Dinner at restaurant",
        "Street food", "Swiggy order", "Zomato order", "Breakfast idli",
        "Coffee and biscuits", "Zepto groceries", "Blinkit milk run",
    ]),
    ("Transport",     20,  500, 18, [
        "Auto rickshaw", "Ola ride", "Uber to airport", "Metro card top-up",
        "Petrol refill", "Rapido bike", "Bus pass", "Cab to office",
    ]),
    ("Bills",        200, 3000, 12, [
        "Electricity bill", "Broadband bill", "Mobile recharge",
        "Gas cylinder", "Water bill", "DTH recharge", "Credit card bill",
    ]),
    ("Health",       100, 2000,  6, [
        "Pharmacy", "Doctor consultation", "Lab test", "Vitamins",
        "Dental checkup", "Health supplements",
    ]),
    ("Entertainment",100, 1500,  7, [
        "Movie ticket", "BookMyShow streaming", "Spotify premium",
        "Netflix subscription", "Stand-up show", "Concert ticket",
    ]),
    ("Shopping",     200, 5000, 15, [
        "Amazon order", "Flipkart order", "Myntra clothing",
        "Footwear", "Electronics accessory", "Meesho order", "Grocery haul",
    ]),
    ("Other",         50, 1000, 12, [
        "Household supplies", "Petty cash", "Gift for friend",
        "Courier charges", "Salon visit", "Barber",
    ]),
]


# Today's date from /currentDate — keep the script reproducible.
TODAY = date(2026, 7, 17)


def pick_random_date(months: int) -> date:
    """A random date in the last <months> months, ending TODAY."""
    # Earliest = the 1st of the month that is (months-1) months before TODAY's month.
    year = TODAY.year
    month = TODAY.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    earliest = date(year, month, 1)

    span_days = (TODAY - earliest).days
    return earliest + timedelta(days=random.randint(0, span_days))


def generate_expense(user_id: int, months: int) -> tuple:
    """Return (user_id, amount, category, date, description) for one row."""
    name, lo, hi, _weight, descriptions = random.choices(
        CATEGORIES, weights=[c[3] for c in CATEGORIES], k=1
    )[0]
    amount = round(random.uniform(lo, hi), 2)
    description = random.choice(descriptions)
    return (user_id, amount, name, pick_random_date(months).isoformat(), description)


def main(user_id: int, count: int, months: int) -> int:
    app = Flask(__name__)
    with app.app_context():
        # Mirror app.py's startup so the DB file + tables exist.
        init_db(app)
        db = get_db()

        # Step 2: verify the user exists before generating anything.
        if db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone() is None:
            print(f"No user found with id {user_id}.")
            return 1

        rows = [generate_expense(user_id, months) for _ in range(count)]

        # Step 3: insert in a single transaction. If any insert raises,
        # the `with` block rolls back; nothing partial is persisted.
        try:
            with db:  # implicit BEGIN ... COMMIT / ROLLBACK
                db.executemany(
                    """
                    INSERT INTO expenses (user_id, amount, category, date, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    rows,
                )
        except Exception as exc:
            print(f"Insert failed, rolled back: {exc}")
            return 1

        # Step 4: report.
        # Re-query for the actual range and sample so we print what landed
        # in the DB, not just what we tried to send.
        agg = db.execute(
            """
            SELECT COUNT(*)        AS n,
                   MIN(date)       AS first_date,
                   MAX(date)       AS last_date
            FROM expenses
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        sample = db.execute(
            """
            SELECT id, amount, category, date, description
            FROM expenses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (user_id,),
        ).fetchall()

        print(f"Inserted {agg['n']} expenses for user_id={user_id}.")
        print(f"Date range: {agg['first_date']} to {agg['last_date']}")
        print("Sample of 5 most-recent inserted records:")
        for r in sample:
            print(f"  id={r['id']:>3}  {r['date']}  ₹{r['amount']:>7.2f}  "
                  f"{r['category']:<14}  {r['description']}")
        return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)
    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
    except ValueError:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)
    sys.exit(main(user_id, count, months))
