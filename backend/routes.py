from flask import render_template, request, redirect, url_for, flash, send_file
from database.db import (
    get_all_notes,
    insert_note,
    get_note_by_id,
    update_note,
    delete_note,
    search_notes,
)
from database.db import archive_note, get_archived_notes, restore_note
from datetime import datetime


def register_routes(app):
    """Register Flask routes for the DebugDiary application."""

    def badge_class(category):
        """Map note categories to CSS badge styles."""
        return {
            'Error': 'badge-error',
            'Command': 'badge-command',
            'Code Snippet': 'badge-code-snippet',
            'Interview Question': 'badge-interview-question',
            'Resource': 'badge-resource',
        }.get(category, 'badge-secondary')

    app.jinja_env.filters['badge_class'] = badge_class

    @app.route('/')
    def index():
        notes = get_all_notes()
        recent_notes = notes[:5]
        stats = {
            'total': len(notes),
            'archived': len(get_archived_notes()),
            'recent_count': len(recent_notes),
            'Error': sum(1 for note in notes if note['category'] == 'Error'),
            'Command': sum(1 for note in notes if note['category'] == 'Command'),
            'Code Snippet': sum(1 for note in notes if note['category'] == 'Code Snippet'),
            'Interview Question': sum(1 for note in notes if note['category'] == 'Interview Question'),
            'Resource': sum(1 for note in notes if note['category'] == 'Resource'),
        }

        return render_template(
            'index.html',
            stats=stats,
            recent_notes=recent_notes,
        )

    @app.route('/add', methods=['GET', 'POST'])
    def add_note():
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            category = request.form.get('category', '').strip()
            content = request.form.get('content', '').strip()
            tags = request.form.get('tags', '').strip()

            insert_note(title, category, content, tags)
            flash('Note added successfully.', 'success')
            return redirect(url_for('notes'))

        default_category = request.args.get('category', 'Error')
        return render_template('add_note.html', default_category=default_category)

    @app.route('/notes')
    def notes():
        # Retrieve query parameters for search, filtering, sorting and tag filtering
        q = request.args.get('q', '').strip()
        category = request.args.get('category', 'All')
        sort = request.args.get('sort', 'newest')
        tag = request.args.get('tag', '').strip()

        # Start from all notes and apply filters in Python to avoid changing DB functions
        all_notes = get_all_notes()
        filtered = all_notes

        # Search by title, content, tags or category (case-insensitive substring match)
        if q:
            q_low = q.lower()
            filtered = [n for n in filtered if (
                q_low in (n.get('title') or '').lower()
                or q_low in (n.get('content') or '').lower()
                or q_low in (n.get('tags') or '').lower()
                or q_low in (n.get('category') or '').lower()
            )]

        # Category filter
        if category and category != 'All':
            filtered = [n for n in filtered if n.get('category') == category]

        # Tag filter (exact tag match, case-insensitive)
        if tag:
            t_low = tag.lower()
            def has_tag(n):
                tags = n.get('tags') or ''
                tag_list = [t.strip().lower() for t in tags.split(',') if t.strip()]
                return t_low in tag_list
            filtered = [n for n in filtered if has_tag(n)]

        # Sorting
        def parse_date(s):
            try:
                return datetime.strptime(s, '%Y-%m-%d')
            except Exception:
                return datetime.min

        if sort == 'newest':
            filtered.sort(key=lambda n: parse_date(n.get('date_added') or ''), reverse=True)
        elif sort == 'oldest':
            filtered.sort(key=lambda n: parse_date(n.get('date_added') or ''), reverse=False)
        elif sort == 'alpha':
            filtered.sort(key=lambda n: (n.get('title') or '').lower())
        elif sort == 'category':
            filtered.sort(key=lambda n: (n.get('category') or '', n.get('title') or ''))

        # Render the notes page with current filter state so the UI can reflect selections
        return render_template('notes.html', notes=filtered, q=q, category=category, sort=sort, tag=tag)

    @app.route('/search')
    def search():
        query = request.args.get('q', '').strip()
        notes = []
        if query:
            notes = search_notes(query)
        return render_template('search_results.html', notes=notes, query=query)

    @app.route('/note/<int:id>')
    def view_note(id):
        note = get_note_by_id(id)
        if note is None:
            return redirect(url_for('index'))
        # Find related notes by shared category or tags (exclude current note)
        all_notes = get_all_notes()
        related = []

        # Prepare tag set for the current note
        note_tags = [t.strip().lower() for t in (note.get('tags') or '').split(',') if t.strip()]

        def score_other(n):
            if n['id'] == note['id']:
                return -1
            score = 0
            # same category
            if n.get('category') == note.get('category'):
                score += 2
            # shared tags
            other_tags = [t.strip().lower() for t in (n.get('tags') or '').split(',') if t.strip()]
            shared = set(note_tags) & set(other_tags)
            score += len(shared)
            return score

        scored = []
        for n in all_notes:
            if n['id'] == note['id']:
                continue
            s = score_other(n)
            if s > 0:
                scored.append((s, n))

        # sort by score desc then date_added desc
        from datetime import datetime as _dt
        def parse_date(s):
            try:
                return _dt.strptime(s, '%Y-%m-%d')
            except Exception:
                return _dt.min

        scored.sort(key=lambda pair: (pair[0], parse_date(pair[1].get('date_added') or '')), reverse=True)
        related = [pair[1] for pair in scored][:5]

        return render_template('view_note.html', note=note, related=related)

    @app.route('/edit/<int:id>', methods=['GET', 'POST'])
    def edit_note(id):
        note = get_note_by_id(id)
        if note is None:
            return redirect(url_for('index'))

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            category = request.form.get('category', '').strip()
            content = request.form.get('content', '').strip()
            tags = request.form.get('tags', '').strip()

            update_note(id, title, category, content, tags)
            flash('Note updated successfully.', 'success')
            return redirect(url_for('notes'))

        return render_template('edit_note.html', note=note)

    @app.route('/delete/<int:id>')
    def delete_note_route(id):
        """Archive a note (soft-delete)."""
        note = get_note_by_id(id)
        if note is not None:
            archive_note(id)
            flash('Note archived successfully.', 'success')
        return redirect(url_for('notes'))

    @app.route('/permanently-delete/<int:id>')
    def permanently_delete_note_route(id):
        """Permanently delete a note from the database."""
        note = get_note_by_id(id)
        if note is not None:
            delete_note(id)
            flash('Note permanently deleted.', 'warning')
            return redirect(url_for('archived'))
        return redirect(url_for('archived'))

    @app.route('/archive/<int:id>')
    def archive_note_route(id):
        note = get_note_by_id(id)
        if note is not None:
            archive_note(id)
            flash('Note archived successfully.', 'success')
        return redirect(url_for('notes'))

    @app.route('/archived')
    def archived():
        archived_notes = get_archived_notes()
        return render_template('archived.html', notes=archived_notes)

    @app.route('/restore/<int:id>')
    def restore_note_route(id):
        note = get_note_by_id(id)
        if note is not None:
            restore_note(id)
            flash('Note restored successfully.', 'success')
        return redirect(url_for('archived'))

    @app.route('/export/pdf')
    def export_pdf():
        # Maintain filters from query params (q, category, tag, sort)
        q = request.args.get('q', '').strip()
        category = request.args.get('category', 'All')
        tag = request.args.get('tag', '').strip()
        sort = request.args.get('sort', 'newest')

        # Start from search results if a query is present to leverage search_notes()
        if q:
            notes_list = search_notes(q)
        else:
            notes_list = get_all_notes()

        # Apply category filter
        if category and category != 'All':
            notes_list = [n for n in notes_list if n.get('category') == category]

        # Apply tag filter
        if tag:
            t_low = tag.lower()
            def has_tag(n):
                tags = n.get('tags') or ''
                tag_list = [t.strip().lower() for t in tags.split(',') if t.strip()]
                return t_low in tag_list
            notes_list = [n for n in notes_list if has_tag(n)]

        # Sorting
        from datetime import datetime as _dt
        def parse_date(s):
            try:
                return _dt.strptime(s, '%Y-%m-%d')
            except Exception:
                return _dt.min

        if sort == 'newest':
            notes_list.sort(key=lambda n: parse_date(n.get('date_added') or ''), reverse=True)
        elif sort == 'oldest':
            notes_list.sort(key=lambda n: parse_date(n.get('date_added') or ''), reverse=False)
        elif sort == 'alpha':
            notes_list.sort(key=lambda n: (n.get('title') or '').lower())
        elif sort == 'category':
            notes_list.sort(key=lambda n: (n.get('category') or '', n.get('title') or ''))

        # Try to import ReportLab for PDF generation.
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
        except Exception:
            flash('PDF export requires ReportLab. Install with: pip install reportlab', 'danger')
            return redirect(request.referrer or url_for('notes'))

        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        h2 = styles['Heading2']
        body = styles['BodyText']
        pre_style = ParagraphStyle('pre', parent=styles['Code'] if 'Code' in styles else body, fontName='Courier', fontSize=9)

        elements = []
        elements.append(Paragraph('DebugDiary - Personal Developer Knowledge Base', title_style))
        elements.append(Spacer(1, 12))

        if not notes_list:
            elements.append(Paragraph('No notes found for the selected filters.', body))
        else:
            for note in notes_list:
                elements.append(Paragraph(note.get('title', 'Untitled'), h2))
                meta = ('<b>Category:</b> %s &nbsp;&nbsp; <b>Tags:</b> %s &nbsp;&nbsp; '
                        '<b>Created:</b> %s &nbsp;&nbsp; <b>Last Updated:</b> %s') % (
                    note.get('category', ''), note.get('tags', ''), note.get('date_added', ''), note.get('last_updated', '')
                )
                elements.append(Paragraph(meta, body))
                elements.append(Spacer(1, 6))
                # Preserve newlines in content by replacing with <br/>
                content_text = (note.get('content') or '').replace('\n', '<br/>')
                elements.append(Paragraph(content_text, body))
                elements.append(Spacer(1, 12))

        doc.build(elements)
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name='debugdiary_export.pdf', mimetype='application/pdf')
