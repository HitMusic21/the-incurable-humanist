# UTM registry

The canonical vocabulary for `utm_source`, `utm_medium`, `utm_campaign`, and
`utm_content` across every outbound link, ad, bio-link, and referral share
on The Incurable Humanist.

**Rule zero:** all UTM values are **lowercase**. GA4 treats `Instagram` and
`instagram` as separate sources — pick one, stick with it, don't fragment
attribution.

**Rule one:** enforced in code via `frontend/src/lib/utm.ts::withUTM()` (which
lowercases everything) and `captureIncomingUTMs()` (which logs a dev-console
warning when it sees an off-registry `utm_source` on inbound traffic).

---

## `utm_source`

Where the click originated. If it's not in this list, add it here **before**
using it in a real campaign.

| Source          | When to use                                                       |
|-----------------|-------------------------------------------------------------------|
| `website`       | On-site outbound (thank-you referrals, archive → Substack, etc.)  |
| `tiktok`        | Organic TikTok posts                                              |
| `instagram`     | Organic Instagram posts + stories                                 |
| `facebook`      | Organic Facebook posts                                            |
| `youtube`       | Organic YouTube description links + community tab                 |
| `linkedin`      | Organic LinkedIn posts                                            |
| `x`             | Organic X/Twitter posts                                           |
| `substack`      | Substack newsletter body links pointing back to the site          |
| `newsletter`    | Owned newsletter body links (SendGrid welcome + magnet emails)    |
| `email`         | One-off personal emails, press outreach                           |
| `press`         | Coverage in an outlet (link Denise sends to a journalist)         |
| `bio-link`      | The `/links` bio-page (also uses `?src=` for per-platform origin) |

To add: edit `KNOWN_SOURCES` in `frontend/src/lib/utm.ts` **and** the
`UtmSource` union type, then add a row here.

## `utm_medium`

The channel type. Smaller allowlist — resist expanding it.

| Medium            | When to use                                                       |
|-------------------|-------------------------------------------------------------------|
| `organic-social`  | Non-paid social posts                                             |
| `paid-social`     | Meta Ads, TikTok Ads, LinkedIn Ads                                |
| `email`           | Any email-body link                                               |
| `bio-link`        | The `/links` page (source is the specific platform)               |
| `referral`        | On-site thank-you referrals; reader-to-reader shares              |
| `cta`             | On-site call-to-action fallbacks (e.g. "open Substack" fallback)  |

## `utm_campaign`

Free-form-ish, but conventions:

- Use kebab-case: `reader-magnet`, `spring-2026-launch`, `venezuela-arc`
- One campaign = one theme or one calendar window, not a permanent bucket
- Keep it short (< 40 chars) — long values truncate in GA4 reports
- **Never** put PII, session IDs, or timestamps here

Active campaigns:

| Campaign             | Purpose                                                            |
|----------------------|--------------------------------------------------------------------|
| `reader-magnet`      | Post-confirmation referral share (subscribed thank-you page)       |
| `archive-best-of`    | Archive page → best-of essay outbound links                        |
| `archive-recent`     | Archive page → live Substack feed outbound links                   |
| `archive-feed-fallback` | Fallback link when Substack feed API is unreachable             |
| `site-cta-fallback`  | SubscribeCTA "Open Substack" fallback when our API fails           |
| `links-page`         | `/links` bio-page → all outbound links                             |

## `utm_content`

Which specific button/card/position was clicked. Kebab-case, granular but bounded.

- `home-hero`, `home-read-door` — Home page CTAs
- `about-footer`, `speak-secondary`, `speak-footer` — page-level positions
- `archive-primary`, `archive-after-best-of`, `archive-footer` — Archive positions
- `latest-essay`, `speak`, `listen`, `instagram`, `tiktok` — Links page cards
- `thank-you` — post-confirmation referral shares

## `utm_term`

Unused today. Reserve for keyword-level attribution if we ever run search ads.

---

## Dev-time enforcement

`captureIncomingUTMs()` runs on every page load (`main.tsx`) and reads the
current query string. If it sees a `utm_source` that isn't in `KNOWN_SOURCES`,
it logs `[utm] Unknown utm_source="…"` to the browser console in dev builds
only (prod stays silent — Denise's readers don't need to see it).

`withUTM()` doesn't validate — it just lowercases and appends. That's
deliberate: outbound links are authored in code, so any typo shows up in a PR
review; enforcement lives in the inbound direction where humans (Denise
writing an Instagram caption, a paid-social manager pasting a URL) can
actually get it wrong.

## When to update this doc

- Adding a new `utm_source`: update `KNOWN_SOURCES` in `utm.ts` **and** the
  `UtmSource` union type **and** the table above, in the same commit.
- Adding a new `utm_medium`: same three edits.
- Launching a new campaign: add a row under **Active campaigns** with a
  one-sentence purpose. Retire rows when the campaign ends.
