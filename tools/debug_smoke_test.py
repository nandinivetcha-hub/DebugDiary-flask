import os
import sys
import time
sys.path.insert(0, os.path.abspath('..'))
from app import app
from database.db import get_all_notes, insert_note, get_note_by_id

with app.app_context():
    client = app.test_client()
    ts = int(time.time())
    title = f"Smoke Test Note {ts}"
    insert_note(title, 'Error', 'This is a smoke test note.', 'smoke,testing')
    notes = get_all_notes()
    n = next((n for n in notes if n['title'] == title), None)
    print('inserted', bool(n), 'id', n['id'] if n else None)
    r = client.get(f'/notes?tag=smoke')
    html = r.get_data(as_text=True)
    print('/notes?tag=smoke', r.status_code)
    print('title in html', title in html)
    if title in html:
        idx = html.index(title)
        print('snippet', html[max(0, idx-120):idx+120])
    r2 = client.get(f'/note/{n['id']}') if n else None
    if r2:
        view_html = r2.get_data(as_text=True)
        print('/note status', r2.status_code)
        print('copy exact', 'id="copy-btn"' in view_html)
        print('copy any', 'copy-btn' in view_html)
        if 'id="copy-btn"' in view_html:
            idx = view_html.index('id="copy-btn"')
            print('copy snippet', view_html[max(0, idx-120):idx+120])
    else:
        print('no note view')
