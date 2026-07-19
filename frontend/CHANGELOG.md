# Frontend Changelog

Chronological log of user-facing UI/UX changes. Newest first.

Conventions: see `docs/UI_DESIGN_SYSTEM.md`.
Load-bearing conventions summary: see repo-root `CLAUDE.md` § "UI conventions (frontend)".

---

## 2026-07-19

### Fixed

- **`/about` — prose measure + justification** (`src/pages/About.tsx`)
  Both prose containers (the "The Incurable Humanist" card and the "The Founder" card) rendered at ~880px+ card width, producing 100+ character lines with ragged right edges and awkward line breaks (e.g. `"It is leaving home, it is / heartbreak"`). Swapped `max-w-3xl` + `leading-relaxed` for `max-w-[62ch]` + `leading-[1.75]` + `text-justify` + `hyphens-auto` + `[text-wrap:pretty]`. Line lengths now ~78 chars; edges symmetric; hyphens break at natural syllable boundaries (`mi- gration`, `en- dure`). Matches the prospectus / literary-journal treatment already used on the landing page. Canonical reference for future prose blocks: see the About page or `docs/UI_DESIGN_SYSTEM.md` § Convention #1.

- **`/speak` — CTA pill overflow** (`src/pages/Speak.tsx`)
  The "Email booking@theincurablehumanist.com" pill button was stretching into a grotesque tall oval because a 32-character email inside a fixed `h-12 rounded-pill` overflowed and forced text to wrap inside the pill. Neighboring "Download press kit (PDF)" button similarly broken. Shortened button labels to "Email Denise" + "Press kit (PDF)"; moved the full email into the trust line below as an inline underlined link (`Response within 3 business days · booking@…`); added `whitespace-nowrap` on both buttons so text physically can't wrap mid-pill; added `flex-wrap` on the parent so pills drop to a new row on narrow viewports rather than crush; added envelope + download SVG icons (Heroicons/Lucide 24×24 style, `w-4 h-4`); added `focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2` for keyboard focus (a11y CRITICAL); added `aria-label` on both anchors so screen readers still get the full descriptive text; added `cursor-pointer`. Canonical reference for future CTA pairs: see the Speak page or `docs/UI_DESIGN_SYSTEM.md` § Convention #2.

### Added

- **`docs/UI_DESIGN_SYSTEM.md`** — living design-system reference. Documents the two load-bearing conventions above (long-form prose + pill CTAs with long labels), the anti-patterns that produce known regressions, the Docker dev loop caveat (pre-built bundle + Chrome cache), and the canonical file references to copy from when introducing a new page.

- **`CLAUDE.md` § "UI conventions (frontend)"** — condensed version of the two load-bearing conventions so future Claude sessions inherit them without needing to read the full design system doc first.

- **`frontend/CHANGELOG.md`** (this file) — chronological log of UI changes for future traceability.

### Notes

The Docker frontend container serves a pre-built nginx bundle. `.tsx` edits require `docker compose up -d --build frontend` (or `--no-cache` for a full rebuild). Chrome then needs a hard reload (Cmd+Shift+R). This tripped up today's iteration cycle — documented in `docs/UI_DESIGN_SYSTEM.md` § Convention #3 so future sessions don't hit it. For iterative UI work, prefer `make fe-dev` (Vite HMR on `:5173`); rebuild the container only for final production-bundle verification.

---

## Format

Group entries by date under `## YYYY-MM-DD` headings. Use `### Fixed`, `### Added`, `### Changed`, `### Removed`, `### Notes` subheadings. One entry per user-facing change; a short paragraph is fine — include the file, the symptom, the root cause, and the fix. Link to `docs/UI_DESIGN_SYSTEM.md` when a change reifies a new load-bearing convention.
