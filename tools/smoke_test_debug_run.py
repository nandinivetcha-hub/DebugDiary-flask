import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from database.db import get_all_notes, insert_note, get_note_by_id, delete_note, archive_note, get_archived_notes

with app.app_context():
    client = app.test_client()
    ts = int(time.time())
    title = f"Smoke Test Note {ts}"
    insert_note(title, 'Error', 'This is a smoke test note.', 'smoke,testing')
    notes = get_all_notes()
    my = next((n for n in notes if n.get('title') == title), None)
    print('inserted note title:', title)
    print('found note:', my)
    nid = my['id']
    r = client.get('/notes?tag=smoke')
    html = r.get_data(as_text=True)
    print('/notes?tag=smoke status', r.status_code)
    print('title in html', title in html)
    if title not in html:
        print('html snippet for tags:', html[:1200])
    r = client.get(f'/note/{nid}')
    view_html = r.get_data(as_text=True)
    print('/note status', r.status_code)
    print('copy-btn exact', 'id="copy-btn"' in view_html)
    print('copy-btn any', 'copy-btn' in view_html)
    if title in view_html:
        print('note title present in html')
    else:
        print('note title missing in view html')
    # cleanup
    alln = get_all_notes() + get_archived_notes()
    for n in alln:
        if str(ts) in (n.get('title') or ''):
            print('cleanup note', n['id'])
            delete_note(n['id'])
