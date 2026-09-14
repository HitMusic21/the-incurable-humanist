// Build-time prerender for SEO / OG-scraper visibility. NOT SSR — the page
// still hydrates as a pure SPA on load. We just inject the right <title>,
// meta description, canonical, OG tags, and Article JSON-LD into <head> before
// the JS bundle boots, so bots that don't run JS (Googlebot mostly does, but
// many social scrapers and AI crawlers don't) see accurate per-page metadata.
//
// Written to `dist/<path>/index.html`. nginx serves them via existing
// `try_files $uri $uri/index.html /index.html`.
//
// Fail-open on network errors — logs a warning and continues with whatever
// pages it can render.

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
// Speaking topics come from the shared source of truth — the runtime SITE
// object (React consumers) and this build script now use the same list.
import { SPEAKING_TOPICS } from "../src/data/speakingTopics.mjs";
import {
  articleNode,
  breadcrumbNode,
  pageTitle,
  personNode,
  serviceNode,
  websiteNode,
} from "../src/lib/schemaNodes.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const DIST = resolve(HERE, "..", "dist");
const INDEX_HTML = resolve(DIST, "index.html");

const SITE_URL = (process.env.SITE_URL || "https://theincurablehumanist.com").replace(/\/$/, "");
const API_URL = (process.env.API_URL || "http://localhost:8000").replace(/\/$/, "");
// PERSON_ID / WEBSITE_ID are no longer declared here — they live in
// schemaNodes.mjs alongside the builders that use them, so the two cannot drift.

// Kept in inline mirrors so this script doesn't need to compile TS at build.
const STATIC_PAGES = [
  {
    // The homepage was previously the ONLY route this script did not touch,
    // so it kept index.html's hand-written JSON-LD while every other page
    // got prerender's (then-stubbed) version. Prerendering it too makes the
    // whole site consistent and is what scopes the /founder.jpg LCP preload
    // to the one route that actually renders it.
    path: "/",
    crumb: "Home",
    preloadImage: "/founder.jpg",
    title: "The Incurable Humanist | Grief, Migration, and Art",
    description:
      "Denise Rodriguez Dao writes The Incurable Humanist, a weekly newsletter on grief, migration, and art — and what gets inherited anyway.",
  },
  {
    path: "/about",
    title: "About — Denise Rodriguez Dao | The Incurable Humanist",
    description:
      "Denise Rodriguez Dao is a writer and immigration consultant based in New York. She writes The Incurable Humanist, a weekly newsletter on grief, migration, and art.",
  },
  {
    path: "/archive",
    title: "Archive — The Incurable Humanist",
    description:
      "A curated archive of essays by Denise Rodriguez Dao on grief, migration, and art. Start with the four essays that most fully express the work; then browse recent pieces.",
  },
  {
    path: "/speak",
    title: "Speaking — Denise Rodriguez Dao | The Incurable Humanist",
    description:
      "Denise Rodriguez Dao speaks on grief, migration, art, and the Latin American diaspora. Booking cultural centers, universities, and literary events.",
  },
  {
    path: "/listen",
    title: "Listen — The Incurable Humanist",
    description:
      "Audio essays and playlists from Denise Rodriguez Dao's Incurable Humanist newsletter.",
  },
  {
    path: "/press",
    crumb: "Press",
    title: "Press — Denise Rodriguez Dao | The Incurable Humanist",
    description:
      "Denise Rodriguez Dao in the press: Observer, The Art Gorgeous, Singulart Magazine, and La Guía de Caracas on Latin American art, migration, and cultural advocacy.",
  },
  {
    path: "/privacy",
    title: "Privacy — The Incurable Humanist",
    description:
      "How The Incurable Humanist handles analytics, cookies, and newsletter data — what is collected, why, and how to opt out.",
  },
  // Transactional landing pages. Both are noindex: /subscribed is the
  // double-opt-in destination (worker.py's confirm_lead redirects here) and
  // /links is the bio-link page, already Disallowed in robots.txt. Neither
  // belongs in search results, but both need a real title instead of
  // inheriting the generic homepage one from the shell.
  {
    path: "/subscribed",
    crumb: "Subscribed",
    noindex: true,
    title: "You're in — The Incurable Humanist",
    description:
      "Your subscription to The Incurable Humanist is confirmed. Weekly essays on grief, migration, and art, by Denise Rodriguez Dao.",
  },
  {
    path: "/links",
    crumb: "Links",
    noindex: true,
    title: "Links — The Incurable Humanist",
    description:
      "Denise Rodriguez Dao — newsletter, essays, speaking, and social links.",
  },
];

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Node builders now come from src/lib/schemaNodes.mjs (see the import at the
// top of this file). They used to be defined here as local copies, and they
// drifted: this file's personNode() returned only @type/@id/name/url, and
// because inject() strips index.html's id="tih-jsonld-page" block and replaces
// it, every prerendered page shipped a Person with no sameAs, no jobTitle and
// no alumniOf. Only the homepage — which this script does not touch — kept the
// rich node. Do not reintroduce local copies.

async function fetchStories() {
  try {
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(`${API_URL}/stories?status=published&limit=500`, {
      signal: controller.signal,
    });
    clearTimeout(t);
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    return Array.isArray(data?.stories) ? data.stories : [];
  } catch (e) {
    console.warn(`[prerender] Backend fetch failed (${e?.message ?? e}). Static pages only.`);
    return [];
  }
}

function renderHead({ title, description, canonical, ogImage, jsonLd, noindex, ogType, preloadImage }) {
  // Essay images are now self-hosted under /essay-images/, so cover_image_url is
  // a ROOT-RELATIVE path. og:image / twitter:image must be absolute or the
  // social + AI crawlers that fetch them out of context resolve nothing.
  if (ogImage && ogImage.startsWith("/")) ogImage = `${SITE_URL}${ogImage}`;
  const parts = [];
  parts.push(`<title>${escapeHtml(title)}</title>`);
  parts.push(`<meta name="description" content="${escapeHtml(description)}" />`);
  parts.push(`<link rel="canonical" href="${escapeHtml(canonical)}" />`);
  parts.push(`<meta property="og:title" content="${escapeHtml(title)}" />`);
  parts.push(`<meta property="og:description" content="${escapeHtml(description)}" />`);
  parts.push(`<meta property="og:url" content="${escapeHtml(canonical)}" />`);
  // "article" is right for essays and wrong for the homepage and the
  // marketing routes, which are not articles.
  parts.push(`<meta property="og:type" content="${escapeHtml(ogType || "website")}" />`);
  if (ogImage) {
    parts.push(`<meta property="og:image" content="${escapeHtml(ogImage)}" />`);
  }
  parts.push(`<meta name="twitter:card" content="summary_large_image" />`);
  parts.push(`<meta name="twitter:title" content="${escapeHtml(title)}" />`);
  parts.push(`<meta name="twitter:description" content="${escapeHtml(description)}" />`);
  if (ogImage) {
    parts.push(`<meta name="twitter:image" content="${escapeHtml(ogImage)}" />`);
  }
  parts.push(
    `<meta name="robots" content="${noindex ? "noindex, nofollow" : "index, follow"}" />`
  );
  if (preloadImage) {
    // Route-scoped LCP preload. The <img> lives inside the React tree, so
    // without this the browser only discovers it after the bundle parses.
    parts.push(
      `<link rel="preload" as="image" href="${escapeHtml(preloadImage)}" fetchpriority="high" />`
    );
  }
  parts.push(`<link rel="alternate" type="application/rss+xml" title="The Incurable Humanist" href="${SITE_URL}/rss.xml" />`);
  parts.push(
    `<script type="application/ld+json" id="tih-jsonld-page">${JSON.stringify(
      { "@context": "https://schema.org", "@graph": jsonLd }
    )}</script>`
  );
  return parts.join("\n    ");
}

// Rewrite the shell HTML by removing any tag we intend to re-emit, then
// injecting our block. Idempotent — safe if prerender runs twice.
function inject(shellHtml, headBlock) {
  let html = shellHtml;
  // Strip existing <title>, <meta name="description">, <link rel="canonical">, and any
  // existing JSON-LD "tih-jsonld-page" script so we don't duplicate.
  html = html.replace(/<title>[\s\S]*?<\/title>/i, "");
  html = html.replace(/<meta\s+name=["']description["'][^>]*>/gi, "");
  html = html.replace(/<link\s+rel=["']canonical["'][^>]*>/gi, "");
  html = html.replace(
    /<script[^>]*id=["']tih-jsonld-page["'][^>]*>[\s\S]*?<\/script>/gi,
    ""
  );
  html = html.replace(
    /<meta\s+property=["']og:(title|description|url|image|type)["'][^>]*>/gi,
    ""
  );
  html = html.replace(
    /<meta\s+name=["']twitter:(card|title|description|image)["'][^>]*>/gi,
    ""
  );
  html = html.replace(/<meta\s+name=["']robots["'][^>]*>/gi, "");
  // Inject our block right before </head>.
  return html.replace(/<\/head>/i, `    ${headBlock}\n  </head>`);
}

function writePage(routePath, html) {
  const outDir = resolve(DIST, "." + routePath);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(resolve(outDir, "index.html"), html, "utf8");
}

async function main() {
  let shell;
  try {
    shell = readFileSync(INDEX_HTML, "utf8");
  } catch (e) {
    console.error(`[prerender] Can't read dist/index.html — did vite build run? (${e?.message ?? e})`);
    process.exit(0);
  }

  let written = 0;

  // Static pages
  for (const p of STATIC_PAGES) {
    const canonical = `${SITE_URL}${p.path}`;
    const head = renderHead({
      title: p.title,
      description: p.description,
      canonical,
      // `noindex` is forwarded for transactional pages (/subscribed, /links).
      // Before this, the flag existed on renderHead but was never passed.
      noindex: p.noindex,
      preloadImage: p.preloadImage,
      jsonLd: [
        personNode(),
        websiteNode(),
        // The homepage is the breadcrumb root, so it gets a single-item trail
        // rather than "Home > Home".
        breadcrumbNode(
          p.path === "/"
            ? [{ name: "Home", path: "/" }]
            : [
                { name: "Home", path: "/" },
                { name: p.crumb || p.title.split(" — ")[0], path: p.path },
              ]
        ),
      ],
    });
    writePage(p.path, inject(shell, head));
    written++;
  }

  // Speaking topics
  for (const t of SPEAKING_TOPICS) {
    const url = `${SITE_URL}/speak/${t.slug}`;
    const head = renderHead({
      title: `${t.title} — Speaking with Denise Rodriguez Dao`,
      description: t.blurb,
      canonical: url,
      jsonLd: [
        personNode(),
        websiteNode(),
        breadcrumbNode([
          { name: "Home", path: "/" },
          { name: "Speaking", path: "/speak" },
          { name: t.title, path: `/speak/${t.slug}` },
        ]),
        serviceNode({ title: t.title, url, blurb: t.blurb }),
      ],
    });
    writePage(`/speak/${t.slug}`, inject(shell, head));
    written++;
  }


// Fail-open is right for a flaky network and WRONG for a misconfigured
// API_URL: that ships a 10-URL sitemap and 9 prerendered pages instead of 83
// and 84, silently, and the deploy looks successful. Require an explicit
// opt-out so an empty build is always a deliberate choice.
function assertStories(stories, label) {
  if (stories && stories.length) return;
  if (process.env.ALLOW_EMPTY_BUILD) {
    console.warn(`[${label}] 0 essays — continuing because ALLOW_EMPTY_BUILD is set.`);
    return;
  }
  console.error(
    `[${label}] 0 essays fetched from ${API_URL}.\n` +
      `  The build would ship a site with no essays. Point API_URL at a live\n` +
      `  backend, or set ALLOW_EMPTY_BUILD=1 if that is genuinely intended.`
  );
  process.exit(1);
}

  // Essays (network-dependent)
  const stories = await fetchStories();
  assertStories(stories, "prerender");
  for (const s of stories) {
    const ownUrl = `${SITE_URL}/essays/${s.slug}`;
    const canonical = s.canonical_url && s.canonical_url.length > 0 ? s.canonical_url : ownUrl;
    const description = s.meta_description || s.excerpt || `${s.title} — an essay by Denise Rodriguez Dao.`;
    const head = renderHead({
      // Truncated for the <title> only. 28 of 73 essay titles overflowed the
      // ~60-char search-result budget once the suffix was appended (worst: 159
      // chars). articleNode below keeps the FULL headline, which schema.org
      // wants and which has no length limit.
      title: pageTitle(s.title),
      description,
      canonical,
      ogImage: s.cover_image_url || undefined,
      ogType: "article",
      jsonLd: [
        personNode(),
        websiteNode(),
        breadcrumbNode([
          { name: "Home", path: "/" },
          // Label follows the nav ("Writing"); the path stays /archive,
          // which is where the inbound links and the sitemap point.
          { name: "Writing", path: "/archive" },
          { name: s.title, path: `/essays/${s.slug}` },
        ]),
        articleNode({
          title: s.title,
          url: ownUrl,
          description,
          published: s.published_at || undefined,
          modified: s.updated_at || undefined,
          image: s.cover_image_url || undefined,
        }),
      ],
    });
    writePage(`/essays/${s.slug}`, inject(shell, head));
    written++;
  }

  console.log(`[prerender] Wrote ${written} prerendered pages (${STATIC_PAGES.length} static + ${SPEAKING_TOPICS.length} topics + ${stories.length} essays).`);
}

main().catch((e) => {
  console.error("[prerender] Fatal error:", e);
  // Fail-open.
  process.exit(0);
});
