import os
import sys
sys.path.insert(0, os.path.abspath('..'))
from app import app
from database.db import insert_note, get_all_notes

with app.app_context():
    client = app.test_client()
    ts = 999999999
    title = f"Smoke Test Note {ts}"
    insert_note(title, 'Error', 'This is a smoke test note.', 'smoke,testing')
    r = client.get('/notes?tag=smoke')
    html = r.get_data(as_text=True)
    print('status', r.status_code)
    print('title present', title in html)
    print('html snippet', html[html.find(title)-80:html.find(title)+140] if title in html else 'not found')
    # Cleanup
    notes = get_all_notes()
    for n in notes:
        if n['title'] == title:
            print('cleanup removing', n['id'])
            from database.db import delete_note
            delete_note(n['id'])
