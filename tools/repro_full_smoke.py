import os
import sys
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
    print('inserted note found', bool(my), 'id', my and my['id'])
    nid = my['id']
    def check_desc(route, method='get', data=None, expected=(200, 302)):
        if method == 'get':
            r = client.get(route, follow_redirects=False)
        else:
            r = client.post(route, data=data or {}, follow_redirects=False)
        print('check', route, 'status', r.status_code)
        return r
    for name, route, method, data, expected in [
        ('Dashboard', '/', 'get', None, [200]),
        ('Notes', '/notes', 'get', None, [200]),
        ('Add Note (GET)', '/add', 'get', None, [200]),
        ('Add Note (POST)', '/add', 'post', {'title': f'Added {ts}', 'category': 'Error', 'content': 'x', 'tags': ''}, [302]),
        ('View Note', f'/note/{nid}', 'get', None, [200]),
        ('Edit Note (GET)', f'/edit/{nid}', 'get', None, [200]),
        ('Edit Note (POST)', f'/edit/{nid}', 'post', {'title': title, 'category': 'Error', 'content': 'updated', 'tags': 'smoke'}, [302]),
        ('Export PDF', '/export/pdf', 'get', None, [200,302]),
        ('Search+Filter+Sort+Tag', f'/notes?q=Smoke&category=All&sort=alpha&tag=smoke', 'get', None, [200]),
        ('Archive Note', f'/archive/{nid}', 'get', None, [302]),
        ('Archived Page', '/archived', 'get', None, [200]),
        ('Permanently Delete (archived)', f'/permanently-delete/{nid}', 'get', None, [302]),
    ]:
        r = check_desc(route, method, data, expected)
        if r.status_code not in expected:
            print('unexpected status', name, r.status_code)
    r = client.get('/notes?tag=smoke')
    html = r.get_data(as_text=True)
    print('tag filter check status', r.status_code, 'title found', title in html)
    if title not in html:
        print(html[:1200])
    r = client.get(f'/note/{nid}')
    view_html = r.get_data(as_text=True)
    print('view note status', r.status_code, 'copy exact', 'id="copy-btn"' in view_html, 'copy any', 'copy-btn' in view_html)
    if title not in view_html:
        print('title missing from view html')
    print('related present', 'Related Notes' in view_html)
    print('dark words present', 'dark' in view_html.lower() or 'theme' in view_html.lower())
    # cleanup
    for n in get_all_notes() + get_archived_notes():
        if str(ts) in (n.get('title') or ''):
            delete_note(n['id'])
