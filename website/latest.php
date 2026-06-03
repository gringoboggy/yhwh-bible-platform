<?php
/*
 * latest.php — tiny serverless "latest release" feed for YHWH Ya' Way.
 *
 * It asks GitHub for the newest release SERVER-SIDE and returns a small JSON
 * object. Because the fetch happens here on the server (not in the visitor's
 * browser), a visitor's IP is never sent to GitHub just to read a version
 * number — the site keeps its no-tracking promise. The answer is cached on
 * disk for 15 minutes so GitHub isn't hit on every page view.
 *
 * SETUP AT LAUNCH (two lines):
 *   1. set $REPO to the public repo that hosts the Releases, e.g. "gringoboggy/yhwh-app".
 *   2. create a file OUTSIDE public_html (e.g. ~/yhwh-gh-token.txt, chmod 600)
 *      containing a fine-grained, READ-ONLY, single-repo GitHub token, and point
 *      $TOKEN_FILE at it. (Read-only public-repo token = near-zero risk; it just
 *      lifts the anonymous rate limit.)
 *
 * Until $REPO is set, it returns {"ok":false} and the page keeps its static text.
 */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=900');

$REPO = '';                                  // e.g. 'gringoboggy/yhwh-app'  (empty = not live yet)
$TOKEN_FILE = __DIR__ . '/../yhwh-gh-token.txt';   // outside public_html; optional
$CACHE = sys_get_temp_dir() . '/yhwh_latest_release.json';
$CACHE_TTL = 900;                            // 15 minutes

function fail() { echo json_encode(['ok' => false]); exit; }

if ($REPO === '') { fail(); }

// Serve fresh cache if we have it.
if (is_file($CACHE) && (time() - filemtime($CACHE) < $CACHE_TTL)) {
    $cached = file_get_contents($CACHE);
    if ($cached !== false && $cached !== '') { echo $cached; exit; }
}

if (!function_exists('curl_init')) { fail(); }

$headers = ['User-Agent: yhwhyaway.com', 'Accept: application/vnd.github+json'];
if (is_file($TOKEN_FILE)) {
    $tok = trim((string)file_get_contents($TOKEN_FILE));
    if ($tok !== '') { $headers[] = 'Authorization: Bearer ' . $tok; }
}

$ch = curl_init('https://api.github.com/repos/' . $REPO . '/releases/latest');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => $headers,
    CURLOPT_TIMEOUT => 6,
    CURLOPT_FOLLOWLOCATION => false,
]);
$body = curl_exec($ch);
$code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($body === false || $code !== 200) {
    // GitHub down / rate-limited / no release: serve any stale cache, else fail.
    if (is_file($CACHE)) { echo file_get_contents($CACHE); exit; }
    fail();
}

$rel = json_decode($body, true);
if (!is_array($rel) || empty($rel['tag_name'])) { fail(); }

// Map release assets to friendly download buttons by an explicit suffix allowlist.
$want = [
    '.exe'      => 'Windows installer (.exe)',
    '.dmg'      => 'macOS (.dmg)',
    '.AppImage' => 'Linux (.AppImage)',
];
$assets = [];
foreach (($rel['assets'] ?? []) as $a) {
    $name = $a['name'] ?? '';
    foreach ($want as $suffix => $label) {
        if (substr($name, -strlen($suffix)) === $suffix) {
            $assets[] = ['label' => $label, 'url' => $a['browser_download_url'] ?? ''];
        }
    }
}

$out = json_encode([
    'ok'      => true,
    'version' => $rel['tag_name'],
    'date'    => isset($rel['published_at']) ? substr($rel['published_at'], 0, 10) : '',
    'url'     => $rel['html_url'] ?? '',
    'assets'  => $assets,
]);

@file_put_contents($CACHE, $out);   // best-effort cache; ignore failure
echo $out;
