import os
import sys
sys.path.insert(0, os.path.abspath('..'))
from app import app
from database.db import get_all_notes

with app.app_context():
    client = app.test_client()
    notes = get_all_notes()
    print('notes count', len(notes))
    if not notes:
        print('no notes available')
        sys.exit(0)
    last = notes[-1]
    print('last note', last)
    nid = last['id']
    r = client.get(f'/note/{nid}')
    html = r.get_data(as_text=True)
    print('note id', nid)
    print('status', r.status_code)
    print('has exact id="copy-btn"', 'id="copy-btn"' in html)
    print('has copy-btn', 'copy-btn' in html)
    print('note title exact', last['title'])
    print('snippet:', html[:800])
    r2 = client.get('/notes?tag=smoke')
    print('/notes?tag=smoke status', r2.status_code)
    print('tag page contains title', 'Smoke Test Note' in r2.get_data(as_text=True))
    print('tags filter snippet:', r2.get_data(as_text=True)[:1200])
