import sys
import os
import time
# Ensure project root is on sys.path so `from app import app` works when invoked from tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from database.db import get_all_notes, insert_note, get_note_by_id, delete_note, archive_note, get_archived_notes

results = {
    'success': [],
    'warnings': [],
    'errors': []
}

with app.app_context():
    client = app.test_client()

    ts = int(time.time())
    title = f"Smoke Test Note {ts}"
    insert_note(title, 'Error', 'This is a smoke test note.', 'smoke,testing')

    # find the note
    notes = get_all_notes()
    my = next((n for n in notes if n.get('title') == title), None)
    if not my:
        results['errors'].append('Could not find inserted smoke test note')
        print(results)
        sys.exit(2)
    nid = my['id']

    def check(route, method='get', data=None, expected=(200, 302)):
        try:
            if method.lower() == 'get':
                r = client.get(route, follow_redirects=False)
            else:
                r = client.post(route, data=data or {}, follow_redirects=False)
            status = r.status_code
            ok = (status in expected)
            return ok, status, r
        except Exception as e:
            return False, None, e

    # List of checks
    checks = []
    checks.append(('Dashboard', '/', 'get', None, [200]))
    checks.append(('Notes', '/notes', 'get', None, [200]))
    checks.append(('Add Note (GET)', '/add', 'get', None, [200]))
    checks.append(('Add Note (POST)', '/add', 'post', {'title': f'Added {ts}', 'category': 'Error', 'content': 'x', 'tags': ''}, [302]))
    checks.append(('View Note', f'/note/{nid}', 'get', None, [200]))
    checks.append(('Edit Note (GET)', f'/edit/{nid}', 'get', None, [200]))
    checks.append(('Edit Note (POST)', f'/edit/{nid}', 'post', {'title': title, 'category': 'Error', 'content': 'updated', 'tags': 'smoke'}, [302]))
    checks.append(('Export PDF', '/export/pdf', 'get', None, [200,302]))
    checks.append(('Search+Filter+Sort+Tag', f'/notes?q=Smoke&category=All&sort=alpha&tag=smoke', 'get', None, [200]))

    for name, route, method, data, expected in checks:
        ok, status, resp = check(route, method, data, expected)
        if ok:
            results['success'].append(f'{name}: {route} -> {status}')
        else:
            if isinstance(resp, Exception):
                results['errors'].append(f'{name}: Exception {resp}')
            else:
                results['errors'].append(f'{name}: Unexpected status {status} for {route}')

    # Verify search returned something for smoke tag before archive/delete actions
    r = client.get('/notes?tag=smoke')
    if r.status_code == 200 and title in r.get_data(as_text=True):
        results['success'].append('Tag filter displays inserted note')
    else:
        results['warnings'].append('Tag filter did not surface the inserted note (may be filtered out)')

    # Verify copy button exists in view template before note deletion
    r = client.get(f'/note/{nid}')
    view_html = r.get_data(as_text=True)
    if 'id="copy-btn"' in view_html or "copy-btn" in view_html:
        results['success'].append('Copy-to-clipboard button present in view_note template')
    else:
        results['warnings'].append('Copy button not found in view template')

    # Verify related notes section renders (presence of 'Related Notes')
    if 'Related Notes' in view_html:
        results['success'].append('Related notes block present in view template (static check)')
    else:
        results['warnings'].append('Related notes block not present in view template (may be absent if none)')

    # Dark mode toggle check (best-effort: look for explicit theme toggle markers)
    theme_toggle_markers = ['id="theme-toggle"', 'id="dark-mode"', 'id="light-mode"', 'class="theme-toggle"', 'class="dark-mode"', 'class="light-mode"', 'theme-switch']
    if any(marker in view_html for marker in theme_toggle_markers):
        results['success'].append('Dark mode toggle or theme switch found in templates (manual review recommended)')
    else:
        results['warnings'].append('No explicit dark mode toggle found in templates')

    # Non-destructive route checks done; now verify archive/delete behavior
    destructive_checks = []
    destructive_checks.append(('Archive Note', f'/archive/{nid}', 'get', None, [302]))
    destructive_checks.append(('Archived Page', '/archived', 'get', None, [200]))
    destructive_checks.append(('Permanently Delete (archived)', f'/permanently-delete/{nid}', 'get', None, [302]))

    for name, route, method, data, expected in destructive_checks:
        ok, status, resp = check(route, method, data, expected)
        if ok:
            results['success'].append(f'{name}: {route} -> {status}')
        else:
            if isinstance(resp, Exception):
                results['errors'].append(f'{name}: Exception {resp}')
            else:
                results['errors'].append(f'{name}: Unexpected status {status} for {route}')

    # List routes
    routes = []
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        routes.append(f'{rule.endpoint} {rule.rule} methods={sorted(list(rule.methods))}')

    # Cleanup: try to remove inserted notes if they still exist
    try:
        # remove any note with our timestamp in title
        alln = get_all_notes() + get_archived_notes()
        for n in alln:
            if str(ts) in (n.get('title') or ''):
                delete_note(n['id'])
    except Exception as e:
        results['warnings'].append(f'Cleanup warning: {e}')

    # Print report
    print('=== SMOKE TEST REPORT ===')
    print('\n-- Successful tests --')
    for s in results['success']:
        print(f'- {s}')
    print('\n-- Warnings --')
    for w in results['warnings']:
        print(f'- {w}')
    print('\n-- Errors --')
    for e in results['errors']:
        print(f'- {e}')
    print('\n-- Registered routes --')
    for r in routes:
        print('- ' + r)

    # Exit with non-zero if errors
    if results['errors']:
        sys.exit(2)
    else:
        sys.exit(0)
