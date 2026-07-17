# Spec: Login and Logout

## Overview
Wire up the authentication flow for Spendly. The `/login` route currently only renders the form (GET), and `/logout` is a placeholder that returns a string. This step adds session-based authentication: visitors can sign in with the email and password they registered with (Step 2), stay signed in across requests, and sign out. A `secret_key` is introduced to enable signed session cookies, and a `login_required` helper gates routes that need an authenticated user. The navbar is updated so it reflects the user's signed-in state (show "Sign out" instead of "Sign in" / "Get started" when logged in).

## Depends on
- **Step 1** — `database/db.py` with `users` table (id, name, email, password_hash) and `get_db()`.
- **Step 2** — `/register` must be able to create a row in `users` with a `werkzeug`-hashed password.

## Routes

- `GET /login` — render the sign-in form — **public**
- `POST /login` — verify credentials and start a session, then redirect to `/` (landing) — **public**
- `GET /logout` — clear the session and redirect to `/` — **public** (signing out should never 404 even if the user wasn't signed in)
- `GET /dashboard` — minimal placeholder shown after login (e.g. "Welcome, {name}") — **logged-in**
  - The dashboard is intentionally minimal here. A full profile/expense view comes in Step 4+. For now it exists only to give the post-login redirect a real destination and to demonstrate the `login_required` guard.

## Database changes
No database changes. The `users` table from Step 1 already stores `password_hash` with a `werkzeug` hash, which is exactly what `check_password_hash` expects.

## Templates
- **Modify:** `templates/login.html` — already exists with `method="POST" action="/login"` and an `{% if error %}{{ error }}{% endif %}` block; no changes required to its structure, but it will be wired to the POST handler.
- **Modify:** `templates/base.html` — swap the navbar links when the user is signed in. Currently shows "Sign in" and "Get started"; when `session.user_id` is set, show the user's name and a "Sign out" link pointing to `/logout`.
- **Create:** `templates/dashboard.html` — minimal signed-in landing page that greets the user by name and contains a "Sign out" link.

## Files to change
- `app.py` — implement POST `/login`, replace stub `/logout` with a real session-clearing handler, add a `dashboard` route, add `_login_required` helper, set `app.secret_key`, import `session` and `check_password_hash`.

## Files to create
- `.claude/specs/03-login-logout.md` (this spec)
- `templates/dashboard.html` — minimal authenticated landing page

## New dependencies
No new pip packages. Uses:
- `flask.session` (stdlib Flask)
- `werkzeug.security.check_password_hash` (already used in `seed_db` for `generate_password_hash`)
- `functools.wraps` (stdlib, for preserving the wrapped view's name/docstring when wrapping with `_login_required`)

## Rules for implementation
- No SQLAlchemy or any other ORM — raw `sqlite3` only.
- Parameterised SQL only (`?` placeholders). Never f-string or `%` into SQL.
- Passwords compared with `werkzeug.security.check_password_hash`. Never compare hashes with `==`.
- Email lookup is case-insensitive: `.strip().lower()` the submitted email before the `SELECT` (matches the lowercasing done in `/register`).
- `app.secret_key` must be set BEFORE any request is served so session cookies can be signed. Use a hard-coded dev key (`"dev-secret-change-me"`) and add a `# TODO: replace with env var in production` comment. Do NOT add a `.env` file or new pip packages.
- `login_required` must be a no-arg decorator that wraps a view function. It returns 302 to `/login` if `session.get("user_id")` is missing. Use `functools.wraps` so the wrapped view's `__name__` survives (Flask needs the original name for `url_for`).
- `/logout` is idempotent — clearing an empty session is fine, no error.
- After successful login, redirect to `/dashboard` (not `/`); this gives a real route to demonstrate the `login_required` guard. From `/dashboard` the user can navigate elsewhere.
- After `/logout`, redirect to `/` (the landing page).
- Never store the password in the session — only `user_id` (and optionally `user_name` for the navbar greeting).
- All templates extend `base.html`. No inline `<style>` blocks in `dashboard.html` — reuse the existing design tokens (`.auth-section`, `.auth-container`, `.auth-card`, `.btn-submit`, etc.) that `register.html` / `login.html` already use.
- Do NOT modify `database/db.py`.
- Do NOT add a `flash()` mechanism — keep error messages flowing through the `error=` template variable, same as Step 2.
- Failed login must take the same constant-ish amount of work as a successful one in principle. (Don't branch on "user not found" vs "wrong password" with two different code paths that return different errors to the user — keep it as one "Invalid email or password" message.)

## Definition of done

- [ ] `app.secret_key` is set in `app.py` and a `# TODO: replace with env var in production` comment sits next to it.
- [ ] `GET /login` renders the form with no error.
- [ ] `POST /login` with a valid email + password sets `session["user_id"]` (and `session["user_name"]`) and redirects (302) to `/dashboard`.
- [ ] `POST /login` with an unknown email shows "Invalid email or password." (no row leak, no 500).
- [ ] `POST /login` with a known email but wrong password shows the same "Invalid email or password." (no row leak, no 500).
- [ ] `POST /login` with an empty email or empty password shows "Please enter your email and password." (no 500, no DB call).
- [ ] Email comparison is case-insensitive (`Alice@x.com` matches `alice@x.com`).
- [ ] `GET /dashboard` while NOT signed in redirects to `/login`.
- [ ] `GET /dashboard` while signed in shows "Welcome, {name}." with the user's actual name.
- [ ] `GET /logout` clears the session and redirects to `/` regardless of whether the user was signed in.
- [ ] After `/logout`, visiting `/dashboard` redirects back to `/login` (proving the session is actually cleared, not just navigated away from).
- [ ] Navbar shows "Sign in" / "Get started" when logged out, and the user's name + "Sign out" when logged in.
- [ ] No new pip packages were added.
- [ ] `database/db.py` is unchanged.
- [ ] `templates/login.html` and `templates/register.html` are unchanged (their existing `{% if error %}` block and form fields still work).
- [ ] All SQL is parameterised; no f-strings or `%` formatting in queries.
- [ ] `templates/dashboard.html` extends `base.html` and uses existing CSS classes (no inline `<style>`, no new hardcoded hex values).
