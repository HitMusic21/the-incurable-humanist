# PostHog dashboards

Three funnels + one retention view to build in the PostHog UI. All events are
consent-gated at the client (see `frontend/src/lib/analytics.ts`) so counts
only start populating once a visitor has accepted the ConsentBanner.

**Setup checklist** before building dashboards:

1. In PostHog project settings, confirm `$pageview` autocapture is enabled.
2. Under **Data Management → Events**, verify these custom events have
   appeared at least once each. If any are missing, no one has triggered
   that flow yet — seed by clicking through it in prod (with consent granted).

## Custom events reference

Kept in sync with `frontend/src/lib/analytics.ts::ANALYTICS_EVENTS`.

| Event                        | Fired from                                                       | Key properties                          |
|------------------------------|------------------------------------------------------------------|-----------------------------------------|
| `newsletter_signup`          | `SubscribeCTA` (any placement) + `ExitIntentModal`               | `placement`, `variant`, `utm_source`    |
| `newsletter_signup_error`    | `SubscribeCTA` — API returned non-2xx                            | `placement`, `variant`, `error`         |
| `lead_magnet_confirmed`      | `Subscribed` page — landed with `?magnet=1` (post double-opt-in) | `source`                                |
| `confirmation_email_opened`  | Server-side, from SendGrid webhook (Tier 4)                      | `source`, `utm_source`                  |
| `referral_share_click`       | `Subscribed` — user clicked a share channel                      | `channel` (twitter/whatsapp/email)      |
| `essay_click`                | `Archive` on-site essay card                                     | `slug`, `placement`                     |
| `essay_scroll_75`            | Any essay page — 75% scroll milestone                            | `slug`, `ratio`                         |
| `essay_read_complete`        | Any essay page — bottom + 5s dwell                               | `slug`                                  |
| `speaker_inquiry`            | `Speak` + `/speak/:topic` — email/press-kit click                | `placement`, `topic`, `action`          |
| `press_article_click`        | `PressItemCard`                                                  | `outlet`, `title`, `url`                |
| `bio_link_click`             | `/links` — every card                                            | `source`, `destination`, `content`      |
| `external_link_click`        | Global `App` delegate — any `target=_blank` anchor               | `href`, `host`, `page_path`             |
| `page_view`                  | Route change (React Router)                                      | `page_path`, `page_name`                |

`newsletter_signup` and `speaker_inquiry` are additionally mirrored to GA4 /
Meta Pixel / TikTok Pixel via `mirrorConversionEvent` in
`frontend/src/lib/analytics.ts`.

## Funnel 1 — Full lead-magnet funnel

**Question it answers:** how many landing visitors become confirmed subscribers
who actually download the reader?

| Step | Event                        | Filter               |
|-----:|------------------------------|----------------------|
| 1    | `$pageview`                  | (any path)           |
| 2    | `newsletter_signup`          |                      |
| 3    | `confirmation_email_opened`  | (requires Tier 4 webhook + template) |
| 4    | `lead_magnet_confirmed`      |                      |

- **Time window:** 7 days between step 1 and step 4 (double-opt-in + magnet
  email typically clicked within a day, but 7d catches weekenders).
- **Breakdown:** by `utm_source` on `newsletter_signup` → shows which
  channels convert visitors into confirmed readers, not just signups.
- **Sanity check:** step-3 conversion should be > 70%. Lower means SendGrid
  template rendering issues or spam-folder delivery.

## Funnel 2 — Essay → subscription

**Question:** which essays actually convert readers, versus which just get
traffic?

| Step | Event                        | Filter                       |
|-----:|------------------------------|------------------------------|
| 1    | `$pageview`                  | `$pathname` matches `^/essays/` |
| 2    | `newsletter_signup`          | `placement` contains `essay-`  |

- **Time window:** same session (30 min).
- **Breakdown:** by the essay `$pathname` in step 1. Ranks essays by
  conversion rate, not just views. Highest-converting essays are candidates
  for the free 5-essay reader PDF.
- **Companion insight:** trends chart of `essay_read_complete` — reveals
  which essays hold attention to the end.

## Funnel 3 — Speaking pipeline

**Question:** which speaking-topic landing pages drive real booking inquiries?

| Step | Event                        | Filter                              |
|-----:|------------------------------|-------------------------------------|
| 1    | `$pageview`                  | `$pathname` matches `^/speak`       |
| 2    | `speaker_inquiry`            |                                     |

- **Time window:** same session.
- **Breakdown:** by `$pathname` in step 1 → separates `/speak` vs individual
  `/speak/:topic` pages. Topics with high conversion should get more inbound
  linking and paid amplification.

## Retention view — reader depth

Not a funnel. Trends chart with three series:

- `essay_click` (interest signal)
- `essay_scroll_75` (real engagement)
- `essay_read_complete` (loyal reader)

Interval: **daily**, break down by `slug`. Two useful cohorts:

- **New readers** — first `$pageview` in the last 7 days.
- **Return readers** — `$pageview` count ≥ 5 in the last 30 days. These are
  the highest-value users; they should be seeing the referral share block
  post-confirmation and should be over-indexed in `referral_share_click`.

## Alert recipes

Set as PostHog Insights → Alerts:

- **Signup drop:** `newsletter_signup` day-over-day drops > 40% → email Denise.
- **Confirmation collapse:** ratio of `confirmation_email_opened` to
  `newsletter_signup` (previous day) drops below 40% → email Denise (usually
  means SendGrid deliverability regression).
- **API 5xx surge:** `newsletter_signup_error` count > 20 in 1h → email Denise
  (backend or SendGrid outage).

## Maintenance

When a new event is added to `ANALYTICS_EVENTS`, add a row to the reference
table above. When a funnel changes (e.g. adding an interstitial step), update
the funnel here **and** rebuild the PostHog funnel in the UI — the two must
stay in sync or the funnel silently reports on the old shape.
