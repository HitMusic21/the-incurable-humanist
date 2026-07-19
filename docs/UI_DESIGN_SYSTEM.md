# UI Design System — The Incurable Humanist

**Last updated:** 2026-07-19
**Owner:** Frontend
**Status:** Living document — update in the same commit as any change to the site's visual language.

This document captures the small set of load-bearing UI decisions that have been made deliberately and should not silently regress. It is a companion to (not replacement for) Tailwind config, `frontend/src/config/site.ts`, and per-component code.

If you are adding a new page or component, read this first. If you're proposing to change one of these conventions, update this doc in the same PR — otherwise the next Claude session (or human) will unknowingly regress it.

---

## Visual identity

**Genre**: prospectus / literary journal.
**Tone**: measured, considered, editorial. Not "SaaS." Not "startup landing."
**Voice**: serif for content, sans-serif for UI chrome. Warm off-white background, muted ink, small accent color used sparingly.

Design tokens live in `frontend/tailwind.config.ts`. Colors we use:
- `bg` / `surface` — the warm cream page background + card fills
- `ink` — primary text
- `muted-ink` — secondary text (captions, metadata)
- `accent` / `accent2` — the two accent colors (small doses only — buttons, headings, links)
- `line` — hairline borders

---

## Convention #1 — Long-form prose

### The rule

Any prose block that reads like body copy (About page bio, essay body, newsletter card body, founder statement, etc.) MUST use this exact combination:

```tsx
<div className="space-y-8 text-[17px] md:text-[18px] leading-[1.75] max-w-[62ch] mx-auto text-justify hyphens-auto [text-wrap:pretty]">
  <p>…</p>
  <p>…</p>
</div>
```

### Why each class matters

| Class | Purpose | Why not the obvious alternative |
|---|---|---|
| `max-w-[62ch]` | Constrains the reading measure to ~62 chars per line | `max-w-3xl` = 768px = ~100+ chars at 18px serif. Well past the 65-75ch readability sweet spot. Fatigues the eye. |
| `mx-auto` | Centers the block in the parent card | `text-center` would center each line — wrong for prose. |
| `text-justify` | Even left AND right edges | Left-only is fine for casual UI copy. For prospectus prose the symmetric edge is the visual signature of the site. |
| `hyphens-auto` | Enables browser-native hyphenation | Without it, `text-justify` creates rivers of white space between words on narrow measures. `hyphens-auto` breaks at natural syllable boundaries and smooths the rhythm. |
| `leading-[1.75]` | Line-height 1.75 for long-form density | `leading-relaxed` (1.625) is fine for UI copy. Long-form serif prose benefits from more air between lines. |
| `[text-wrap:pretty]` | Modern CSS `text-wrap: pretty` | Avoids widows/orphans (single word on the last line) on Safari 17+ and Chrome 117+. Progressive enhancement — degrades gracefully. |
| `space-y-8` | Consistent inter-paragraph vertical rhythm | Matches the 32px gap the landing page uses. |

### Anti-pattern (do NOT do this)

```tsx
{/* BAD — ragged edges, oversized measure, no hyphens, wrong line-height */}
<div className="space-y-8 text-[17px] md:text-[18px] leading-relaxed max-w-3xl mx-auto">
  <p>Grief is more than mourning the death of a loved one. It is leaving home, it is heartbreak, it is losing who we once were, it is navigating trauma.</p>
</div>
```

This is exactly what `frontend/src/pages/About.tsx` looked like before the 2026-07-19 fix. Output: 100+ chars per line, ragged right edges, awkward line breaks. Fixed by swapping to the canonical class list above.

### Canonical reference

`frontend/src/pages/About.tsx` — both prose containers (the "The Incurable Humanist" card and the "The Founder" card) use the canonical class list verbatim. Copy from there when introducing a new prose block.

---

## Convention #2 — Pill CTAs with long labels

### The rule

Any pill-shaped CTA that MIGHT carry a long label (email address, URL, long phrase) MUST follow this pattern:

```tsx
<div className="flex flex-col sm:flex-row flex-wrap gap-3">
  <a
    href={mailto}
    aria-label={`Email ${SITE.bookingEmail} — Speaking inquiry`}
    className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 active:brightness-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent2 transition font-medium whitespace-nowrap cursor-pointer"
  >
    <svg viewBox="0 0 24 24" className="w-4 h-4" aria-hidden="true">…</svg>
    Email Denise
  </a>
  {/* … second button, same shape … */}
</div>

<p className="mt-4 text-[13px] text-muted-ink">
  Response within 3 business days ·{" "}
  <a href={`mailto:${SITE.bookingEmail}`} className="underline decoration-muted-ink/40 underline-offset-2 hover:text-accent2 hover:decoration-accent2 transition-colors">
    {SITE.bookingEmail}
  </a>
</p>
```

### Why each rule matters

| Rule | Purpose | Consequence of skipping |
|---|---|---|
| Button label is short (≤ ~16 chars) | Pill stays visually a pill | Long strings inside `h-12 rounded-pill` force text to wrap inside the pill, producing a grotesque tall oval. |
| `whitespace-nowrap` | Text physically cannot break mid-line | Belt on top of the "short label" suspenders. |
| Parent has `flex-wrap` | Buttons drop to a new row on narrow viewports | Without it, two pills on a narrow column crush each other. |
| `aria-label` carries the full descriptive string | Screen readers get the full context that visual users get from the trust line below | `<a>Email Denise</a>` alone is ambiguous to a screen reader. |
| `focus-visible:outline …-offset-2` | Keyboard focus ring | Keyboard users cannot see focus. CRITICAL a11y regression. |
| `cursor-pointer` | Explicit interactive-cursor state | Some Tailwind base resets strip `cursor: pointer` from anchors — always add it explicitly on CTAs. |
| SVG icons (not emoji) | Consistent stroke + color | Emoji icons render differently across OS + look amateur. Use Heroicons / Lucide style outlined SVGs. |
| Full email/URL in a trust line below | Users still see + can copy the address | Preserves the affordance without breaking the pill layout. |

### Anti-pattern (do NOT do this)

```tsx
{/* BAD — 32-char email inside a fixed-height pill, no whitespace-nowrap, no focus ring, no aria-label */}
<a
  href={mailto}
  className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 active:brightness-95 transition font-medium"
>
  Email {SITE.bookingEmail}
</a>
```

This is what `frontend/src/pages/Speak.tsx` looked like before the 2026-07-19 fix. Output: a stretched tall oval with text wrapping inside. Fixed by shortening the label to "Email Denise", moving the email to the trust line, adding `whitespace-nowrap`, `focus-visible:outline`, `aria-label`, and an SVG icon.

### Canonical reference

`frontend/src/pages/Speak.tsx` — the "Bring The Incurable Humanist to your stage" card contains the two-button pair (`Email Denise` + `Press kit (PDF)`). Copy that class list verbatim when introducing a new CTA pair.

---

## Convention #3 — Docker dev loop + browser cache

The frontend Docker container serves a **pre-built nginx bundle**, not a Vite dev server. Two implications:

1. **Edits to `.tsx` files are NOT hot-reloaded in the container.** You must rebuild:
   ```bash
   docker compose up -d --build frontend           # normal rebuild
   docker compose build --no-cache frontend        # force full rebuild
   ```
2. **Chrome caches nginx assets aggressively.** After a rebuild, always hard-reload (Cmd+Shift+R) or check "Disable cache" in DevTools → Network. Otherwise the browser shows the previous bundle even though the container has the new one.

### Recommended iterative flow

For UI work with fast feedback:
```bash
make fe-dev                                     # Vite HMR on :5173, edits reload instantly
```

Only use the Docker container to verify the final production-bundled output before shipping.

---

## Anti-patterns index

Quick scan when reviewing or writing UI code — these are the ones that show up repeatedly.

| Symptom | Root cause | Fix |
|---|---|---|
| Prose block has line lengths >90 chars | Missing `max-w-[62ch]` | Add the canonical prose class list (Convention #1) |
| Prose has ragged, uneven right edge | Missing `text-justify` + `hyphens-auto` | Add both |
| Pill button stretched vertically into a tall oval | Long label + fixed `h-12` + no `whitespace-nowrap` | Shorten label, add `whitespace-nowrap`, move full string to trust line (Convention #2) |
| Two pills crushed together on narrow viewport | Missing `flex-wrap` on parent | Add `flex-wrap` |
| Icon-only or icon+short-label button reads as "button" in screen reader | Missing `aria-label` | Add descriptive `aria-label` |
| No focus ring when tabbing | Missing `focus-visible:outline` | Add the standard outline classes |
| Emoji as icon | Ambient laziness | Replace with SVG (Heroicons / Lucide 24×24 viewBox, `w-4 h-4` or `w-6 h-6`) |
| Browser shows old UI after Docker rebuild | Chrome / nginx cache | Cmd+Shift+R or DevTools "Disable cache" |

---

## Extending this document

When you make a design decision that would be regrettable to silently regress:

1. Add a new numbered Convention here
2. Include: the rule, why each class matters, the anti-pattern, and a canonical reference (file + component)
3. Update `CLAUDE.md` § "UI conventions (frontend)" if it's a load-bearing rule
4. Add an entry to `frontend/CHANGELOG.md` with the date and reference

Small doc + tight referencing beats sprawling doc.
