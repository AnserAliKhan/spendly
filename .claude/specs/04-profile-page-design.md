# Spec: Profile Page Design

## Overview
Replace the `/profile` placeholder string with a real, read-only profile page that shows the signed-in user their account information and a small at-a-glance spending summary derived from their existing `expenses` rows. This is the first step where a logged-in user actually sees their data, so it needs to be presentable: clear hierarchy, sensible grouping, and a layout that the future "edit profile" and "list expenses" steps can build on without being torn down. The page is **read-only** here — editing the name, email, or password is intentionally out of scope and belongs in a later step. The stats block is intentionally small: just total spent, transaction count, and top category. Full filtering / charts / trends belong with the expense listing work in Steps 5–6.

## Depends on
- **Step 1** — `database/db.py` with the `users` (id, name, email, password_hash, created_at) and `expenses` (id, user_id, amount, category, date, description, created_at) tables.
- **Step 2** — `/register` so a user has a row in `users`.
- **Step 3** — `/login` + `_login_required` so the page can be gated and the current user identified by `session["user_id"]`.

## Routes

- `GET /profile` — render the signed-in user's profile page — **logged-in**

No new routes. The existing `/profile` placeholder is replaced in place. No POST handler — this step is read-only.

## Database changes
No database changes. The `users` and `expenses` tables from Step 1 already expose every field the page needs.

## Templates

- **Create:** `templates/profile.html` — the profile page itself.
- **Modify:** `templates/base.html` — when signed in, the navbar's "Sign out" link should be preceded (or accompanied) by a "Profile" link pointing to `url_for('profile')`, so the page is discoverable from the global nav.

## Files to change

- `app.py` — replace the `/profile` placeholder with a real handler that:
  1. Reads the current user via a parameterised `SELECT id, name, email, created_at FROM users WHERE id = ?` (re-fetch from the DB, not just the session — so any future name/email change shows up immediately).
  2. Computes three small aggregates in a single query each (or one combined query — see "Implementation notes" below) over the user's `expenses`:
     - **Total spent** — `SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?`.
     - **Transaction count** — `SELECT COUNT(*) FROM expenses WHERE user_id = ?`.
     - **Top category** — `SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 1`. If the user has zero expenses, render "No expenses yet.".
  3. Passes `user` (a dict-like row), `total_spent`, `tx_count`, and `top_category` (or `None`) to the template.

- `templates/base.html` — add a "Profile" link in the signed-in branch of the navbar, before the user's name.

## Files to create

- `.claude/specs/04-profile-page-design.md` (this spec).
- `templates/profile.html` — the page.

## New dependencies
No new pip packages. Uses:
- `sqlite3` (stdlib) via `database.db.get_db()`.
- `flask.session`, `flask.render_template`, `flask.redirect`, `flask.url_for` — all already imported.

## Rules for implementation

- No SQLAlchemy or any other ORM — raw `sqlite3` only.
- All SQL is parameterised (`?` placeholders). Never f-string or `%` into SQL.
- The `/profile` route must be gated by `_login_required` (same decorator used by `/dashboard` in Step 3). The session's `user_id` is the only identity used.
- Never echo the password or `password_hash` to the template. The handler's `SELECT` deliberately omits `password_hash`.
- Re-fetch the user row from the DB on every request rather than relying on `session["user_name"]` / `session["user_id"]` for display values. The session is for identity (`user_id`); the DB row is the source of truth for what to show.
- Currency in the stats is **rupees (₹)**, matching the rest of Spendly. Format with two decimals (`₹1,250.00`).
- Dates in the page use a human-readable form. `users.created_at` is stored as `YYYY-MM-DD HH:MM:SS` (SQLite `datetime('now')`). Display the date part only, formatted as e.g. "18 July 2026".
- All templates extend `base.html`. No new inline `<style>` blocks. Reuse the existing design tokens: `.auth-section`, `.auth-container`, `.auth-card`, `.auth-header`, `.auth-title`, `.auth-subtitle`, `.btn-submit`, `.form-group`, plus any new layout classes that go into `static/css/style.css` (defined below).
- The profile page should introduce a small set of new layout classes in `style.css` for stat tiles and a key/value list, **using existing CSS variables only** (no new hex values). Specifically, add classes like `.profile-section`, `.profile-stats`, `.stat-tile`, `.stat-tile-label`, `.stat-tile-value`, `.info-list`, `.info-list-row`, `.info-list-label`, `.info-list-value`. All colors must come from `--ink`, `--ink-muted`, `--paper-card`, `--border`, `--accent`, etc.
- Do NOT add a `flash()` mechanism. If a future step needs a notification, add it then.
- The page must work for a user with **zero** expenses (the demo seed has 8, but a freshly registered user has none). Render the stats block with `₹0.00`, `0`, and "No expenses yet." in the top-category slot — no 500, no division-by-zero.
- Do NOT modify `database/db.py`.
- Do NOT introduce any new routes (no `/profile/edit` etc. in this step).

## Implementation notes

The three aggregate queries can be combined into one round-trip for efficiency, but **clarity beats cleverness** for a teaching scaffold. Either approach is acceptable; pick whichever is more readable. A simple three-query approach is fine and matches the per-step teaching style of the rest of the codebase.

If combining, the pattern is:

```sql
SELECT
  (SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = :uid) AS total_spent,
  (SELECT COUNT(*)               FROM expenses WHERE user_id = :uid) AS tx_count,
  (SELECT category FROM expenses WHERE user_id = :uid
   GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1) AS top_category
```

Either way, the SQL must remain parameterised.

## Definition of done

- [ ] `GET /profile` while not signed in redirects to `/login`.
- [ ] `GET /profile` while signed in returns 200.
- [ ] The page shows the user's `name`, `email`, and a "Member since" line with a human-readable date.
- [ ] The page never displays the password or `password_hash`.
- [ ] The page shows "Total spent" as `₹<amount>` with two decimals (e.g. `₹5,148.00` for the demo user).
- [ ] The page shows "Transactions" as the count of the user's expenses.
- [ ] The page shows "Top category" as the category with the highest total amount for the user (for the demo user: "Bills" at ₹2,200).
- [ ] A freshly registered user with no expenses sees `₹0.00`, `0`, and "No expenses yet." — no 500.
- [ ] The navbar (when signed in) shows a "Profile" link pointing to `/profile`.
- [ ] The page extends `base.html` and uses existing CSS variables only — `grep` of `templates/profile.html` finds no hex literals.
- [ ] `static/css/style.css` has the new layout classes (`.profile-section`, `.profile-stats`, `.stat-tile`, etc.) and all of them reference existing `:root` variables only.
- [ ] No new pip packages were added.
- [ ] `database/db.py` is unchanged.
- [ ] No new routes were added (no `/profile/edit`, etc.).
- [ ] All SQL in the new handler is parameterised; no f-strings or `%` formatting in queries.
- [ ] The page is readable on a phone-width viewport (the existing `.auth-container` max-width and the new layout classes should not break the existing responsive rules in `style.css`).
