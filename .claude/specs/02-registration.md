
1. Overview
Implement the user registration flow for Spendly.
Currently `/register` only renders the form (GET). The form already POSTs to `/register` with `name`, `email`, `password`, but no handler reads the form yet. This step wires the POST handler so visitors can create an account.

The flow stays self-contained: on success, redirect to `/login` so the user signs in. Auto-login + session management belongs to a later step (Step 3) — out of scope here.

2. Depends on
Step 1 — database/db.py must be implemented, with the `users` table and `get_db()` available.
3. Routes
A. `/register` — change from GET-only to GET + POST
GET behavior (unchanged): render `templates/register.html`
POST behavior (new):
Read `name`, `email`, `password` from `request.form`
Validate (see §10)
On valid input: insert user, redirect to `/login`
On invalid input or DB error: re-render `register.html` with an `error` message
No new routes are introduced.
4. Changes to app.py
A. Imports
Add at the top of the file (alongside the existing `from flask import ...`):
import sqlite3
from flask import redirect, request, url_for
from werkzeug.security import generate_password_hash
from database.db import get_db
B. `/register` route
Replace the existing GET-only handler with:
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        error = _validate_registration(name, email, password)
        if error:
            return render_template("register.html", error=error)

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with that email already exists.")

        return redirect(url_for("login"))

    return render_template("register.html")
C. New module-level helper
Define a small private helper next to the route (not in database/db.py — it deals with HTTP form input, not data access):
def _validate_registration(name: str, email: str, password: str) -> str | None:
    """Return an error message string, or None if all fields are valid."""
    if not name:
        return "Please enter your name."
    if "@" not in email or "." not in email.split("@")[-1]:
        return "Please enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None
5. Changes to templates
None.
`templates/register.html` already has:
`method="POST" action="/register"`
`name` attributes matching the fields read above (`name`, `email`, `password`)
`{% if error %}{{ error }}{% endif %}` block for the message
The existing `auth-error` class styles the red error banner — reuse it.
6. Changes to database/db.py
None.
The existing `users` table (id, name, email, password_hash, created_at) already supports this step. `get_db()` already returns a connection with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`, so the `INSERT` in §4 just works.
7. Files to Change
app.py — replace the `/register` route, add imports, add `_validate_registration`
8. Files to Create
None
9. Dependencies
No new pip packages
Use:
sqlite3 (standard library) — already used in db.py
werkzeug.security.generate_password_hash — already used in seed_db
flask.redirect, flask.request, flask.url_for — stdlib Flask
10. Validation Rules
Applied server-side on every POST. Client-side `required` and `type="email"` are UX hints only.
Field
Rule
Error message
name
Non-empty after `.strip()`
"Please enter your name."
email
Non-empty, contains `@`, has a `.` in the domain part (lightweight check; full RFC validation is overkill for this step)
"Please enter a valid email address."
password
Length ≥ 8 characters
"Password must be at least 8 characters."
Email is lowercased before insert so login (Step 3) is case-insensitive without extra logic.
Password is never logged, never echoed back, never stored in plaintext. Only the bcrypt-style hash from `generate_password_hash` lands in `users.password_hash`.
11. Rules for Implementation
Use parameterized SQL (?, never f-strings) — consistent with db.py
Do not introduce a session, cookie, or `app.secret_key` in this step
Do not auto-login the user — redirect to `/login` instead
Do not call `flash()` — pass `error=` to the template (the existing template already renders it; avoids needing `secret_key`)
Do not modify `database/db.py` — the data layer is done
On duplicate email, catch `sqlite3.IntegrityError` (the `users.email` UNIQUE constraint) and re-render the form
12. Expected Behavior
GET `/register`:
Renders the empty form, no error message.
POST `/register` with valid, unique credentials:
User row inserted, `password_hash` column holds the hashed password.
Browser is redirected (302) to `/login`. The URL bar shows `/login`.
POST `/register` with invalid input:
The same form is re-rendered. Above the form, the `auth-error` banner shows the matching message from §10. The `name` field is NOT repopulated (the template's `value=` attributes would need to be added if you want that — out of scope).
POST `/register` with an email that already exists in `users`:
The same form is re-rendered with the duplicate-email error.
The password the user typed is never echoed anywhere on the page.
13. Error Handling Expectations
Missing/empty form field → user-friendly message, no 500
Malformed email → user-friendly message, no 500
Password too short → user-friendly message, no 500
Duplicate email → caught `IntegrityError`, user-friendly message, no 500
Unexpected DB error (disk full, file locked, etc.) → bubbles up as 500 — acceptable for this step
14. Definition of Done

`/register` accepts GET and POST
Empty name, bad email, short password each show their own error
A successful POST inserts a row in `users` with a hashed password
A second POST with the same email shows the duplicate-email error and does not insert
After success, the browser lands on `/login`
No `app.secret_key` is added (no flash, no session)
All SQL is parameterized
The `name` and `email` and `password` fields in the form have not been renamed or restructured
`database/db.py` is unchanged
