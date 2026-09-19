// Build-time generator for dist/related-essays.json.
//
// WHY THIS EXISTS
// ---------------
// Before Sep 2026, ZERO of the 75 essays linked to any other essay. /archive
// was the only page linking to them, so every essay sat one hop from the index
// and zero hops from its siblings. That costs three things at once: internal
// links are how PageRank flows, related links are how a reader goes from one
// essay to a second, and topic clusters are how a search engine infers what a
// site is ABOUT rather than just what each page says.
//
// There is no tag data to build this from. The `theme` / `story_theme` tables
// exist in the legacy SQLModel backend but were never migrated to D1 — the
// live database has exactly one content table, `story`, with no tags column.
// So relatedness is derived from the prose itself.
//
// HOW
// ---
// Classic TF-IDF cosine similarity over title + body:
//   - title terms count 3x. The title states the subject most directly, and
//     without the weighting the long tail of body text drowns it out.
//   - terms appearing in only ONE essay are dropped (df > 1). They cannot
//     express similarity to anything and just add noise to the norm.
//   - a MIN_SCORE floor applies. Measured on the real corpus, forcing three
//     links onto every essay produced pairings like "Stop Calling Frida and
//     Diego Relationship Goals" -> "June Reading List" at 0.11, which is
//     essentially random. An essay with no genuine sibling shows nothing:
//     a bad recommendation is worse than an absent one, for the reader and
//     for the topical signal.
//
// Why build-time and not a Worker endpoint: this is O(n^2) over the full
// corpus and the corpus only changes when the hourly sync writes. Recomputing
// it per request would burn CPU on every essay view to produce a value that
// changes at most once an hour.
//
// Reads the same API_URL as generate-sitemap.mjs. Fail-open in the same way:
// a missing file makes RelatedEssays render nothing, which is exactly the
// pre-Sep-2026 behaviour, so a CI outage cannot break the build.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const DIST = resolve(HERE, "..", "dist");
const API_URL = (process.env.API_URL || "http://localhost:8000").replace(/\/$/, "");

/** How many related essays to show at most. Three fits one row on desktop. */
const MAX_RELATED = 3;

/**
 * Minimum cosine similarity to count as "related".
 *
 * Tuned against the live 75-essay corpus. At this floor 19% of essays get no
 * related links at all, which is the intended behaviour — see the header.
 * Lowering it to 0.08 links every essay but reintroduces the random pairings.
 */
const MIN_SCORE = 0.12;

// Function words carry no topical signal but are frequent enough to distort
// the vectors. Short tokens (<4 chars) are dropped separately.
const STOP = new Set(
  `a an the and or but if then than that this these those of in on at to for with by
   from as is are was were be been being it its i you he she they we me my your his
   her their our us them do does did not no so such own same too very can will just
   should now what which who when where why how all any both each few more most other
   some only don have has had would could may might must about into over under again
   further once because while during before after above below up down out off there
   here`.split(/\s+/)
);

function tokenize(input) {
  const text = String(input || "")
    .replace(/<[^>]+>/g, " ") // strip markup — bodies are sanitized HTML
    .replace(/[‘’]/g, "'")
    .toLowerCase();
  const out = [];
  for (const word of text.match(/[a-z][a-z'-]{2,}/g) || []) {
    if (word.length > 3 && !STOP.has(word)) out.push(word);
  }
  return out;
}

function termFrequencies(story) {
  const counts = new Map();
  // Title terms weighted 3x — see header.
  const terms = [
    ...tokenize(story.title),
    ...tokenize(story.title),
    ...tokenize(story.title),
    ...tokenize(story.content || story.excerpt || ""),
  ];
  for (const t of terms) counts.set(t, (counts.get(t) || 0) + 1);
  return counts;
}

function buildVectors(stories) {
  const tf = new Map();
  const df = new Map();
  for (const s of stories) {
    const counts = termFrequencies(s);
    tf.set(s.slug, counts);
    for (const term of counts.keys()) df.set(term, (df.get(term) || 0) + 1);
  }

  const n = stories.length;
  const vectors = new Map();
  for (const [slug, counts] of tf) {
    const vec = new Map();
    let sumSquares = 0;
    for (const [term, count] of counts) {
      const docFreq = df.get(term);
      if (docFreq < 2) continue; // unique to one essay — cannot express similarity
      const weight = (1 + Math.log(count)) * Math.log(n / docFreq);
      vec.set(term, weight);
      sumSquares += weight * weight;
    }
    const norm = Math.sqrt(sumSquares) || 1;
    for (const [term, weight] of vec) vec.set(term, weight / norm);
    vectors.set(slug, vec);
  }
  return vectors;
}

function cosine(a, b) {
  // Iterate the smaller vector; the result is symmetric either way.
  const [small, large] = a.size <= b.size ? [a, b] : [b, a];
  let total = 0;
  for (const [term, weight] of small) {
    const other = large.get(term);
    if (other) total += weight * other;
  }
  return total;
}

export function computeRelated(stories) {
  const vectors = buildVectors(stories);
  const bySlug = new Map(stories.map((s) => [s.slug, s]));
  const result = {};

  for (const story of stories) {
    const self = vectors.get(story.slug);
    const scored = [];
    for (const other of stories) {
      if (other.slug === story.slug) continue;
      const score = cosine(self, vectors.get(other.slug));
      if (score >= MIN_SCORE) scored.push({ slug: other.slug, score });
    }
    scored.sort((x, y) => y.score - x.score);
    const top = scored.slice(0, MAX_RELATED).map((m) => {
      const s = bySlug.get(m.slug);
      return { slug: s.slug, title: s.title, excerpt: s.excerpt || null };
    });
    if (top.length) result[story.slug] = top;
  }
  return result;
}

async function fetchStories() {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    // limit=500 covers the corpus; `content` comes back only on the detail
    // endpoint, so bodies are fetched per essay below.
    const res = await fetch(`${API_URL}/stories?status=published&limit=500`, {
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    const list = Array.isArray(data?.stories) ? data.stories : [];

    // Excerpts alone average ~300 chars, which measurably degrades the
    // pairings (it produced "Good Grief" -> "Becoming a Plantain Chip
    // Connoisseur"). Pull the full body for each essay instead.
    const withBodies = [];
    for (const s of list) {
      try {
        const r = await fetch(`${API_URL}/stories/${encodeURIComponent(s.slug)}`);
        const detail = r.ok ? await r.json() : null;
        withBodies.push({ ...s, content: detail?.content || "" });
      } catch {
        withBodies.push({ ...s, content: "" });
      }
    }
    return withBodies;
  } catch (e) {
    console.warn(
      `[related] Backend fetch failed (${e?.message ?? e}). Skipping related-essays.json.`
    );
    return null;
  }
}

async function main() {
  const stories = await fetchStories();
  if (!stories || stories.length === 0) {
    console.warn("[related] No essays available — skipping related-essays.json.");
    return;
  }

  const related = computeRelated(stories);
  mkdirSync(DIST, { recursive: true });
  writeFileSync(resolve(DIST, "related-essays.json"), JSON.stringify(related), "utf8");

  const links = Object.values(related).reduce((n, v) => n + v.length, 0);
  const covered = Object.keys(related).length;
  console.log(
    `[related] Wrote related-essays.json (${links} links across ${covered}/${stories.length} essays).`
  );
}

// Only run when invoked directly, so the pure functions above stay unit-testable.
if (process.argv[1] && process.argv[1].endsWith("generate-related.mjs")) {
  main();
}
