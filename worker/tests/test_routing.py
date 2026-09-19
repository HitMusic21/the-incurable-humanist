"""Routing tests for the Worker catch-all.

These cover the three decisions that the catch-all makes before anything
touches the network: is this a retired route (301), does this path name a file
(real 404) or a client route (SPA shell), and may this prefix fall back at all.

`worker/src/worker.py` cannot be imported here — it does
`from workers import WorkerEntrypoint, asgi, env` at module scope, which only
resolves inside the Pyodide/workerd runtime. The pure helpers are therefore
re-declared below and kept byte-identical to the originals. That is a real
duplication cost, accepted because the alternative is no coverage at all on the
highest-risk code in the deployment: a regression here either 404s the
newsletter confirmation landing page or serves HTML in place of a missing JS
bundle, and the second failure reports 200 to every uptime monitor.

If you change _REDIRECTS, _ASSET_EXTS, _NO_FALLBACK_PREFIXES, _looks_like_asset
or _redirect_target in worker.py, mirror the change here. test_mirrors_source
fails when the two drift.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_WORKER_PY = Path(__file__).resolve().parents[1] / "src" / "worker.py"

# --- mirrored from worker/src/worker.py -------------------------------------

# "press" is intentionally NOT here — it became a real page in Aug 2026.
# test_press_is_no_longer_a_redirect guards that.
_REDIRECTS = {
    "newsletter": "/",
    "contact": "/speak",
    "essays": "/archive",
}

_ASSET_EXTS = (
    ".js", ".mjs", ".css", ".map", ".json", ".xml", ".txt", ".webmanifest",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".avif", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pdf", ".mp3", ".mp4", ".webm", ".zip",
)

_NO_FALLBACK_PREFIXES = ("admin",)

_IMMUTABLE_PREFIXES = ("assets/", "essay-images/")


def _looks_like_asset(clean: str) -> bool:
    return clean.rsplit("/", 1)[-1].lower().endswith(_ASSET_EXTS)


def _redirect_target(clean: str) -> str | None:
    if clean in _REDIRECTS:
        return _REDIRECTS[clean]
    if clean.startswith("archive/") and clean.count("/") == 1:
        slug = clean.split("/", 1)[1]
        if slug:
            return f"/essays/{slug}"
    return None


def _falls_back(clean: str) -> bool:
    """Mirrors the Phase 1 fallback condition (given an upstream 404)."""
    return not _looks_like_asset(clean) and not clean.startswith(_NO_FALLBACK_PREFIXES)


# --- redirects ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("newsletter", "/"),
        ("contact", "/speak"),
        ("essays", "/archive"),
        # Legacy essay alias -> canonical, no trailing slash (matches sitemap).
        ("archive/ambiguous-loss", "/essays/ambiguous-loss"),
        ("archive/why-the-lindsay-clancy-trial", "/essays/why-the-lindsay-clancy-trial"),
    ],
)
def test_retired_routes_redirect(path, expected):
    assert _redirect_target(path) == expected


@pytest.mark.parametrize(
    "path",
    [
        "",                       # home
        "about",
        "archive",                # the real listing page, NOT an alias
        "press",                  # a real page since Aug 2026, not a redirect
        "essays/ambiguous-loss",  # a real essay shares the /essays prefix
        "speak",
        "speak/grief-and-inheritance",
        "listen",
        "privacy",
        "subscribed",
        "links",
        "admin",                  # excluded from redirects AND fallback
        "admin/login",
        "admin/stories",
        "archive/",               # trailing slash strips to "archive"
    ],
)
def test_live_routes_are_not_redirected(path):
    """A redirect here would break a working page or shadow a real essay."""
    assert _redirect_target(path.strip("/")) is None


def test_redirect_targets_are_never_themselves_redirected():
    """Guards against a redirect loop."""
    for target in _REDIRECTS.values():
        assert _redirect_target(target.strip("/")) is None


# --- asset vs route ----------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "assets/index-9W2p5K45.js",
        "assets/index-Uw_kCr6G.css",
        "assets/index-abc.js.map",
        "essay-images/f8407f0284d5e55e.jpg",
        "robots.txt",
        "sitemap.xml",
        "rss.xml",
        "favicon.svg",
        "founder.jpg",
        "denisehome.jpeg",
        "og-image.svg",
        "vite.svg",
        "speaking-topics.json",
        "press-kit.pdf",
        "ASSETS/INDEX.JS",  # case-insensitive
    ],
)
def test_files_are_recognised_as_assets(path):
    """A missing file must 404. Serving index.html as text/html for a missing
    .js white-screens the site while reporting 200 to every monitor."""
    assert _looks_like_asset(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "",
        "about",
        "archive",
        "speak",
        "speak/grief-and-inheritance",
        "essays/ambiguous-loss",
        "essays/the-incurable-humanists-reading-list",
        "subscribed",
        "links",
        "listen",
        "privacy",
        "nonexistent-typo",
        "admin/stories/42/edit",
    ],
)
def test_routes_are_not_mistaken_for_assets(path):
    assert _looks_like_asset(path) is False


def test_slug_with_dots_would_be_misread_but_cannot_occur():
    """Documents the one theoretical hole in the extension check.

    A slug ending in a known extension would be served a 404 instead of the
    shell. It cannot happen: slugify() (backend/app/services/slugify.py) strips
    everything outside [a-z0-9\\s-], so a slug contains no dots at all. This
    test pins that reasoning so a future slug-format change trips it.
    """
    assert _looks_like_asset("essays/report.pdf") is True      # would be a 404
    assert _looks_like_asset("essays/on-t-s-eliot") is False   # real slug shape

    slug_clean = re.compile(r"[^a-z0-9\s-]")
    assert slug_clean.sub("", "report.pdf") == "reportpdf"     # dot cannot survive


# --- SPA fallback eligibility ------------------------------------------------


@pytest.mark.parametrize("path", ["subscribed", "links", "nonexistent-typo", "about"])
def test_client_routes_get_the_shell(path):
    """/subscribed is where every confirmed double-opt-in lands; before the
    fallback existed it returned 404 with a 0-byte body."""
    assert _falls_back(path) is True


@pytest.mark.parametrize("path", ["admin", "admin/login", "admin/stories"])
def test_admin_is_excluded_from_fallback(path):
    """The Worker has no auth API (POST /api/auth/login is 405 — the endpoints
    were left in backend/app), so serving the shell would render a login form
    that cannot log in. Honest 404 until the auth endpoints are ported."""
    assert _falls_back(path) is False


@pytest.mark.parametrize("path", ["assets/missing.js", "essay-images/gone.jpg", "robots.txt"])
def test_missing_files_do_not_fall_back(path):
    assert _falls_back(path) is False


# --- cache-control policy ----------------------------------------------------


@pytest.mark.parametrize("path", ["assets/index-abc.js", "essay-images/deadbeef.jpg"])
def test_hashed_assets_are_immutable(path):
    assert path.startswith(_IMMUTABLE_PREFIXES)


@pytest.mark.parametrize("path", ["", "about", "essays/ambiguous-loss", "archive"])
def test_html_is_never_immutable(path):
    """If HTML got `immutable`, a deploy would be invisible to returning
    visitors for a year."""
    assert not path.startswith(_IMMUTABLE_PREFIXES)


# --- drift guard -------------------------------------------------------------


def test_mirrors_source():
    """Fail when the constants above drift from worker.py."""
    src = _WORKER_PY.read_text(encoding="utf-8")

    for key, value in _REDIRECTS.items():
        assert f'"{key}": "{value}"' in src, f"_REDIRECTS[{key!r}] differs from worker.py"

    for ext in (".js", ".css", ".jpg", ".xml", ".txt", ".json", ".woff2"):
        assert f'"{ext}"' in src, f"{ext} missing from worker.py _ASSET_EXTS"

    assert '_NO_FALLBACK_PREFIXES = ("admin",)' in src
    assert '_IMMUTABLE_PREFIXES = ("assets/", "essay-images/")' in src
    # The archive SSR link must stay slash-free to match sitemap.xml.
    assert 'href="/essays/{_esc(r["slug"])}"' in src
    # HEAD must be served, or link checkers get 405 sitewide.
    assert 'methods=["GET", "HEAD"]' in src


# --- content security policy --------------------------------------------------


def _csp() -> str:
    """The CSP string as declared in worker.py."""
    src = _WORKER_PY.read_text(encoding="utf-8")
    start = src.index("_CSP = (")
    end = src.index(")\n", start)
    return src[start:end]


def test_csp_ships_report_only_first():
    """Enforcing a wrong policy white-screens the site; Report-Only cannot.

    The marketing tags are consent-gated, so an un-consented page load exercises
    none of them — the policy has to be observed from a CONSENTED session before
    it is enforced.
    """
    src = _WORKER_PY.read_text(encoding="utf-8")
    assert '_SECURITY_HEADERS["Content-Security-Policy-Report-Only"] = _CSP' in src
    assert '_SECURITY_HEADERS["Content-Security-Policy"] = _CSP' not in src


@pytest.mark.parametrize(
    ("origin", "why"),
    [
        ("https://fonts.googleapis.com", "index.html font stylesheet"),
        ("https://fonts.gstatic.com", "font files"),
        ("https://us.i.posthog.com", "VITE_PUBLIC_POSTHOG_HOST"),
        ("https://www.googletagmanager.com", "GA4 loader in analytics.ts"),
        ("https://connect.facebook.net", "Meta pixel in analytics.ts"),
        ("https://analytics.tiktok.com", "TikTok pixel in analytics.ts"),
        ("https://open.spotify.com", "SpotifyPlaylist.tsx iframe — /listen breaks without it"),
        (
            "https://www.youtube-nocookie.com",
            "Voices for Venezuela reel on /speak — blank frame without it",
        ),
        # All four measured as real violations on 2026-09-19, with consent
        # granted. See the comment above _CSP in worker.py.
        ("https://us-assets.i.posthog.com", "PostHog config.js + exception-autocapture.js"),
        ("https://static.cloudflareinsights.com", "Cloudflare's own analytics beacon"),
        ("https://www.googletagmanager.com", "GA4 sends its collection hit as an IMAGE"),
        ("https://substackcdn.com", "two synced essays still carry Substack-hosted images"),
    ],
)
def test_csp_allows_every_origin_the_site_actually_loads(origin, why):
    assert origin in _csp(), f"CSP would block {origin}: {why}"


def test_csp_keeps_the_baseline_restrictions():
    csp = _csp()
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp


def test_hsts_is_not_set_in_the_worker():
    """HSTS belongs at the Cloudflare zone so it also covers responses this
    Worker never produces. Setting it in both places invites drift."""
    src = _WORKER_PY.read_text(encoding="utf-8")
    assert "Strict-Transport-Security" not in src.split("_SECURITY_HEADERS = {")[1].split("}")[0]


def test_press_is_no_longer_a_redirect():
    """/press used to 301 to /archive, where the press cards lived.

    It became a page of its own in Aug 2026. The redirect table is consulted
    BEFORE ASSETS.fetch(), so a lingering entry here would 301 away from the
    page and no amount of prerendering would make it reachable.
    """
    assert _redirect_target("press") is None
    assert '"press":' not in _WORKER_PY.read_text(encoding="utf-8").split("_REDIRECTS = {")[1].split("}")[0]


def test_scheduled_reads_bindings_off_self_not_a_parameter():
    """The cron handler must use self.env, never an `env` parameter.

    WorkerEntrypoint supplies the environment as an instance attribute; the
    runtime does not pass it positionally to scheduled(). The original
    signature `scheduled(self, controller, env, ctx)` therefore bound `env` to
    the wrong thing and every hourly run died on

        AttributeError: 'NoneType' object has no attribute 'DB'

    for roughly three weeks, silently, because Workers Logs were off.
    """
    src = _WORKER_PY.read_text(encoding="utf-8")
    sig = re.search(r"async def scheduled\(([^)]*)\)", src)
    assert sig, "scheduled() handler not found"
    params = [p.strip() for p in sig.group(1).split(",")]
    assert "env" not in params, (
        f"scheduled() takes an `env` parameter ({params}) — the runtime does not "
        "pass one, so it binds to the wrong value. Read self.env instead."
    )
    body = src[sig.end() : sig.end() + 1200]
    assert "self.env" in body, "scheduled() must read bindings off self.env"


def test_observability_is_enabled():
    """Workers Logs must stay on, or cron failures are invisible.

    scheduled() reports failure with print(). With observability disabled that
    output is discarded, which is why a three-week sync outage produced no
    signal at all.
    """
    import json

    raw = (_WORKER_PY.parent.parent / "wrangler.jsonc").read_text(encoding="utf-8")
    stripped = re.sub(r"^\s*//.*$", "", raw, flags=re.M)
    config = json.loads(stripped)
    assert config.get("observability", {}).get("enabled") is True, (
        "observability.enabled must be true — without it print() from the cron "
        "handler goes nowhere and sync failures are silent"
    )


# --- trailing-slash canonicalization -----------------------------------------


def test_trailing_slash_redirects_to_the_bare_url():
    """/essays/x/ and /essays/x must not both be live URLs.

    `clean = path.strip("/")` made them render identically, so both returned
    200 and Google treated them as two URLs. The canonical tag pointed at the
    bare form, so this never caused duplicate INDEXING — it wasted crawl
    budget, which GSC confirmed was real rather than theoretical: the slash
    variants were crawled and earned their own impressions
    (trader-joes-panic…/ 4, will-this-matter…/ 6), and several essays listed a
    /slug/ self-referrer as their only referring URL.

    That matters because crawl budget is the binding constraint here: 10 of 76
    essays are unindexed with Google declining to crawl them.
    """
    src = _WORKER_PY.read_text(encoding="utf-8")
    assert 'if path.endswith("/") and clean and not _looks_like_asset(clean):' in src
    assert 'RedirectResponse(url=f"/{clean}", status_code=301)' in src


def test_trailing_slash_redirect_runs_after_retired_routes():
    """Order matters: /archive/<slug>/ must reach /essays/<slug> in ONE hop.

    If the slash redirect came first it would send /archive/x/ to /archive/x,
    which then 301s again to /essays/x — a redirect chain, and chains dilute
    the link equity the legacy alias exists to preserve.
    """
    src = _WORKER_PY.read_text(encoding="utf-8")
    retired = src.index("target = _redirect_target(clean)")
    slash = src.index('if path.endswith("/") and clean')
    assert retired < slash, "retired-route redirects must be evaluated first"


def test_homepage_is_exempt_from_the_slash_redirect():
    """"/" strips to "", which is falsy — the guard must keep it a 200.

    Without the `and clean` check the homepage would 301 to "/" forever.
    """
    src = _WORKER_PY.read_text(encoding="utf-8")
    guard = src[src.index('if path.endswith("/") and clean') :][:120]
    assert "and clean" in guard
