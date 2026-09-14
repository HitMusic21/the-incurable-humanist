"""The four route lists must agree.

Adding a page means registering it in four independent places:

    frontend/src/main.tsx              the React route
    frontend/scripts/prerender.mjs     STATIC_PAGES  -> <title>, meta, JSON-LD
    frontend/scripts/generate-sitemap.mjs STATIC_ROUTES -> sitemap.xml
    worker/src/worker.py               _STATIC_SSR / _render_markup -> SSR

Nothing enforced that before this file. `generate-sitemap.mjs` says "Keep in
sync with src/main.tsx" in a comment, and worker.py notes that these lists "had
already drifted apart once" — both true, neither checked. A page could land in
three of the four and the only symptom would be a missing <title> or an absent
sitemap entry, discovered weeks later in a crawl report.

These are deliberately text scans rather than imports: the .mjs files pull in
Vite-aliased modules that bare pytest cannot resolve, and worker.py needs the
Pyodide runtime.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_MAIN_TSX = _ROOT / "frontend" / "src" / "main.tsx"
_PRERENDER = _ROOT / "frontend" / "scripts" / "prerender.mjs"
_SITEMAP = _ROOT / "frontend" / "scripts" / "generate-sitemap.mjs"
_SITE_TS = _ROOT / "frontend" / "src" / "config" / "site.ts"

# Public, indexable marketing pages. Everything outside this set is excluded on
# purpose:
#   /subscribed, /links  prerendered but noindex and absent from the sitemap
#   /essays/:slug, /speak/:topic  dynamic, generated per row
#   /admin/*             deliberately unreachable (no auth API on the Worker)
_PUBLIC_PAGES = {"/", "/about", "/archive", "/speak", "/listen", "/press", "/privacy"}


def _sitemap_paths() -> set[str]:
    block = _SITEMAP.read_text(encoding="utf-8").split("STATIC_ROUTES = [")[1].split("];")[0]
    return set(re.findall(r'path:\s*"([^"]+)"', block))


def _prerender_paths() -> set[str]:
    block = _PRERENDER.read_text(encoding="utf-8").split("STATIC_PAGES = [")[1].split("\n];")[0]
    return set(re.findall(r'path:\s*"([^"]+)"', block))


def _nav_paths() -> set[str]:
    block = _SITE_TS.read_text(encoding="utf-8").split("nav: [")[1].split("],")[0]
    return set(re.findall(r'to:\s*"([^"]+)"', block))


def test_every_public_page_is_in_the_sitemap():
    missing = _PUBLIC_PAGES - _sitemap_paths()
    assert not missing, f"absent from sitemap.xml, so never crawled: {sorted(missing)}"


def test_every_public_page_is_prerendered():
    """Without an entry a page inherits the shell's generic homepage <title>."""
    # "/" is prerendered from the Vite shell itself and is present in
    # STATIC_PAGES; the rest must be too.
    missing = _PUBLIC_PAGES - _prerender_paths()
    assert not missing, f"no per-page title/meta/JSON-LD: {sorted(missing)}"


def test_every_nav_target_is_a_real_page():
    """A nav item pointing at an unregistered path is a visible dead link."""
    unknown = _nav_paths() - _PUBLIC_PAGES
    assert not unknown, f"nav links to pages that are not registered: {sorted(unknown)}"


def test_nav_targets_are_routed_in_main_tsx():
    routes = _MAIN_TSX.read_text(encoding="utf-8")
    for path in sorted(_nav_paths()):
        if path == "/":
            assert "index: true" in routes, "no index route for /"
            continue
        assert f'path: "{path.lstrip("/")}"' in routes, f"{path} has no route in main.tsx"


@pytest.mark.parametrize("path", sorted(_PUBLIC_PAGES - {"/privacy"}))
def test_public_pages_are_not_noindexed(path):
    """Only the transactional pages carry noindex; marketing pages must not."""
    block = _PRERENDER.read_text(encoding="utf-8").split("STATIC_PAGES = [")[1].split("\n];")[0]
    entry = re.search(
        r'\{[^}]*path:\s*"' + re.escape(path) + r'"[^}]*\}', block, re.S
    )
    assert entry, f"{path} missing from STATIC_PAGES"
    assert "noindex" not in entry.group(0), f"{path} is noindexed but is a public page"


def test_press_is_registered_everywhere():
    """The Aug 2026 addition — the case this file was written for."""
    assert "/press" in _sitemap_paths(), "missing from sitemap"
    assert "/press" in _prerender_paths(), "missing from prerender"
    assert "/press" in _nav_paths(), "missing from nav"
    assert 'path: "press"' in _MAIN_TSX.read_text(encoding="utf-8"), "no React route"


def test_both_spotify_playlists_are_mirrored_into_the_worker_ssr():
    """SITE.spotifyPlaylists and the Worker's /listen SSR must name the same IDs.

    The embeds are client-only (consent-gated), so the SSR block is the only
    thing a non-JS crawler can read — and it repeats the IDs by hand, because
    site.ts is TypeScript the Worker cannot import. Denise added the Autumn
    playlist alongside the original in Sep 2026; adding a third to site.ts and
    forgetting the Worker would silently hide it from every AI crawler.
    """
    worker_py = (_ROOT / "worker" / "src" / "worker.py").read_text(encoding="utf-8")
    site_ts = _SITE_TS.read_text(encoding="utf-8")

    block = re.search(r"spotifyPlaylists:\s*\[(.*?)\]", site_ts, re.S)
    assert block, "spotifyPlaylists array not found in site.ts"
    ids = re.findall(r'id:\s*"([^"]+)"', block.group(1))
    assert len(ids) >= 2, f"expected both playlists in site.ts, found {ids}"

    for playlist_id in ids:
        assert playlist_id in worker_py, (
            f"playlist {playlist_id} is in site.ts but missing from the Worker's "
            "/listen SSR — non-JS crawlers would never see it"
        )
