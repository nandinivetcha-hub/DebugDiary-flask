# DebugDiary

DebugDiary is a small Flask application for storing and viewing debug journal notes.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```

## Project structure

- `app.py` - application routes and startup logic.
- `database/db.py` - SQLite database helper functions.
- `templates/` - Jinja2 HTML templates.
- `static/` - static CSS and JavaScript assets.
- `instance/debugdiary.db` - SQLite database file.
