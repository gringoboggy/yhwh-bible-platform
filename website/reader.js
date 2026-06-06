// reader.js — copy a column of the chapter reader to the clipboard.
// Progressive enhancement only: the scripture text is plain, selectable Unicode, so
// copy-and-paste works without this script too. No tracking, no dependencies.
(function () {
  function textOf(sel) {
    return Array.from(document.querySelectorAll(sel))
      .map(function (el) { return el.textContent.trim(); })
      .join('\n');
  }
  document.querySelectorAll('.rdr-copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var sel = btn.dataset.col === 'en' ? '.rdr-en' : '.rdr-gez';
      var label = btn.textContent;
      var done = function () {
        btn.textContent = 'Copied ✓';
        setTimeout(function () { btn.textContent = label; }, 1500);
      };
      var text = textOf(sel);
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { /* blocked — select manually */ });
      }
    });
  });
})();
