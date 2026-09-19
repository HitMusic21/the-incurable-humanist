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

### Status as of 2026-09-19 — steps 1-6 are DONE, one permission is missing

Re-checked from the CLI today. What already exists:

| Thing | State |
|---|---|
| GCP project `savvy-ceiling-474522-r8` | exists |
| `searchconsole.googleapis.com` | **enabled** |
| `indexing.googleapis.com` | **enabled** |
| Service account `tih-gsc-reader@savvy-ceiling-474522-r8.iam.gserviceaccount.com` | **exists**, added to the GSC property with Full permission |
| Site ownership verification | done (meta tag + DNS TXT) |

So the setup is 90% complete. Two things block the last step, and **both need
someone other than `admin@hitmusic21.com`**:

1. **No key file, and no permission to create one.** An org policy blocks
   service-account key creation (that is why this stalled originally).
2. **No permission to impersonate the service account instead.** Impersonation
   is the modern, keyless alternative — but it needs
   `roles/iam.serviceAccountTokenCreator`, and granting it requires
   `iam.serviceAccounts.setIamPolicy`, which `admin@hitmusic21.com` does not
   have. Verified today:

   ```
   ERROR: permission: iam.serviceAccounts.setIamPolicy
   reason: IAM_PERMISSION_DENIED
   ```

**The project owner is `edgarvaldez@hitmusic21.com`.** One of these unblocks it:

- **(preferred, keyless)** Ask them to run:
  ```bash
  gcloud iam service-accounts add-iam-policy-binding \
    tih-gsc-reader@savvy-ceiling-474522-r8.iam.gserviceaccount.com \
    --member="user:admin@hitmusic21.com" \
    --role="roles/iam.serviceAccountTokenCreator" \
    --project=savvy-ceiling-474522-r8
  ```
  Then no key file is ever created or stored on disk.

- **(alternative)** Ask them to grant `admin@hitmusic21.com`
  `roles/iam.serviceAccountAdmin` on that project, and to lift the
  key-creation org policy — then step 4 below works.

- **(simplest, no GCP at all)** For a one-off look, export the Performance
  report by hand: **Search Console → Performance → Export → CSV**, and drop the
  file in the repo. That answers "what is actually ranking" without any API.

Once unblocked, add the credential path:

```jsonc
// ~/.config/claude-seo/google-api.json
{
  "api_key": "<existing — leave as is>",
  "default_property": "<existing — leave as is>",
  "service_account_path": "/Users/carlosmescalona/.config/claude-seo/gsc-service-account.json"
}
```

Verify with `claude-seo run google_auth.py --check` — Search Console should
report `[OK]` instead of Tier 0.

**Why it is worth the chase.** Everything else about SEO here is verified
*output* — crawlers receive the full text, canonicals are right, 148 internal
links now exist. What is still unknown is the *outcome*: which essays earn
impressions, which rank, and whether Substack is outranking this site for
Denise's own work (see "Substack canonicals" below). That question cannot be
answered from the site itself.

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

**Re-verified 2026-09-19** (all three prerequisites still hold, still not set):

```
http://theincurablehumanist.com      -> 301 (redirects to HTTPS)
https://www.theincurablehumanist.com -> 200
subdomains (blog/mail/shop/app/staging) -> none resolve
Strict-Transport-Security header     -> absent
```

No subdomains exist, so "Apply to subdomains" is safe either way today — the
recommendation to leave it OFF is about future ones, not present risk. This
cannot be done from the CLI: the Wrangler OAuth token is scoped to Workers and
gets `9109 Unauthorized` on zone settings, so it needs the dashboard.

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

### Substack canonicals — the biggest single ranking factor left

**Verified 2026-09-19.** Every essay exists twice, and both copies claim to be
the original:

| | canonical tag says |
|---|---|
| `theincurablehumanist.com/essays/good-grief` | itself ✅ |
| `theincurablehumanist.substack.com/p/good-grief` | **itself** ⚠️ |

The text is the same — Substack serves ~3,091 visible chars of "Good Grief"
including the identical opening line; the on-site copy is 2,608 chars of body
prose. Checked five posts, all self-canonical on Substack.

Google picks one URL per duplicate. When a very high-authority domain claims
authorship of identical text, it usually wins — so Denise's essays may be
earning their search visibility under *Substack's* brand rather than her own
domain, and the on-site copies risk being filtered as duplicates.

Nothing in this repo can fix it. The site already does everything correctly on
its side: self-canonical, `index, follow`, full server-rendered text, complete
Article schema, 148 internal links, all 75 essays in the sitemap. The remaining
signal lives in Substack's own `<head>`.

**The fix, in Substack:** each post's settings has a canonical URL field. Set it
to `https://theincurablehumanist.com/essays/<slug>`. That tells Google the
on-site copy is the original and consolidates ranking signals onto Denise's
domain. Roughly a minute per post, and it can be set going forward on new ones.

**Caveat — this may be a deliberate choice.** Session notes record it as
previously "dropped by decision." Keeping Substack canonical is a legitimate
trade-off if subscriber growth on Substack matters more than domain authority.
The point is that it should be a *conscious* trade-off: it is the single
largest factor in whether theincurablehumanist.com ranks for Denise's own work.

### Everything else

- **Essay subheadings** — 7 `<h2>` and 0 `<h3>` across 73 essays. The top
  remaining citability lever. Proposals for the 10 longest essays are drafted
  for Denise's review (see the review file referenced in the session notes);
  nothing is applied without her approval, since it means putting words in her
  byline.
- **Newly synced essays keep Substack-hosted images** — found 2026-09-19.
  `backend/scripts/rehost_essay_images.py` is a **one-off**, not part of the
  hourly sync, so every essay that arrives after the last run keeps
  `substackcdn.com` image URLs. Currently 2 of 75 essays (both synced Sep 14:
  *The Ultimate New York Art Guide* and *Good Grief*), and the count grows by
  one per new essay.

  This re-creates exactly the dependency the rehosting migration removed: if
  Substack changes CDN rules or the account lapses, those essays lose their
  images — including the `og:image` used for social previews. It also surfaced
  as a CSP violation, which is why `substackcdn.com` is now in `img-src`.

  Two options: run the script periodically after syncs, or fold the rewrite
  into `substack_sync.py` so it happens on ingest. The second is the durable
  fix but needs care — the script deliberately does **not** recompute
  `content_hash` (it hashes text, not markup), and that invariant must hold or
  every sync would rewrite every row.

- **WebP/AVIF images** — blocked on the Cloudflare Free plan (Polish is Pro+).
  Alternative is converting the 185 files in `/essay-images/` at build time,
  typically 25-50% smaller. A real task, not a toggle.
- **Re-measure CLS** — the cover-image fix is verified structurally (the
  unsized, shifting element is gone) but not by a fresh Lighthouse run; the
  PageSpeed Insights daily quota was exhausted. Re-run on an essay page and
  confirm CLS is under 0.1.

---

## Cron scheduler suspended — check this first (2026-09-19)

**Symptom.** No scheduled invocation since 17:05 UTC, including the hourly
`0 * * * *`. The Worker itself is healthy: the site, the API and all 76 essays
return 200, and a manual sync completes in ~2s.

**Cause.** The scheduled handler was killed with `exceededCpu` (2,010ms) on
repeated runs, and Cloudflare stopped invoking it. Both underlying bugs are now
fixed and deployed:

1. `scheduled()` read `env` from a parameter the runtime never passes, so it
   died on its first line for weeks (commit c0c813c).
2. Once it actually ran, per-entry D1 lookups plus feed parsing exceeded the
   2,000ms scheduled-invocation CPU budget (commit 6e86502).

**How to check whether it recovered.** Poll the health endpoint; `last_run`
turns over once a cron executes:

```bash
curl -s https://theincurablehumanist.com/api/sync-health | python3 -m json.tool
```

`last_run.ran_at` newer than `2026-09-19T17:50:55Z` (the manual verification
run) means crons are firing again. `last_run.ok` is the field to monitor
generally — it reports pipeline health within an hour, whereas `stale` only
notices after ten days of no new content.

**If it has not recovered within a few hours**, a fresh `pywrangler deploy`
re-registers the triggers and is the documented nudge. Failing that, the
Cloudflare dashboard (Workers → tih-api → Settings → Triggers) shows the
schedule state directly.

**Manual sync in the meantime.** The HTTP endpoint runs the identical code and
has a far larger CPU budget:

```bash
curl -X POST https://theincurablehumanist.com/api/stories/sync \
  -H "X-Scheduler-Token: $SCHEDULER_TOKEN"
```

Note `SCHEDULER_TOKEN` was rotated on 2026-09-19 to run that verification; the
current value is in the Worker's secrets (`wrangler secret list` shows it
exists, not its value). Nothing else consumes this token.
