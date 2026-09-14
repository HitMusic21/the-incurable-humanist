"""The Incurable Humanist API — FastAPI on Cloudflare Python Workers.

Replaces the Cloud Run FastAPI + Postgres backend. Two structural differences
from `backend/app`:

  1. **No ORM.** D1 is queried through the `env.DB` binding with prepared
     statements, so the SQLModel layer is replaced by explicit SQL. Column
     names and the shapes returned to the frontend are unchanged — see
     `frontend/src/config/api.ts`, which mirrors them by hand.
  2. **No `/api` prefix here.** In production nginx used to strip it; on
     Workers the frontend and API share one origin, so the routes are declared
     with the `/api` prefix directly and static assets fall through to ASSETS.

Datetimes are stored as ISO-8601 TEXT (SQLite has no datetime type) and are
returned to the client unchanged, matching what the Postgres backend serialized.
"""

from fastapi import Body, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response
from workers import WorkerEntrypoint, asgi, env

import leads as leads_service
from substack_sync import sync_from_feed

app = FastAPI(title="TIH API")

# Columns the public list endpoint returns. Kept in sync with StoryPublic in
# frontend/src/config/api.ts — the frontend types are hand-mirrored, not generated.
_PUBLIC_COLS = (
    "id, title, slug, excerpt, meta_description, cover_image_url, canonical_url, "
    "source_url, read_time_minutes, status, published_at, updated_at"
)

# StoryDetail = StoryPublic + these.
_DETAIL_COLS = _PUBLIC_COLS + ", content, content_warning, view_count"


def _db(request: Request):
    """D1 binding.

    Prefer the per-request env (the documented FastAPI path) and fall back to
    the module-level `env` import, which is what the runtime exposes when the
    ASGI scope does not carry one.
    """
    scope_env = request.scope.get("env")
    return (scope_env or env).DB


def _to_py(value):
    """Materialize a JsProxy into plain Python, if it is one."""
    return value.to_py() if hasattr(value, "to_py") else value


async def _all(stmt) -> list[dict]:
    """Run a prepared statement and return plain dicts.

    D1 hands back a JS object across the FFI boundary. `.to_py()` converts the
    result list, but each row may still be a JsProxy / Map rather than a dict,
    so convert per row as well.
    """
    result = await stmt.all()
    rows = _to_py(result.results)
    out = []
    for row in rows:
        row = _to_py(row)
        out.append(dict(row) if not isinstance(row, dict) else row)
    return out


@app.get("/api/stories")
async def list_stories(
    request: Request,
    status: str | None = Query(default="published"),
    # Cap high (500) so the sitemap/RSS generators can pull the full corpus in
    # one request; UI clients still pass smaller limits.
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Public list. `status=all` returns every row; default is published only."""
    db = _db(request)
    filtered = bool(status) and status.lower() != "all"

    # NULLS LAST is Postgres syntax; SQLite sorts NULLs first on DESC, so order
    # by "published_at IS NULL" first to reproduce nullslast().
    order = " ORDER BY published_at IS NULL, published_at DESC, id DESC"

    if filtered:
        total_stmt = db.prepare("SELECT count(*) AS c FROM story WHERE status = ?").bind(status)
        rows_stmt = db.prepare(
            f"SELECT {_PUBLIC_COLS} FROM story WHERE status = ?{order} LIMIT ? OFFSET ?"
        ).bind(status, limit, offset)
    else:
        total_stmt = db.prepare("SELECT count(*) AS c FROM story")
        rows_stmt = db.prepare(
            f"SELECT {_PUBLIC_COLS} FROM story{order} LIMIT ? OFFSET ?"
        ).bind(limit, offset)

    total = (await _all(total_stmt))[0]["c"]
    return {"stories": await _all(rows_stmt), "total_count": total}


@app.get("/api/stories/{slug}")
async def get_story(request: Request, slug: str):
    """Public detail by slug. Only published rows are exposed here."""
    db = _db(request)
    rows = await _all(
        db.prepare(
            f"SELECT {_DETAIL_COLS} FROM story WHERE slug = ? AND status = 'published'"
        ).bind(slug)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Story not found")
    return rows[0]


@app.get("/api/health")
async def health(request: Request):
    """Liveness + D1 reachability. Reports the failure instead of a bare 500."""
    import traceback

    try:
        rows = await _all(_db(request).prepare("SELECT count(*) AS stories FROM story"))
        return {"status": "ok", "stories": rows[0]["stories"]}
    except Exception as exc:  # noqa: BLE001 - diagnostic endpoint
        return {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "trace": traceback.format_exc()[-800:],
        }


def _setting(request_env, name: str, default: str | None = None) -> str | None:
    """Read a var/secret.

    Wrangler vars and secrets live on the `env` binding object, NOT in
    os.environ — reading them from os.environ silently yields None, which made
    the correct SCHEDULER_TOKEN fail the equality check and 401 every request.
    """
    value = getattr(request_env or env, name, None)
    return default if value is None else str(value)


async def _resolve_author_id(db, request_env=None) -> int:
    """The user row essays are attributed to.

    Fails closed: without an author row the sync must not invent one, because
    every story carries author_id as a NOT NULL foreign key.
    """
    email = _setting(request_env, "AUTHOR_EMAIL", "denise@theincurablehumanist.com")
    rows = await _all(db.prepare("SELECT id FROM user WHERE email = ?").bind(email))
    if not rows:
        rows = await _all(db.prepare("SELECT id FROM user WHERE is_author = 1 LIMIT 1"))
    if not rows:
        raise RuntimeError(f"no author row for {email!r} — create one before syncing")
    return rows[0]["id"]


async def _run_sync(db, request_env=None) -> dict:
    author_id = await _resolve_author_id(db, request_env)
    # settings carries the env binding so the sync can read INDEXNOW_KEY.
    return await sync_from_feed(db, author_id, settings=request_env or env)


@app.post("/api/stories/sync")
async def sync_substack(
    request: Request,
    x_scheduler_token: str | None = Header(default=None, alias="X-Scheduler-Token"),
):
    """Manual trigger for the same sync the cron runs.

    Fails closed like the Cloud Run version: without a matching SCHEDULER_TOKEN
    this returns 401 and syncs nothing. The cron path does not come through
    here, so an unset token disables only the manual trigger.
    """
    request_env = request.scope.get("env") or env
    expected = _setting(request_env, "SCHEDULER_TOKEN")
    if not expected or x_scheduler_token != expected:
        raise HTTPException(status_code=401, detail="Invalid scheduler token")
    try:
        return await _run_sync(_db(request), request_env)
    except Exception as exc:  # noqa: BLE001 - upstream feed/network failure
        raise HTTPException(status_code=503, detail=f"Substack sync failed: {exc}") from exc


def _settings_dict(request_env) -> dict:
    """Collect the vars/secrets the lead flow needs off the env binding."""
    keys = (
        "SENDGRID_API_KEY", "SENDGRID_TPL_CONFIRM", "SENDGRID_FROM_EMAIL",
        "SENDGRID_FROM_NAME", "FRONTEND_URL",
    )
    out = {}
    for key in keys:
        value = _setting(request_env, key)
        if value is not None:
            out[key] = value
    return out


@app.post("/api/leads/subscribe", status_code=202)
async def subscribe(request: Request, payload: dict = Body(...)):
    """Newsletter signup.

    Rate limiting is NOT done here — the Cloud Run version used slowapi
    (10/hour per IP). On Workers that belongs in Cloudflare's own rate-limiting
    rules, which run before the Worker and cost nothing. Until such a rule is
    configured this endpoint is unthrottled; see the deployment notes.
    """
    request_env = request.scope.get("env") or env
    try:
        return await leads_service.subscribe(_db(request), _settings_dict(request_env), payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/leads/confirm")
async def confirm_lead(request: Request, token: str = Query(...)):
    """Double opt-in click-through. Redirects to the frontend either way."""
    request_env = request.scope.get("env") or env
    base = (_setting(request_env, "FRONTEND_URL") or "https://theincurablehumanist.com").rstrip("/")
    ok = await leads_service.confirm(_db(request), token)
    # /subscribed is a real route in main.tsx; an invalid token lands on the
    # home page rather than a dead end.
    return RedirectResponse(url=f"{base}/subscribed" if ok else f"{base}/", status_code=302)


@app.post("/api/leads/unsubscribe")
async def unsubscribe_lead(request: Request, payload: dict = Body(...)):
    return await leads_service.unsubscribe(_db(request), payload.get("email", ""))


def _esc(text: str) -> str:
    """Escape text for HTML. Used for titles/excerpts, never for story.content —
    that is already allowlist-sanitized on ingest (see html_sanitize.py) and
    escaping it would render tags as literal text."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# The prerendered shell ships an empty React root. SSR replaces it with real
# markup so non-JS clients get content; React then hydrates over the top.
_ROOT_DIV = '<div id="root"></div>'


def _inject(html: str, markup: str) -> str:
    """Put server-rendered markup inside the React root element.

    React replaces the root's children on mount, so this content is transitional
    for real browsers but is the ENTIRE page for GPTBot/ClaudeBot/PerplexityBot,
    which do not execute JS.
    """
    if _ROOT_DIV not in html:
        return html
    return html.replace(_ROOT_DIV, f'<div id="root">{markup}</div>', 1)


async def _ssr_essay(db, slug: str) -> str | None:
    """Server-rendered essay body, or None when the slug is unknown."""
    rows = await _all(
        db.prepare(
            "SELECT title, content, excerpt, published_at, read_time_minutes "
            "FROM story WHERE slug = ? AND status = 'published'"
        ).bind(slug)
    )
    if not rows:
        return None
    row = rows[0]
    meta = []
    if row.get("published_at"):
        meta.append(_esc(str(row["published_at"])[:10]))
    if row.get("read_time_minutes"):
        meta.append(f"{row['read_time_minutes']} min read")
    return (
        f"<article><h1>{_esc(row['title'])}</h1>"
        + (f"<p>{' · '.join(meta)}</p>" if meta else "")
        + (f"<p>{_esc(row.get('excerpt') or '')}</p>" if row.get("excerpt") else "")
        # Not escaped: sanitized at ingest. Escaping would show raw tags.
        + f"<div>{row.get('content') or ''}</div></article>"
    )


async def _ssr_archive(db) -> str:
    """Server-rendered essay index.

    Without this, raw /archive HTML has zero links to /essays/*, so a crawler
    that does not run JS can only reach essays via sitemap.xml.
    """
    rows = await _all(
        db.prepare(
            "SELECT title, slug, excerpt FROM story WHERE status = 'published' "
            "ORDER BY published_at IS NULL, published_at DESC, id DESC LIMIT 100"
        )
    )
    items = "".join(
        # No trailing slash: sitemap.xml and the canonical tag both use the
        # bare form, and both variants resolve 200, so a slash here would make
        # every crawled archive link a duplicate of the canonical URL.
        f'<li><a href="/essays/{_esc(r["slug"])}">{_esc(r["title"])}</a>'
        + (f"<p>{_esc(r.get('excerpt') or '')}</p>" if r.get("excerpt") else "")
        + "</li>"
        for r in rows
        if r.get("slug")
    )
    # "Writing" matches the nav label and the React page's own <h1>. The URL
    # stays /archive — only the label changed.
    return f"<h1>Writing</h1><ul>{items}</ul>"


# About-page prose, mirrored from frontend/src/pages/About.tsx (hardcoded JSX
# that Python cannot import). Deliberately short and factual: this is what a
# non-JS crawler reads, so it must not contradict the Person node's
# `description` in schemaNodes.mjs. Update both together.
_ABOUT_MARKUP = (
    "<h1>About — Denise Rodriguez Dao</h1>"
    "<p>Welcome to the curious world of <em>The Incurable Humanist</em>, a space "
    "to explore grief, migration, and art — and what gets inherited anyway.</p>"
    "<p>Having lived in Caracas, Mexico City, and now based in New York City, "
    "Denise Rodriguez Dao writes about memory, migration, and the lives behind "
    "the statistics. She is a writer and business immigration consultant working "
    "with artists, collectors, entrepreneurs, and leaders across art and "
    "entertainment.</p>"
    '<p><a href="/archive">Read the writing</a> · '
    '<a href="/speak">Speaking topics and booking</a></p>'
)

# Marketing routes whose server-rendered body needs no D1 query.
# Before these existed, every one of these routes shipped a 29-byte body:
# Googlebot renders JS so it eventually saw them, but GPTBot, ClaudeBot and
# PerplexityBot do not, so /about and the speaking pages were literally blank
# to every AI answer engine.
_STATIC_SSR = {
    # Tagline mirrors SITE.heroTagline, not SITE.positioning: Denise dropped
    # "— and what gets inherited anyway" from visible copy while keeping it in
    # meta descriptions and JSON-LD. The nav strip mirrors SITE.nav.
    "": (
        "<h1>The Incurable Humanist</h1>"
        "<p>By Denise Rodriguez Dao. Weekly essays on grief, migration, and art.</p>"
        '<p><a href="/about">About</a> · <a href="/archive">Writing</a> · '
        '<a href="/speak">Speaking</a> · <a href="/listen">Listening</a> · '
        '<a href="/press">Press</a></p>'
    ),
    "about": _ABOUT_MARKUP,
    # Mirrors frontend/src/pages/Listen.tsx. The Spotify embed itself is
    # consent-gated and client-only by design (see SpotifyPlaylist.tsx), so the
    # server-rendered version describes what is there and links out rather than
    # pretending to embed a player.
    "listen": (
        "<h1>Listening</h1>"
        "<h2>Audio essays</h2>"
        "<p>Every essay is also available in audio, read by Denise — whether "
        "you prefer to read or listen.</p>"
        '<p><a href="https://theincurablehumanist.substack.com">'
        "Listen on Substack</a></p>"
        "<h2>Playlists</h2>"
        "<p>A curated playlist tied to the essays — the music that runs "
        "alongside the writing.</p>"
        '<p><a href="/archive">Read the essays instead</a></p>'
    ),
    # The privacy policy is mirrored in full rather than summarised. A crawler
    # or an AI system checking how this site handles data should be able to read
    # the actual commitments, not a one-line teaser — and a policy page is a
    # trust signal precisely because it is specific. Keep this in step with
    # frontend/src/pages/Privacy.tsx, which is itself tied to what
    # src/lib/analytics.ts actually does.
    "privacy": (
        "<h1>Privacy</h1>"
        "<p>This site is a personal publication. It collects as little as "
        "possible, and nothing at all until you say yes.</p>"
        "<h2>Analytics and cookies</h2>"
        "<p>Nothing is tracked until you accept the banner. If you decline, or "
        "simply ignore it, no analytics or marketing scripts are loaded and the "
        "site works exactly the same.</p>"
        "<p>If you accept, this site uses PostHog for product analytics (which "
        "pages are read, which links are followed) and loads Google Analytics 4, "
        "the Meta Pixel, and the TikTok Pixel. Those three are advertising tools "
        "and are only ever injected after consent — they are not present in the "
        "page otherwise.</p>"
        "<p>Your choice is stored in your browser's local storage under the key "
        "tih_consent_v1 and expires after twelve months, at which point you will "
        "be asked again.</p>"
        "<h2>The newsletter</h2>"
        "<p>If you subscribe, your email address is stored so the newsletter can "
        "be sent to you, and the referring page and any campaign parameters in "
        "the link you arrived from are recorded so it is possible to know which "
        "writing brought people here. Delivery is handled by SendGrid. Every "
        "email includes an unsubscribe link, and unsubscribing is honoured "
        "immediately.</p>"
        "<h2>What is never done</h2>"
        "<p>Your data is not sold and it is not shared with anyone beyond the "
        "services named above, each of which is used only to run this site. "
        "There is no advertising network buying this list.</p>"
        "<h2>Changing your mind</h2>"
        "<p>To withdraw consent, clear this site's data in your browser settings "
        "and the banner will appear again on your next visit. To be removed from "
        "the newsletter, use the unsubscribe link in any email. For anything "
        'else — including a request to delete data already held — write to '
        '<a href="mailto:hello@theincurablehumanist.com">'
        "hello@theincurablehumanist.com</a>.</p>"
    ),
}


async def _topics(request_env) -> list[dict]:
    """Speaking topics, read from the build-time JSON in public/.

    Emitted by scripts/generate-sitemap.mjs from src/data/speakingTopics.mjs,
    which that file's header names as the single source of truth. Reading it
    through the ASSETS binding avoids keeping a fourth, Python, copy of the
    topic list that would silently drift when a topic is added.
    """
    import json

    resp = await request_env.ASSETS.fetch("https://assets.local/speaking-topics.json")
    if resp.status != 200:
        return []
    return json.loads((await resp.bytes()).decode("utf-8"))


async def _ssr_topic(request_env, slug: str) -> str | None:
    """Server-rendered /speak/<slug> body."""
    topic = next((t for t in await _topics(request_env) if t.get("slug") == slug), None)
    if not topic:
        return None
    return (
        f"<h1>{_esc(topic['title'])}</h1>"
        + (f"<p>{_esc(topic.get('subtitle') or '')}</p>" if topic.get("subtitle") else "")
        + (f"<p>{_esc(topic.get('blurb') or '')}</p>" if topic.get("blurb") else "")
        + (
            f"<p>Best fit for: {_esc(topic['audience'])}</p>"
            if topic.get("audience")
            else ""
        )
        + '<p><a href="/speak">All speaking topics</a> · '
        '<a href="/about">About Denise Rodriguez Dao</a></p>'
    )


async def _ssr_speak(request_env) -> str | None:
    """Server-rendered /speak index, linking to every topic landing page."""
    topics = await _topics(request_env)
    if not topics:
        return None
    items = "".join(
        f'<li><a href="/speak/{_esc(t["slug"])}">{_esc(t["title"])}</a>'
        + (f"<p>{_esc(t.get('subtitle') or '')}</p>" if t.get("subtitle") else "")
        + "</li>"
        for t in topics
        if t.get("slug")
    )
    return (
        "<h1>Speaking</h1>"
        "<p>Denise Rodriguez Dao speaks on grief, migration, art, and the Latin "
        "American diaspora.</p>"
        f"<ul>{items}</ul>"
    )


async def _ssr_press(request_env) -> str | None:
    """Server-rendered /press body.

    Reads press.json, emitted at build time by scripts/generate-sitemap.mjs from
    src/data/press.mjs — the same ASSETS-binding pattern as _topics(), and for
    the same reason: site.ts is TypeScript this Worker cannot import, and a
    Python copy of the outlet list would drift the moment one is added.
    """
    import json

    resp = await request_env.ASSETS.fetch("https://assets.local/press.json")
    if resp.status != 200:
        return None
    items = json.loads((await resp.bytes()).decode("utf-8"))
    if not items:
        return None
    entries = "".join(
        f"<li><h2>{_esc(i.get('outlet') or '')}</h2>"
        + f'<p><a href="{_esc(i.get("href") or "")}">{_esc(i.get("title") or "")}</a></p>'
        + (f"<p>{_esc(i.get('dek') or '')}</p>" if i.get("dek") else "")
        + "</li>"
        for i in items
        if i.get("href")
    )
    return (
        "<h1>Press</h1>"
        "<p>Writing and conversations about Denise Rodriguez Dao's work in Latin "
        "American art, migration, and cultural advocacy.</p>"
        f"<ul>{entries}</ul>"
    )


async def _render_markup(request_env, clean: str) -> str | None:
    """Server-rendered body for `clean`, or None when the route has no SSR.

    Table-driven rather than a chain of is_* booleans: the SSR list, the
    prerender page list and the router had already drifted apart once, and a
    single dispatch point makes the next addition obvious.
    """
    if clean.startswith("essays/") and clean.count("/") == 1:
        return await _ssr_essay(request_env.DB, clean.split("/", 1)[1])
    if clean == "archive":
        return await _ssr_archive(request_env.DB)
    if clean == "speak":
        return await _ssr_speak(request_env)
    if clean == "press":
        return await _ssr_press(request_env)
    if clean.startswith("speak/") and clean.count("/") == 1:
        return await _ssr_topic(request_env, clean.split("/", 1)[1])
    return _STATIC_SSR.get(clean)


# ---------------------------------------------------------------------------
# Routing tables for the catch-all.
# ---------------------------------------------------------------------------

# Retired routes. These exist in main.tsx only as client-side <Navigate replace>,
# which can never run: before this table existed the Worker 404'd with a 0-byte
# body, so React Router never booted. A server-issued 301 also passes link
# equity, which a 200 shell + a client-side hop does not — crawlers score the
# 200 page, not the JS redirect.
_REDIRECTS = {
    "newsletter": "/",
    "contact": "/speak",
    "essays": "/archive",
}
# "press" deliberately absent. It used to redirect to /archive, where the press
# cards lived; Aug 2026 it became a real page again. This table is consulted
# BEFORE ASSETS.fetch(), so leaving the entry here would 301 away from the page
# and no amount of prerendering would make it reachable.

# Static-file extensions. A 404 on one of these is a REAL 404 and must stay one.
# Serving index.html as text/html for a missing .js white-screens the site while
# reporting 200 to every uptime monitor — the worst possible failure mode.
_ASSET_EXTS = (
    ".js", ".mjs", ".css", ".map", ".json", ".xml", ".txt", ".webmanifest",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".avif", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pdf", ".mp3", ".mp4", ".webm", ".zip",
)

# Admin is intentionally excluded from the SPA fallback. The auth API
# (/auth/login, /stories/id/{id}, admin CRUD) was left behind in backend/app
# during the Workers migration — POST /api/auth/login returns 405, not 404,
# because only this GET catch-all matches it. Serving the shell here would
# render a login form that cannot log in, which is worse than an honest 404.
# Essays arrive via the hourly Substack sync, so admin CRUD is currently
# redundant. Remove this once the auth endpoints exist on the Worker.
_NO_FALLBACK_PREFIXES = ("admin",)

# Applied to every asset/HTML response. Set here rather than via
# BaseHTTPMiddleware: that middleware wraps each response in an anyio task
# group — real per-request cost on Pyodide for what is a dict update — and it
# would also wrap /api/*, where different headers are wanted. Everything we
# need to harden already funnels through _finish().
#
# Strict-Transport-Security is deliberately ABSENT: it is set at the Cloudflare
# zone (SSL/TLS -> Edge Certificates -> HSTS) so it also covers responses this
# Worker never produces. Setting it in both places invites drift.
# Content-Security-Policy is staged separately (Report-Only first) because it
# can white-screen the site.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

# Content-Security-Policy, shipped REPORT-ONLY first.
#
# Report-Only cannot break anything by construction: the browser evaluates the
# policy and reports violations without enforcing it. That matters here because
# the marketing tags are consent-gated — they only load after the visitor opts
# in, so an un-consented page load exercises none of them and would "prove" a
# policy that breaks on first consent. Promote to Content-Security-Policy only
# after watching reports from a consented session on /, /about, /listen, an
# essay and /archive.
#
# Origins below were read out of the source, not guessed:
#   fonts.googleapis.com / fonts.gstatic.com  index.html stylesheet + font files
#   us.i.posthog.com                          VITE_PUBLIC_POSTHOG_HOST
#   www.googletagmanager.com                  analytics.ts GA4 loader
#   connect.facebook.net / www.facebook.com   analytics.ts Meta pixel + beacon
#   analytics.tiktok.com                      analytics.ts TikTok (inactive
#                                             today — the ID is still the
#                                             placeholder — but listed so
#                                             enabling it needs no CSP change)
#   open.spotify.com                          SpotifyPlaylist.tsx iframe; omit
#                                             it and /listen breaks
#
# 'unsafe-inline' is unavoidable in style-src (React inline styles + Tailwind)
# and needed in script-src for now, because analytics.ts builds the Meta and
# TikTok pixel bootstraps as inline scripts. Tightening script-src is a
# follow-up, after the policy is enforcing and stable.
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com "
    "https://connect.facebook.net https://analytics.tiktok.com "
    "https://us.i.posthog.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: https://www.google-analytics.com "
    "https://www.facebook.com https://analytics.tiktok.com; "
    "connect-src 'self' https://us.i.posthog.com "
    "https://www.google-analytics.com https://analytics.tiktok.com "
    "https://connect.facebook.net; "
    "frame-src https://open.spotify.com; "
    "base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
    "object-src 'none'"
)
_SECURITY_HEADERS["Content-Security-Policy-Report-Only"] = _CSP

# Content-hashed filenames: Vite hashes /assets, rehost_essay_images.py sha1s
# /essay-images. The URL changes when the bytes change, so the response can
# never go stale and `immutable` lets the browser skip revalidation entirely.
_IMMUTABLE_PREFIXES = ("assets/", "essay-images/")

# HTML must revalidate: index.html is the SPA shell and the prerendered
# per-route shells carry meta that changes on every build. If HTML ever got
# `immutable`, a deploy would be invisible to returning visitors for a year.
_HTML_CACHE = "public, max-age=0, must-revalidate"


def _looks_like_asset(clean: str) -> bool:
    """True when the path names a file rather than a client route.

    Checked against the LAST segment only. Slugs can never contain a dot —
    slugify() strips everything outside [a-z0-9\\s-] — so an essay URL is never
    mistaken for a file.
    """
    return clean.rsplit("/", 1)[-1].lower().endswith(_ASSET_EXTS)


def _redirect_target(clean: str) -> str | None:
    """Permanent destination for a retired path, or None to keep routing."""
    if clean in _REDIRECTS:
        return _REDIRECTS[clean]
    # /archive/<slug> is the legacy essay alias kept for old inbound links.
    # Canonical is /essays/<slug>, with no trailing slash to match sitemap.xml.
    if clean.startswith("archive/") and clean.count("/") == 1:
        slug = clean.split("/", 1)[1]
        if slug:
            return f"/essays/{slug}"
    return None


def _finish(body: bytes, status: int, upstream_headers, clean: str) -> Response:
    """Build the outgoing Response with corrected caching + security headers.

    `upstream_headers` comes from ASSETS.fetch(). The Workers SDK exposes it as
    an http.client.HTTPMessage-backed mapping, so dict() is enough — but copy it
    rather than mutating in place, since Starlette re-encodes every value.
    """
    # Lower-case every key on the way in. The upstream mapping is
    # case-insensitive but preserves the wire casing ("Cache-Control"), so
    # writing a differently-cased key alongside it emits the header TWICE —
    # observed as "public, max-age=0, must-revalidate, public, max-age=0,
    # must-revalidate". Normalising first makes assignment a real overwrite.
    try:
        headers = {str(k).lower(): str(v) for k, v in dict(upstream_headers).items()}
    except Exception:  # noqa: BLE001 - header shape is runtime-dependent
        headers = {}

    # Starlette recomputes content-length from the (SSR-grown) body. Carrying
    # the upstream value truncates the response.
    headers.pop("content-length", None)

    if clean.startswith(_IMMUTABLE_PREFIXES):
        headers["cache-control"] = "public, max-age=31536000, immutable"
    elif headers.get("content-type", "").startswith("text/html") or not clean:
        headers["cache-control"] = _HTML_CACHE

    # The asset server sends a bare "text/html" with no charset. Browsers fall
    # back to the document's <meta charset>, but the HTTP header takes
    # precedence for consumers that read it — and essays carry accented names
    # ("Andrés Bello"), em-dashes and curly quotes that garble if a client
    # guesses the encoding. Declare it explicitly.
    content_type = headers.get("content-type", "")
    if content_type.startswith("text/html") and "charset=" not in content_type.lower():
        headers["content-type"] = f"{content_type}; charset=utf-8"

    for key, value in _SECURITY_HEADERS.items():
        headers[key.lower()] = value
    return Response(content=body, status_code=status, headers=headers)


@app.get("/api/sync-health")
async def sync_health(request: Request):
    """How stale is the corpus?

    Exists because the Substack sync went quiet for two weeks in Sep 2026 and
    nobody noticed: two essays sat in the feed while the site served 73. The
    sync itself was fine — a manual trigger created both immediately — so the
    failure was invisible precisely because nothing errored. Silence looked
    identical to "nothing to do".

    `stale` is advisory, not an error. Denise publishes weekly, so no write for
    more than ~10 days means either a genuinely quiet stretch or a sync that has
    stopped running; either is worth a look. Cheap enough to poll from an uptime
    monitor.

    Declared ABOVE the catch-all deliberately — FastAPI matches in declaration
    order, and /{path:path} swallows anything registered after it.
    """
    rows = await _all(
        _db(request).prepare(
            "SELECT COUNT(*) AS total, MAX(published_at) AS newest, "
            "MAX(updated_at) AS last_write FROM story WHERE status = 'published'"
        )
    )
    row = rows[0] if rows else {}
    last = str(row.get("last_write") or "")
    stale, days = True, None
    if last:
        from datetime import datetime, timezone

        try:
            parsed = datetime.fromisoformat(last.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            days = (datetime.now(timezone.utc) - parsed).days
            stale = days > 10
        except Exception:  # noqa: BLE001 - a malformed date is itself a problem
            pass
    return {
        "total": row.get("total"),
        "newest_published": row.get("newest"),
        "last_write": last or None,
        "days_since_write": days,
        "stale": stale,
    }


# Catch-all: hand anything that is not an API route to Workers Static Assets,
# server-rendering content into the shell for the two routes where an empty
# root would otherwise hide everything from non-JS crawlers.
# `run_worker_first` is true in wrangler.jsonc so the Worker sees every request
# and the /api routes above win.
#
# HEAD is served alongside GET because a GET-only decorator made every HEAD
# request 405 sitewide, which breaks link checkers and uptime monitors.
@app.api_route("/{path:path}", methods=["GET", "HEAD"])
async def static_assets(path: str, request: Request):
    # NB: don't shadow the module-level `env` import — _db() falls back to it.
    request_env = request.scope.get("env") or env
    clean = path.strip("/")

    # 1. Retired routes, before touching ASSETS: /essays (retired) and
    #    /essays/<slug> (real) share a prefix, as do /archive and
    #    /archive/<slug>. Deciding here turns a pattern race into a lookup.
    target = _redirect_target(clean)
    if target is not None:
        return RedirectResponse(url=target, status_code=301)

    resp = await request_env.ASSETS.fetch(f"https://assets.local/{path}")
    body = await resp.bytes()

    # Only HTML routes can carry SSR. Gating on the path (rather than trying to
    # decode every response) keeps images and the JS bundle off the decode path.
    if resp.status == 200 and not _looks_like_asset(clean):
        try:
            html = body.decode("utf-8")
            if _ROOT_DIV in html:
                markup = await _render_markup(request_env, clean)
                if markup:
                    return _finish(
                        _inject(html, markup).encode("utf-8"), 200, resp.headers, clean
                    )
        except UnicodeDecodeError:
            pass  # binary asset; nothing to inject
        except Exception as exc:  # noqa: BLE001
            # SSR is an enhancement: a D1 hiccup must serve the SPA shell, not
            # a 500. The page still works for JS clients.
            print(f"SSR failed for /{clean}: {type(exc).__name__}: {exc}")

    # 2. SPA fallback — nginx's `try_files $uri $uri/ /index.html`, reinstated.
    #    Required in code because run_worker_first:true means wrangler's
    #    not_found_handling never fires: this Worker owns the request and calls
    #    ASSETS.fetch() itself.
    #
    #    Returns 200, not 404: /subscribed (where every confirmed double-opt-in
    #    lands) and /links are real routes, indistinguishable from a typo at
    #    this layer. NotFound.tsx carries noindex so genuine typos are not
    #    indexed as soft-404s.
    if (
        resp.status == 404
        and not _looks_like_asset(clean)
        and not clean.startswith(_NO_FALLBACK_PREFIXES)
    ):
        shell = await request_env.ASSETS.fetch("https://assets.local/index.html")
        if shell.status == 200:
            return _finish(await shell.bytes(), 200, shell.headers, clean)

    return _finish(body, resp.status, resp.headers, clean)


_asgi_entrypoint = asgi.entrypoint(app)


class Default(_asgi_entrypoint):
    """ASGI entrypoint plus the hourly Cron Trigger.

    Cron replaces Cloud Scheduler's hourly POST to /stories/sync. It calls the
    same code path as the HTTP route, but skips the token check — Cloudflare
    invokes `scheduled()` directly, so there is no request to authenticate.
    """

    async def scheduled(self, controller, env, ctx):
        try:
            result = await _run_sync(env.DB, env)
            print(f"substack sync: {result}")
        except Exception as exc:  # noqa: BLE001 - never let cron raise unhandled
            print(f"substack sync FAILED: {type(exc).__name__}: {exc}")
