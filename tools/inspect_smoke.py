import os
import sys
import time
sys.path.insert(0, os.path.abspath('..'))
from app import app
from database.db import insert_note, get_all_notes

with app.app_context():
    client = app.test_client()
    ts = int(time.time())
    title = f"Smoke Test Note {ts}"
    insert_note(title, 'Error', 'This is a smoke test note.', 'smoke,testing')
    notes = get_all_notes()
    my = next((n for n in notes if n.get('title') == title), None)
    print('inserted note found?', bool(my))
    if not my:
        sys.exit(1)
    nid = my['id']
    r = client.get('/notes?tag=smoke')
    html = r.get_data(as_text=True)
    print('/notes?tag=smoke status', r.status_code)
    print('title appears in notes page?', title in html)
    if title in html:
        idx = html.find(title)
        print('snippet around title:', html[max(0, idx-80):idx+120])
    r2 = client.get(f'/note/{nid}')
    view_html = r2.get_data(as_text=True)
    print('/note/{nid} status', r2.status_code)
    print('copy button present exactly', 'id="copy-btn"' in view_html)
    print('copy button present any', 'copy-btn' in view_html)
    if 'id="copy-btn"' in view_html:
        idx = view_html.find('id="copy-btn"')
        print('copy snippet:', view_html[max(0, idx-80):idx+120])
    print('related section present', 'Related Notes' in view_html)
    print('dark/theme lower present', 'dark' in view_html.lower() or 'theme' in view_html.lower())
    # cleanup
    from database.db import delete_note
    delete_note(nid)
