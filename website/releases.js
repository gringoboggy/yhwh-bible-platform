// website/releases.js — progressive upgrade of the "latest release" card.
// The page is already correct without this (the build-time fallback is shown).
// If the serverless feed (latest.php) reports a published release, fill in the
// live version, date, and download links.
(function () {
  fetch('latest.php', { headers: { accept: 'application/json' } })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.ok || !d.version) return;
      var name = document.getElementById('latest-name');
      var meta = document.getElementById('latest-meta');
      var links = document.getElementById('latest-links');
      if (name) name.textContent = 'YHWH Ya’ Way ' + d.version;
      if (meta && d.date) meta.textContent = 'Released ' + d.date;
      if (links && d.assets && d.assets.length) {
        links.innerHTML = '';
        d.assets.forEach(function (a) {
          var el = document.createElement('a');
          el.className = 'btn-platform';
          el.href = a.url;
          el.textContent = a.label;
          links.appendChild(el);
          links.appendChild(document.createTextNode(' '));
        });
      }
    })
    .catch(function () { /* leave the static fallback in place */ });
})();
