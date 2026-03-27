# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SellTrack -- NiceGUI-based inventory management app for tracking items for sale. Polish-language UI.
Rewrite of the Flask "inventory" project using NiceGUI (Vue/Quasar frontend, FastAPI backend).

## Running the App

```bash
source venv/bin/activate
python main.py
# Opens at http://localhost:5000
```

## Architecture

**Stack:** NiceGUI 2.x (FastAPI + Vue/Quasar), SQLAlchemy 2.x (SQLite), Pillow

**File structure:**
- `main.py` -- entry point, static files config, category seeding, `ui.run()`
- `db.py` -- SQLAlchemy engine, `Base`, `get_db()` context manager, `init_db()`
- `models.py` -- `Item`, `ItemImage`, `Category` models. Item has `calculated_status` property (computed from `activation_date` + `expiration_days`)
- `services.py` -- image processing (EXIF, resize, format), ZIP export helpers
- `pages/` -- NiceGUI page definitions
  - `__init__.py` -- shared header, status constants, `create_date_input()` helper
  - `items.py` -- item CRUD pages + FastAPI export endpoints (`/api/export/...`)
  - `categories.py` -- category CRUD pages

**Key patterns:**
- `get_db()` context manager for DB sessions; use `selectinload()` for relationships when objects are used outside the session
- `@ui.refreshable` for reactive UI sections (item grid, image previews)
- Status lifecycle: `w_magazynie` -> `aktywny` -> `sprzedany`/`zdjety`; `do_likwidacji` is computed (never stored in DB)
- Category linked via `category_id` FK (not a string like the old Flask app)
- Image uploads processed immediately via `ui.upload` callback, associated to items on form save
- File downloads served via FastAPI `@app.get()` endpoints returning `FileResponse`

**Data storage:**
- SQLite database: `data/selltrack.db`
- Uploaded images: `uploads/`
- ZIP exports: `exports/`

## Deployment (Debian server)

```bash
# Na serwerze jako root:
sudo bash install.sh        # instalacja + uruchomienie
sudo bash uninstall.sh      # deinstalacja

# Zarzadzanie serwisem:
systemctl status selltrack
systemctl restart selltrack
journalctl -u selltrack -f   # logi
```

Installs to `/opt/selltrack/`, runs as systemd service under dedicated `selltrack` user on port 5000.

**Environment variables** (set in `selltrack.service` or shell):
- `SELLTRACK_HOST` -- bind address (default `0.0.0.0`)
- `SELLTRACK_PORT` -- port (default `5000`)
- `SELLTRACK_DEBUG` -- `1`/`true` enables hot-reload (off by default)

## UI Language

All user-facing text is in **Polish** (without diacritics in code strings for ASCII safety).
