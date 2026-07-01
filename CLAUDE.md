# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**Spendly** is a Flask web app for tracking personal expenses. The codebase is a
**step-by-step teaching scaffold**: many routes are placeholders returning
strings like `"Logout — coming in Step 3"` and `# Students will write this file`
comments mark where future code goes. When implementing something, check the
naming of these placeholders (e.g. `Step 4`, `Step 7`, `Step 8`, `Step 9`)
to learn which step a feature belongs to and what shape it should take.

Branding is "Spendly"; UI uses the rupee symbol (₹) and is tuned for an
Indian-market audience. The legal copy (`terms.html`, `privacy.html`) is
already finalized — do not regenerate or paraphrase it without being asked.

## Run / develop

- Run the dev server: `python app.py` — listens on **port 5001** with
  `debug=True` (set in `if __name__ == "__main__":`).
- Dependencies: `flask==3.1.3`, `werkzeug==3.1.6`, `pytest==8.3.5`,
  `pytest-flask==1.3.0`. Install in a venv.
- `requirements.txt` already pulls pytest, but no `tests/` directory exists
  yet — when adding the first test, follow `pytest-flask`'s
  `client.get/post` pattern and create a conftest that yields a fresh
  Flask test client.
- Pre-approved Bash commands live in `.claude/settings.local.json`
  (`python app.py`, `curl *`, the venv Python, `git add *`, `git commit *`).

## Architecture

```
app.py                  # Flask app + all route handlers
database/
  __init__.py           # empty
  db.py                 # STUB — students fill in get_db / init_db / seed_db
templates/
  base.html             # layout (navbar, footer, blocks: title/head/content/scripts)
  landing.html          # marketing page + YouTube-modal via {% block scripts %}
  login.html, register.html, terms.html, privacy.html
static/
  css/style.css         # single CSS file; design tokens at :root (--ink, --accent, etc.)
  js/main.js            # placeholder; currently only landing.html has inline {% block scripts %}
```

### Key patterns

- **Template inheritance**: every page extends `base.html`. Use the four
  defined blocks — `title`, `head`, `content`, `scripts`. Don't add CSS via
  inline `<style>` in templates except for one-off modal/legal pages
  (landing, terms, privacy already do this).
- **Design tokens**: colors, fonts (`DM Serif Display`, `DM Sans`),
  radii, and widths are CSS variables in `style.css :root`. Reuse them
  rather than hard-coding values. The accent palette is forest green
  (`--accent: #1a472a`) with a warm amber secondary (`--accent-2`).
- **Forms**: `login.html` and `register.html` already POST to `/login`
  and `/register`, but `app.py` only defines **GET** handlers for those
  routes. Adding `methods=["GET", "POST"]` and wiring the form is part of
  the upcoming auth steps.
- **DB layer** (when implemented in `database/db.py`): expected to
  expose `get_db()` returning a SQLite connection with
  `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`;
  `init_db()` running `CREATE TABLE IF NOT EXISTS`; `seed_db()` for
  dev sample data. The DB file is gitignored (`expense_tracker.db`).

## Things to watch for

- The landing page's YouTube iframe uses a deferred-load pattern
  (`data-src` → `src` on modal open, cleared on close to stop playback).
  If you change it, keep the autoplay-on-open / clear-on-close behavior.
- `.gitignore` already covers `venv/`, `__pycache__/`, `*.pyc`, `.env`,
  `expense_tracker.db`, `.DS_Store`, `.claude/plans/`. Don't bypass it.
- Port 5000 is often taken on developer machines — the app deliberately
  uses 5001. If a future feature needs port changes, update both `app.py`
  and any docs that mention it.
