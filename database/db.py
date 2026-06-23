import sqlite3
from flask import current_app
import os
from datetime import datetime


def _get_database_path():
    """Return the absolute path to the configured SQLite database."""
    database_file = current_app.config['DATABASE']
    if os.path.isabs(database_file):
        return database_file
    return os.path.join(current_app.root_path, database_file)


def get_db_connection():
    """Open a connection to the SQLite database."""
    db_path = _get_database_path()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    """Create the notes table if it does not already exist."""
    db_path = _get_database_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            date_added TEXT,
            last_updated TEXT,
            is_archived INTEGER DEFAULT 0
        )
        '''
    )
    connection.commit()

    cursor.execute("PRAGMA table_info(notes)")
    columns = [row['name'] for row in cursor.fetchall()]
    if 'last_updated' not in columns:
        try:
            cursor.execute('ALTER TABLE notes ADD COLUMN last_updated TEXT')
            connection.commit()
        except sqlite3.OperationalError:
            # If column already exists or concurrent change occurred, ignore
            pass
    if 'is_archived' not in columns:
        try:
            cursor.execute('ALTER TABLE notes ADD COLUMN is_archived INTEGER DEFAULT 0')
            connection.commit()
        except sqlite3.OperationalError:
            pass

    connection.close()


def get_all_notes():
    """Return all notes as a list of dictionaries."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM notes WHERE IFNULL(is_archived,0)=0 ORDER BY date_added DESC')
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_archived_notes():
    """Return archived notes."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM notes WHERE IFNULL(is_archived,0)=1 ORDER BY date_added DESC')
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_note_by_id(note_id):
    """Return a single note by its ID or None if not found."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def search_notes(query):
    """Search notes by title, category, or tags."""
    connection = get_db_connection()
    cursor = connection.cursor()
    search_query = f'%{query}%'
    cursor.execute(
        '''
        SELECT * FROM notes
        WHERE IFNULL(is_archived,0)=0
          AND (title LIKE ?
          OR category LIKE ?
          OR tags LIKE ?)
        ORDER BY date_added DESC
        ''',
        (search_query, search_query, search_query)
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def insert_note(title, category, content, tags=None):
    """Insert a new note into the notes table with the current date."""
    connection = get_db_connection()
    cursor = connection.cursor()
    date_added = datetime.now().strftime('%Y-%m-%d')
    last_updated = date_added
    cursor.execute(
        '''
        INSERT INTO notes (title, category, content, tags, date_added, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (title, category, content, tags, date_added, last_updated)
    )
    connection.commit()
    connection.close()


def update_note(note_id, title, category, content, tags=None):
    """Update an existing note's fields."""
    connection = get_db_connection()
    cursor = connection.cursor()
    last_updated = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        '''
        UPDATE notes
        SET title = ?, category = ?, content = ?, tags = ?, last_updated = ?
        WHERE id = ?
        ''',
        (title, category, content, tags, last_updated, note_id)
    )
    connection.commit()
    connection.close()


def delete_note(note_id):
    """Remove a note from the database."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    connection.commit()
    connection.close()


def archive_note(note_id):
    """Mark a note as archived (soft-delete)."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE notes SET is_archived = 1 WHERE id = ?', (note_id,))
    connection.commit()
    connection.close()


def restore_note(note_id):
    """Restore an archived note."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE notes SET is_archived = 0 WHERE id = ?', (note_id,))
    connection.commit()
    connection.close()
