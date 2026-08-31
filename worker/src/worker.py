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
    return await sync_from_feed(db, author_id)


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
        f'<li><a href="/essays/{_esc(r["slug"])}/">{_esc(r["title"])}</a>'
        + (f"<p>{_esc(r.get('excerpt') or '')}</p>" if r.get("excerpt") else "")
        + "</li>"
        for r in rows
        if r.get("slug")
    )
    return f"<h1>Archive</h1><ul>{items}</ul>"


# Catch-all: hand anything that is not an API route to Workers Static Assets,
# server-rendering content into the shell for the two routes where an empty
# root would otherwise hide everything from non-JS crawlers.
# `run_worker_first` is true in wrangler.jsonc so the Worker sees every request
# and the /api routes above win.
@app.get("/{path:path}")
async def static_assets(path: str, request: Request):
    # NB: don't shadow the module-level `env` import — _db() falls back to it.
    request_env = request.scope.get("env") or env
    resp = await request_env.ASSETS.fetch(f"https://assets.local/{path}")
    body = await resp.bytes()

    clean = path.strip("/")
    is_essay = clean.startswith("essays/") and clean.count("/") == 1
    is_archive = clean == "archive"

    if resp.status == 200 and (is_essay or is_archive):
        try:
            html = body.decode("utf-8")
            if _ROOT_DIV in html:
                db = request_env.DB
                markup = (
                    await _ssr_essay(db, clean.split("/", 1)[1])
                    if is_essay
                    else await _ssr_archive(db)
                )
                if markup:
                    return Response(
                        content=_inject(html, markup).encode("utf-8"),
                        status_code=200,
                        headers=resp.headers,
                    )
        except Exception as exc:  # noqa: BLE001
            # SSR is an enhancement: a D1 hiccup must serve the SPA shell, not
            # a 500. The page still works for JS clients.
            print(f"SSR failed for /{clean}: {type(exc).__name__}: {exc}")

    return Response(content=body, status_code=resp.status, headers=resp.headers)


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
