import sqlite3
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)

# Required to sign session cookies. The dev key is fine for local use;
# in production this must come from an environment variable so it isn't
# checked into the repo.
# TODO: replace with env var in production
app.secret_key = "dev-secret-change-me"


# ------------------------------------------------------------------ #
# Database initialization                                              #
# ------------------------------------------------------------------ #

# Ensure the schema exists and the demo data is seeded before the first
# request hits a route. Both functions are idempotent, so this is safe
# on every startup.
with app.app_context():
    init_db(app)
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

def _validate_registration(name: str, email: str, password: str) -> str | None:
    """Return an error message string, or None if all fields are valid."""
    if not name:
        return "Please enter your name."
    if "@" not in email or "." not in email.split("@")[-1]:
        return "Please enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


def _login_required(view):
    """Gate a view on a signed-in session.

    Redirects to /login if there is no user_id in the session. The
    functools.wraps preserves the wrapped view's __name__ so Flask's
    url_for() can still resolve the endpoint by name.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def _redirect_if_authenticated(view):
    """Send already-signed-in users away from the auth pages.

    If a session is present, GET and POST both bounce to the landing
    page. Signed-out users fall through to the wrapped view unchanged.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
@_redirect_if_authenticated
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


@app.route("/login", methods=["GET", "POST"])
@_redirect_if_authenticated
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            return render_template("login.html", error="Please enter your email and password.")

        db = get_db()
        row = db.execute(
            "SELECT id, name, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        # Single error message for both "no such user" and "wrong password"
        # so we don't leak which accounts exist.
        if row is None or not check_password_hash(row["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = row["id"]
        session["user_name"] = row["name"]
        return redirect(url_for("landing"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    # Idempotent — clearing an empty session is fine.
    session.clear()
    return redirect(url_for("landing"))


@app.route("/dashboard")
@_login_required
def dashboard():
    return render_template("dashboard.html", user_name=session.get("user_name"))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
