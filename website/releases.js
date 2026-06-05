// website/releases.js — progressive enhancement of the "latest release" card.
//
// The page renders correctly WITHOUT JavaScript (the build-time fallback in
// releases.html is shown). When the project's public GitHub repo has a published
// release, this fills in the live version, date, and real download links straight
// from the GitHub Releases API.
//
// Why the API and not a server script: the site is hosted on GitHub Pages, which
// is purely static — it cannot run PHP, so the old latest.php proxy could never
// execute here (it 404s). The GitHub Releases API is public, CORS-enabled, and
// needs no key for read access, so the browser can read it directly.
(function () {
  'use strict';

  // The public repository that hosts the release artifacts.
  // CONFIRM / REPOINT AT LAUNCH if the public source repo is published elsewhere.
  var REPO = 'gringoboggy/yhwh-bible-platform';
  var API = 'https://api.github.com/repos/' + REPO + '/releases';

  function fmtDate(iso) {
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        year: 'numeric', month: 'long', day: 'numeric',
      });
    } catch (e) { return ''; }
  }

  function labelFor(name) {
    var n = (name || '').toLowerCase();
    if (/\.exe$/.test(n)) return 'Windows installer (' + name + ')';
    if (/\.dmg$/.test(n)) return 'macOS (' + name + ')';
    if (/\.appimage$/.test(n)) return 'Linux x86_64 (' + name + ')';
    if (/sha256|checksum/.test(n)) return 'Checksums (' + name + ')';
    return name;
  }

  function platformOf(name) {
    var n = (name || '').toLowerCase();
    if (/\.exe$/.test(n)) return 'win';
    if (/\.dmg$/.test(n)) return 'mac';
    if (/\.appimage$/.test(n)) return 'linux';
    return null;
  }

  function mkLink(href, text, cls) {
    var a = document.createElement('a');
    a.className = cls || 'btn-platform';
    a.href = href;
    a.rel = 'noopener';
    a.setAttribute('download', '');
    a.textContent = text;
    return a;
  }

  fetch(API, { headers: { accept: 'application/vnd.github+json' } })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (list) {
      // Private repo, no releases yet, or rate-limited -> keep the static fallback.
      if (!Array.isArray(list) || !list.length) return;

      var rel = null;
      for (var i = 0; i < list.length; i++) {
        if (!list[i].draft) { rel = list[i]; break; } // newest non-draft (incl. prereleases)
      }
      if (!rel) return;

      var version = rel.tag_name || rel.name || '';
      var name = document.getElementById('latest-name');
      var meta = document.getElementById('latest-meta');
      var links = document.getElementById('latest-links');

      if (name) name.textContent = 'YHWH Ya’ Way ' + version + (rel.prerelease ? ' (beta)' : '');
      if (meta) meta.textContent = rel.published_at ? 'Released ' + fmtDate(rel.published_at) : '';

      var assets = (rel.assets || []).filter(function (a) { return a && a.browser_download_url; });

      if (links && assets.length) {
        links.innerHTML = '';
        assets.forEach(function (a) {
          links.appendChild(mkLink(a.browser_download_url, labelFor(a.name)));
          links.appendChild(document.createTextNode(' '));
        });
        var notes = mkLink(rel.html_url, 'All files & release notes', 'btn-ghost');
        notes.removeAttribute('download'); // it's a page, not a file
        links.appendChild(notes);
      }

      // Turn the pending platform buttons into real download links where an asset matches.
      var pending = document.querySelectorAll('.platforms .btn-platform.is-pending');
      if (pending.length && assets.length) {
        var byPlat = {};
        assets.forEach(function (a) {
          var p = platformOf(a.name);
          if (p && !byPlat[p]) byPlat[p] = a;
        });
        Array.prototype.forEach.call(pending, function (span) {
          var t = (span.textContent || '').toLowerCase();
          var p = t.indexOf('windows') >= 0 ? 'win'
            : t.indexOf('macos') >= 0 ? 'mac'
            : t.indexOf('linux') >= 0 ? 'linux' : null;
          var a = p && byPlat[p];
          if (!a) return;
          span.parentNode.replaceChild(mkLink(a.browser_download_url, span.textContent), span);
        });
      }
    })
    .catch(function () { /* offline / blocked / rate-limited -> keep the static fallback */ });
})();
