# Architecture — the system as deployed

**Last verified:** 20 September 2026, against production.
**Supersedes:** the stack described in the body of `CLAUDE.md`, which documents
the retired Cloud Run deployment.

---

## The shape of it

```
                    theincurablehumanist.com
                              │
                    Cloudflare Worker  (worker/src/worker.py)
                    run_worker_first: true — sees EVERY request
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   /api/* routes        SSR injection        Static Assets
   FastAPI on Pyodide   into prerendered     worker/public/
        │               HTML shell           (89 pages)
     D1 (SQLite)
     tih-db, 76 essays
```

One Worker is the whole origin: API, server-rendering, static assets, redirects
and the hourly Substack sync. There is no separate backend service.

---

## Load-bearing decisions

Each of these was derived from a production failure. They look arbitrary and
are not.

### 1. The cron handler must read `self.env`

```python
async def scheduled(self, controller, *args):   # correct
    env_binding = self.env
```

`WorkerEntrypoint` supplies the environment as an **instance attribute**. The
runtime does not pass it positionally. The original signature
`scheduled(self, controller, env, ctx)` bound `env` to the wrong value and every
hourly run died on its first line with
`AttributeError: 'NoneType' object has no attribute 'DB'` — silently, for
roughly three weeks. Guarded by `test_scheduled_reads_bindings_off_self_not_a_parameter`.

### 2. `observability.enabled` must stay `true`

The cron reports failure with `print()`. With observability off that output is
discarded, which is *why* the three-week outage produced no signal. Guarded by
`test_observability_is_enabled`.

### 3. `not_found_handling` must stay UNSET in `wrangler.jsonc`

Setting `single-page-application` makes `ASSETS.fetch()` return 200 + index.html
for everything, so the Worker's `resp.status == 404` branch never runs. Verified:
`/assets/nope.js` returned **200 text/html** (a white screen that reports 200 to
uptime monitors) and `/admin` bypassed its exclusion. The SPA fallback lives in
`worker.py`'s catch-all.

### 4. Route declaration order is load-bearing

FastAPI matches in declaration order and `/{path:path}` swallows anything after
it. `/api/sync-health` once returned the SPA shell because it was declared below
the catch-all.

### 5. The trailing-slash redirect must come AFTER the retired-route check

`/archive/<slug>/` has to reach `/essays/<slug>` in **one** hop. If the slash
redirect ran first it would produce a chain, diluting the link equity the legacy
alias exists to preserve. Guarded by
`test_trailing_slash_redirect_runs_after_retired_routes`.

### 6. The sync must batch its D1 lookups

`upsert_entry` used to issue one `SELECT ... WHERE source_url = ?` per feed
entry — 20 sequential round-trips. With a 417KB feed to parse and 20 bodies to
sanitize, that exceeded the 2,000ms scheduled-invocation CPU limit and Cloudflare
killed the run with `exceededCpu`. `load_existing()` now reads the corpus once.
Guarded by `worker/tests/test_sync_batching.py` (6 tests).

### 7. `content_hash` covers text, not markup

`content_hash(plain_text(html))`. RSS emits a bare `<img>`; the JSON API emits
`<picture>` + `srcset` for identical prose. Hashing markup would make the two
sources disagree permanently and rewrite every row every hour.

---

## The four-place page registration

Adding a page means touching **four** independent lists, or it silently
half-exists:

| Place | What it controls |
|---|---|
| `frontend/src/main.tsx` | the React route |
| `frontend/scripts/prerender.mjs` | `<title>`, meta, JSON-LD |
| `frontend/scripts/generate-sitemap.mjs` | sitemap.xml |
| `worker/src/worker.py` | `_STATIC_SSR` / `_render_markup` |

`worker/tests/test_route_lists_agree.py` fails when they drift.

---

## Build pipeline

```bash
cd frontend && API_URL=https://theincurablehumanist.com/api npm run build
```

Runs in order — **the order matters**:

1. `tsc -b && vite build`
2. `generate-sitemap.mjs` → sitemap.xml (87 URLs), rss.xml, speaking-topics.json, press.json
3. `generate-related.mjs` → **related-essays.json** (148 links across 64/76 essays)
4. `prerender.mjs` → 89 pages (9 static + 4 topics + 76 essays)

Then stage and deploy:

```bash
rm -rf worker/public && cp -r frontend/dist worker/public
cd worker && uv run pywrangler deploy
```

**The sitemap is a build artifact.** A new essay synced into D1 is live and
linked but *absent from sitemap.xml* until the next build — which is exactly how
the Sep 15 essay stayed "unknown to Google" while being served correctly.

---

## Components added Sep 2026

| Component | Why it exists |
|---|---|
| `ConsentFacade.tsx` | Click-to-load gate for third-party embeds. Extracted from `SpotifyPlaylist` when the `/speak` YouTube reel needed identical behaviour; two copies would drift. |
| `SocialIconRow.tsx` | Footer and Home each inlined the same icon list, so every network cost two hand-pasted SVG paths. Now keyed off `SITE.socials` and **typed so adding a network without an icon fails the build**. |
| `RelatedEssays.tsx` | Zero of 76 essays linked to any other essay. Renders nothing when an essay has no sufficiently related sibling — a weak recommendation is worse than none. |

**`SITE.spotifyPlaylists` is a LIST.** Denise added the Autumn playlist
*alongside* the original, not in place of it. Titles are the real Spotify names,
read from the oEmbed endpoint.

---

## Substack sync

Hourly cron (`0 * * * *`) → `scheduled()` → `_run_sync()` → `sync_from_feed()`.

- Idempotency key is `source_url` (UNIQUE). `canonical_url` stays NULL so the
  on-site page is canonical.
- Every run records to the **`sync_run`** table. `/api/sync-health` exposes
  `last_run`, which is the field to monitor: `stale` asks "is the content old?"
  and takes ten days to turn red; `last_run.ok` asks "is the pipeline working?"
  and turns red within the hour.
- **Bind `""`, not `None`**, for nullable text columns — a Python `None` through
  the D1 FFI throws, and the surrounding `except` swallows it.
- Substack **rate-limits aggressively**. `limit` above ~25 returns 400, as does
  `offset`. Several apparent parameter errors during development were rate
  limiting; space calls out.

---

## SEO invariants

- **`max-image-preview:large`** on every indexable page. Required for Google
  Discover, which is image-led — without it Google may show only a thumbnail,
  which in practice means no placement. Set in *both* `SEO.tsx` and
  `prerender.mjs`. Guarded by `SEO.test.tsx`.
- **Trailing-slash URLs 301 to the bare form.** Both once returned 200, so
  Google saw two URLs per page and spent crawl budget on duplicates.
- **Canonical is always self-referential** on essays; Google confirms it picks
  our URL over Substack's on all indexed essays.
- SSR carries the **full essay text**, so AI crawlers (GPTBot, ClaudeBot,
  PerplexityBot) read it without executing JS. Verified: identical content to
  Googlebot, no cloaking.

---

## Known constraints

| Constraint | Detail |
|---|---|
| **Scheduled CPU limit** | ~2,000ms. The sync fits only because lookups are batched. |
| **Cron throttling** | After repeated `exceededCpu` kills Cloudflare stops invoking the schedule. Check `last_run` in `/api/sync-health`; a redeploy re-registers triggers. |
| **Cover images** | 33 of 76 are under Discover's 1200px minimum. Fixable only upstream in Substack. |
| **`/speak/:topic` orphaned** | The "Signature topics" grid was their only in-site link. Still prerendered, in the sitemap and server-rendered — reachable by URL and search only. |
| **Admin 404s by design** | No auth API on the Worker; serving the shell would render a login form that cannot log in. |

---

## Testing

```bash
cd frontend && npx vitest run                          # 55 tests
cd worker   && uv run pytest tests/                    # 119 tests
cd frontend && node scripts/verify-ia-changes.mjs https://theincurablehumanist.com
                                                       # 94 browser assertions
```

The Playwright suite takes the base URL as a **positional argument** and honours
`BASE`. It previously ignored `BASE` and silently fell back to localhost, so a
run that looked like it tested production tested a local worker instead.
