# docs/

**Last curated:** 20 September 2026

Start with `ARCHITECTURE.md` — the body of the root `CLAUDE.md` describes the
retired Cloud Run stack, not what is deployed.

---

## Engineering

| Doc | What it covers |
|---|---|
| **`ARCHITECTURE.md`** | **The system as deployed.** Cloudflare Worker + D1, the seven load-bearing decisions, build pipeline, known constraints. Read first. |
| `UI_DESIGN_SYSTEM.md` | Visual conventions that must not silently regress — prose measure, pill CTAs, the Docker dev loop. |
| `SEO_REMAINING_SETUP.md` | What still needs credentials or a dashboard: HSTS, CSP promotion. GSC access is now resolved (§1). |
| `utm-registry.md` | UTM parameter conventions. |
| `analytics-dashboards.md` | What is tracked and where. |

## Audience & growth

| Doc | What it covers |
|---|---|
| **`ICP_AND_GROWTH_ANALYSIS.md`** | **The ICP, built from Substack first-party data.** The finding that reframes everything: Substack's network drove 108 of 167 subscribers, Google drove 4. |
| `ESSAY_TOPIC_RESEARCH_SEP2026.md` | Researched non-Venezuela essay topics, ranked, with publish timing and verification warnings. |
| `ESSAY_SUBHEADINGS_REVIEW.md` | Per-essay `<h2>` proposals for Denise's approval. Eight essays already contain her own labels as `<strong>` — those need promoting, not writing. |
| `BRAND_ECOSYSTEM_PLAN.md` | Brand/positioning plan. *(Was `Markdown text file.md` — renamed Sep 2026 so it is findable.)* |
| `welcome-sequence.md` | Onboarding email sequence. |
| `substack-canonical-checklist.md` | Per-post canonical URLs. **Now optional** — GSC confirms Google already picks our canonical. |

---

## Removed 2026-09-20

Eight files, with the user's approval:

- **Seven 0-byte files** — `PRD.md`, `BRAND IDENTITY PACKAGE.md`,
  `SEO CONTENT STRATEGY.md`, `AD CREATIVE PACKAGE.md`, `feature specs.md`,
  `landing page.md`, `mvp roadmap.md`. Empty since creation in Oct 2025 and
  actively misleading — a file named `SEO CONTENT STRATEGY.md` implies a
  strategy exists.
- **`RIS_User_Personas.md`** — 593 lines of buyer personas for **music royalty
  software**. 59 royalty/catalog terms, zero mentions of Denise, essays or
  Substack. Stray from another repo; a real risk that someone would read it
  and act on the wrong personas.

All recoverable from git history.

---

## Conventions

- Update a doc in the **same commit** as the change it describes.
- State what was **measured** and what is **assumed** — every doc here marks
  its own gaps rather than filling them with plausible-sounding numbers.
- When a recommendation is later disproven by data, **annotate it in place**
  rather than quietly deleting it. See the update banner on
  `substack-canonical-checklist.md`.
