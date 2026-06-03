// website/giscus/lazy.js — load the Giscus comment widget only when the visitor
// scrolls to it, and only when it has been configured. This keeps the disclosure
// ("loads nothing from another service until you scroll to it") literally true:
// nothing from giscus.app loads on page view.
//
// It reads its settings from the data-* attributes on the .giscus container, which
// are filled in at launch from the giscus.app configurator.
(function () {
  var box = document.querySelector('.giscus');
  if (!box) return;

  // Not configured yet (pre-launch): leave the friendly fallback note in place.
  if (!box.getAttribute('data-repo') || !box.getAttribute('data-repo-id')) return;

  function load() {
    if (box.dataset.loaded) return;
    box.dataset.loaded = '1';

    var pending = box.querySelector('.giscus-pending');
    if (pending) pending.remove();

    var s = document.createElement('script');
    s.src = 'https://giscus.app/client.js';
    s.async = true;
    s.setAttribute('data-repo', box.getAttribute('data-repo'));
    s.setAttribute('data-repo-id', box.getAttribute('data-repo-id'));
    s.setAttribute('data-category', box.getAttribute('data-category') || 'Feedback');
    s.setAttribute('data-category-id', box.getAttribute('data-category-id'));
    s.setAttribute('data-mapping', box.getAttribute('data-mapping') || 'specific');
    s.setAttribute('data-term', box.getAttribute('data-term') || 'Website feedback');
    s.setAttribute('data-strict', '1');
    s.setAttribute('data-reactions-enabled', '0');
    s.setAttribute('data-emit-metadata', '0');
    s.setAttribute('data-input-position', 'top');
    s.setAttribute('data-theme', box.getAttribute('data-theme') || 'preferred_color_scheme');
    s.setAttribute('data-lang', 'en');
    box.appendChild(s);
  }

  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) { load(); io.disconnect(); }
    }, { rootMargin: '200px' });
    io.observe(box);
  } else {
    load(); // very old browser: just load it
  }
})();
