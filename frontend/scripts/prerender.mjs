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

const HERE = dirname(fileURLToPath(import.meta.url));
const DIST = resolve(HERE, "..", "dist");
const INDEX_HTML = resolve(DIST, "index.html");

const SITE_URL = (process.env.SITE_URL || "https://theincurablehumanist.com").replace(/\/$/, "");
const API_URL = (process.env.API_URL || "http://localhost:8000").replace(/\/$/, "");
const PERSON_ID = `${SITE_URL}/about#denise`;
const WEBSITE_ID = `${SITE_URL}#website`;

// Kept in inline mirrors so this script doesn't need to compile TS at build.
const STATIC_PAGES = [
  {
    path: "/about",
    title: "About — Denise Rodriguez Dao | The Incurable Humanist",
    description:
      "Denise Rodriguez Dao is a writer and immigration attorney based in New York. She writes The Incurable Humanist, a weekly newsletter on grief, migration, and art.",
  },
  {
    path: "/archive",
    title: "Archive — The Incurable Humanist",
    description:
      "A curated archive of essays by Denise Rodriguez Dao on grief, migration, and art. Start with the four essays that most fully express the work; then browse recent pieces.",
  },
  {
    path: "/speak",
    title: "Speak — Denise Rodriguez Dao | The Incurable Humanist",
    description:
      "Denise Rodriguez Dao speaks on grief, migration, art, and the Latin American diaspora. Booking cultural centers, universities, and literary events.",
  },
  {
    path: "/listen",
    title: "Listen — The Incurable Humanist",
    description:
      "Audio essays and playlists from Denise Rodriguez Dao's Incurable Humanist newsletter.",
  },
];

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function personNode() {
  return {
    "@type": "Person",
    "@id": PERSON_ID,
    name: "Denise Rodriguez Dao",
    url: `${SITE_URL}/about`,
  };
}
function websiteNode() {
  return {
    "@type": "WebSite",
    "@id": WEBSITE_ID,
    url: SITE_URL,
    name: "The Incurable Humanist",
    publisher: { "@id": PERSON_ID },
  };
}
function articleNode({ title, url, description, published, modified, image }) {
  return {
    "@type": "Article",
    headline: title,
    url,
    ...(description ? { description } : {}),
    ...(published ? { datePublished: published } : {}),
    ...(modified ? { dateModified: modified } : {}),
    ...(image ? { image } : {}),
    author: { "@id": PERSON_ID },
    publisher: { "@id": PERSON_ID },
    mainEntityOfPage: url,
    isPartOf: { "@id": WEBSITE_ID },
  };
}
function serviceNode({ title, url, blurb }) {
  return {
    "@type": "Service",
    serviceType: "Speaking Engagement",
    name: title,
    description: blurb,
    provider: { "@id": PERSON_ID },
    url,
  };
}

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

function renderHead({ title, description, canonical, ogImage, jsonLd, noindex }) {
  const parts = [];
  parts.push(`<title>${escapeHtml(title)}</title>`);
  parts.push(`<meta name="description" content="${escapeHtml(description)}" />`);
  parts.push(`<link rel="canonical" href="${escapeHtml(canonical)}" />`);
  parts.push(`<meta property="og:title" content="${escapeHtml(title)}" />`);
  parts.push(`<meta property="og:description" content="${escapeHtml(description)}" />`);
  parts.push(`<meta property="og:url" content="${escapeHtml(canonical)}" />`);
  parts.push(`<meta property="og:type" content="article" />`);
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
      jsonLd: [personNode(), websiteNode()],
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
      jsonLd: [personNode(), websiteNode(), serviceNode({ title: t.title, url, blurb: t.blurb })],
    });
    writePage(`/speak/${t.slug}`, inject(shell, head));
    written++;
  }

  // Essays (network-dependent)
  const stories = await fetchStories();
  for (const s of stories) {
    const ownUrl = `${SITE_URL}/essays/${s.slug}`;
    const canonical = s.canonical_url && s.canonical_url.length > 0 ? s.canonical_url : ownUrl;
    const description = s.meta_description || s.excerpt || `${s.title} — an essay by Denise Rodriguez Dao.`;
    const head = renderHead({
      title: `${s.title} — The Incurable Humanist`,
      description,
      canonical,
      ogImage: s.cover_image_url || undefined,
      jsonLd: [
        personNode(),
        websiteNode(),
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
