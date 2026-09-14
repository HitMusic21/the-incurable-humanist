# Remaining SEO setup — three items that need your credentials

Everything else from the remediation is shipped and verified. These three need
access I don't have, so they're written out precisely rather than half-done.

Ordered by value, not effort.

---

## 1. Google Search Console API — highest value

**Why it matters.** This is the audit's largest remaining blind spot. Right now I
can tell you what crawlers *receive* but not what Google has actually *indexed*
or what earns clicks. After changing 83 URLs, that's the difference between
"the markup is correct" and "it worked."

**Already done:** site ownership is verified — `frontend/index.html:28` carries
the `google-site-verification` meta tag, and there's a matching DNS TXT record.
You do **not** need to re-verify. Only programmatic access is missing.

**Current state** (`claude-seo run google_auth.py --check`): Tier 0 — API key
works (PageSpeed, CrUX), but Search Console, Indexing API and GA4 are all
unauthenticated.

### Steps

1. **Google Cloud Console** → create or pick a project.
2. **APIs & Services → Library** → enable **Google Search Console API**
   (and **Google Analytics Data API** if you want GA4 traffic too).
3. **APIs & Services → Credentials → Create credentials → Service account.**
   Name it anything; no project role is required.
4. On the new service account → **Keys → Add key → Create new key → JSON**.
   Save it somewhere private, e.g. `~/.config/claude-seo/gsc-service-account.json`.
   Do **not** commit it.
5. Copy the service account's email (looks like
   `name@project-id.iam.gserviceaccount.com`).
6. **Search Console** → property `theincurablehumanist.com` → **Settings →
   Users and permissions → Add user** → paste that email → permission
   **Full** (Restricted also works for read-only reporting).
7. Point the tooling at the key. The config file already exists with `api_key`
   and `default_property`; add one field:

   ```jsonc
   // ~/.config/claude-seo/google-api.json
   {
     "api_key": "<existing — leave as is>",
     "default_property": "<existing — leave as is>",
     "service_account_path": "/Users/carlosmescalona/.config/claude-seo/gsc-service-account.json"
   }
   ```

8. Verify: `claude-seo run google_auth.py --check` should move off Tier 0 and
   show Search Console as `[OK]`.

Then I can pull indexation status, impressions/clicks per URL, and confirm
whether the SSR work moved anything.

---

## 2. HSTS — modest value, hard to undo

Cloudflare dashboard → **SSL/TLS → Edge Certificates** → the **Enable HSTS**
button (directly below the "Always Use HTTPS" toggle you already turned on).

**Use these settings — not the defaults:**

| Field | Value | Why |
|---|---|---|
| Enable HSTS | On | |
| Max-Age | **1 day** | Not 6 months. Browsers cache this and it cannot be revoked early; at 1 day a mistake self-heals overnight. Raise it once proven. |
| Apply to subdomains | **OFF** | You have no mail subdomains today (Titan uses its own `titan.email` hosts), but if one is ever added under this zone, a cached policy would force HTTPS on it with no quick undo. |
| Preload | **OFF** | Preload lists are genuinely hard to exit. Only consider after months at a long max-age. |
| No-Sniff header | Either | The Worker already sends `X-Content-Type-Options: nosniff`. |

Cloudflare shows a warning dialog; its prerequisites are all satisfied — HTTPS
works, DNS is proxied, and nothing redirects HTTPS→HTTP.

**Honest framing:** Always Use HTTPS (already live) redirects everyone to HTTPS.
HSTS closes a narrower gap — a downgrade attack on a repeat visitor's first
request. For a publication with no logins or payments, it's real but modest.
The re-audit scored it High; I'd call it Medium. Worth doing, not urgent.

---

## 3. Promote CSP from Report-Only to enforcing — **wait first**

The policy is live as `Content-Security-Policy-Report-Only`, which by
construction cannot break anything. Promoting it means renaming one header key
in `worker/src/worker.py` (`_SECURITY_HEADERS`).

**Do not promote yet.** The marketing tags are consent-gated — they only load
after a visitor opts in — so a page load *without* consent exercises none of
them and would "prove" a policy that breaks the moment someone accepts.

### Before promoting

1. Visit `/`, `/about`, `/listen`, an essay, and `/archive` in a browser.
2. **Accept the cookie banner** on each. This is the step that matters.
3. Open DevTools → Console and look for
   `[Report Only] Refused to load …` messages.
4. Only if there are none across a week of normal use, rename the header:

   ```python
   # worker/src/worker.py
   _SECURITY_HEADERS["Content-Security-Policy"] = _CSP   # was ...-Report-Only
   ```

`worker/tests/test_routing.py` asserts the header is still Report-Only, so
promoting it deliberately turns a test red — change that test in the same
commit. Rollback is one line.

The origins in the policy were read out of the source, not guessed: Google
Fonts, PostHog, GA4, Meta, TikTok, and `open.spotify.com` for the `/listen`
embed.

---

## Also outstanding (no credentials needed, just decisions)

- **Essay subheadings** — 7 `<h2>` and 0 `<h3>` across 73 essays. The top
  remaining citability lever. Proposals for the 10 longest essays are drafted
  for Denise's review (see the review file referenced in the session notes);
  nothing is applied without her approval, since it means putting words in her
  byline.
- **WebP/AVIF images** — blocked on the Cloudflare Free plan (Polish is Pro+).
  Alternative is converting the 185 files in `/essay-images/` at build time,
  typically 25-50% smaller. A real task, not a toggle.
- **Re-measure CLS** — the cover-image fix is verified structurally (the
  unsized, shifting element is gone) but not by a fresh Lighthouse run; the
  PageSpeed Insights daily quota was exhausted. Re-run on an essay page and
  confirm CLS is under 0.1.
