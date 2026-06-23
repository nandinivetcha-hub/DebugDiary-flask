document.addEventListener('DOMContentLoaded', function () {
  var deleteLinks = document.querySelectorAll('.delete-note');
  deleteLinks.forEach(function (link) {
    link.addEventListener('click', function (event) {
      if (!confirm('Are you sure you want to delete this note?')) {
        event.preventDefault();
      }
    });
  });

  var permanentDeleteLinks = document.querySelectorAll('.permanent-delete-note');
  permanentDeleteLinks.forEach(function (link) {
    link.addEventListener('click', function (event) {
      if (!confirm('Are you sure you want to permanently delete this note? This action cannot be undone.')) {
        event.preventDefault();
      }
    });
  });

  var archiveLinks = document.querySelectorAll('.archive-note');
  archiveLinks.forEach(function (link) {
    link.addEventListener('click', function (event) {
      if (!confirm('Are you sure you want to archive this note?')) {
        event.preventDefault();
      }
    });
  });

  var copyBtn = document.getElementById('copy-btn');
  var copyMessage = document.getElementById('copy-message');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var contentEl = document.getElementById('note-content');
      if (!contentEl || !navigator.clipboard) return;
      var text = contentEl.innerText || contentEl.textContent || '';
      navigator.clipboard.writeText(text).then(function () {
        if (copyMessage) {
          copyMessage.classList.remove('d-none');
          setTimeout(function () { copyMessage.classList.add('d-none'); }, 1500);
        }
      }).catch(function (err) {
        console.error('Clipboard error', err);
      });
    });
  });

  var readingBtn = document.getElementById('reading-mode-btn');
  if (readingBtn) {
    readingBtn.addEventListener('click', function () {
      var card = document.getElementById('note-view-card');
      if (!card) return;
      card.classList.toggle('reading-mode');
      var actions = card.querySelectorAll('.action-buttons');
      actions.forEach(function (el) { el.classList.toggle('d-none'); });
      if (copyBtn) {
        copyBtn.classList.toggle('d-none');
      }
      readingBtn.innerText = card.classList.contains('reading-mode') ? 'Exit Reading' : 'Reading Mode';
    });
  }
});
