// Build-time generator for dist/sitemap.xml and dist/rss.xml.
//
// Fail-open: if the backend is unreachable in CI, we still emit a minimal
// sitemap of static routes so the build doesn't die. RSS is skipped in that
// case (no essays to feed it).
//
// Configured via env:
//   SITE_URL   canonical site URL (default: https://theincurablehumanist.com)
//   API_URL    backend base URL   (default: http://localhost:8000)
//
// Wired into `npm run build`.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { SPEAKING_TOPICS } from "../src/data/speakingTopics.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const DIST = resolve(HERE, "..", "dist");
const SITE_URL = (process.env.SITE_URL || "https://theincurablehumanist.com").replace(/\/$/, "");
const API_URL = (process.env.API_URL || "http://localhost:8000").replace(/\/$/, "");

// Static routes surfaced in the sitemap. Keep in sync with src/main.tsx.
// (Manual list — reading TS source at build time isn't worth the complexity.)
const STATIC_ROUTES = [
  { path: "/", priority: "1.0", changefreq: "weekly" },
  { path: "/about", priority: "0.8", changefreq: "monthly" },
  { path: "/archive", priority: "0.9", changefreq: "weekly" },
  { path: "/speak", priority: "0.8", changefreq: "monthly" },
  { path: "/listen", priority: "0.7", changefreq: "monthly" },
];

function xmlEscape(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

async function fetchStories() {
  try {
    const url = `${API_URL}/stories?status=published&limit=500`;
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(t);
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    return Array.isArray(data?.stories) ? data.stories : [];
  } catch (e) {
    console.warn(`[sitemap] Backend fetch failed (${e?.message ?? e}). Continuing with static routes only.`);
    return null;
  }
}

function buildSitemap(stories) {
  const now = new Date().toISOString();
  const urls = [];

  for (const r of STATIC_ROUTES) {
    urls.push(
      `  <url>\n` +
        `    <loc>${xmlEscape(SITE_URL + r.path)}</loc>\n` +
        `    <lastmod>${now}</lastmod>\n` +
        `    <changefreq>${r.changefreq}</changefreq>\n` +
        `    <priority>${r.priority}</priority>\n` +
        `  </url>`
    );
  }

  for (const topic of SPEAKING_TOPICS) {
    urls.push(
      `  <url>\n` +
        `    <loc>${xmlEscape(`${SITE_URL}/speak/${topic.slug}`)}</loc>\n` +
        `    <lastmod>${now}</lastmod>\n` +
        `    <changefreq>monthly</changefreq>\n` +
        `    <priority>0.7</priority>\n` +
        `  </url>`
    );
  }

  if (stories) {
    for (const s of stories) {
      const loc = `${SITE_URL}/essays/${s.slug}`;
      const lastmod = s.updated_at || s.published_at || now;
      urls.push(
        `  <url>\n` +
          `    <loc>${xmlEscape(loc)}</loc>\n` +
          `    <lastmod>${xmlEscape(lastmod)}</lastmod>\n` +
          `    <changefreq>monthly</changefreq>\n` +
          `    <priority>0.8</priority>\n` +
          `  </url>`
      );
    }
  }

  return (
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    urls.join("\n") +
    `\n</urlset>\n`
  );
}

function buildRss(stories) {
  if (!stories || stories.length === 0) return null;
  const now = new Date().toUTCString();
  const items = stories
    .slice(0, 30)
    .map((s) => {
      const url = `${SITE_URL}/essays/${s.slug}`;
      const pub = s.published_at ? new Date(s.published_at).toUTCString() : now;
      const desc = s.meta_description || s.excerpt || "";
      return (
        `    <item>\n` +
        `      <title>${xmlEscape(s.title)}</title>\n` +
        `      <link>${xmlEscape(url)}</link>\n` +
        `      <guid isPermaLink="true">${xmlEscape(url)}</guid>\n` +
        `      <pubDate>${pub}</pubDate>\n` +
        `      <description>${xmlEscape(desc)}</description>\n` +
        `    </item>`
      );
    })
    .join("\n");

  return (
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n` +
    `  <channel>\n` +
    `    <title>The Incurable Humanist</title>\n` +
    `    <link>${xmlEscape(SITE_URL)}</link>\n` +
    `    <atom:link href="${xmlEscape(`${SITE_URL}/rss.xml`)}" rel="self" type="application/rss+xml" />\n` +
    `    <description>Weekly essays on grief, migration, and art by Denise Rodriguez Dao.</description>\n` +
    `    <language>en-us</language>\n` +
    `    <lastBuildDate>${now}</lastBuildDate>\n` +
    items +
    `\n  </channel>\n` +
    `</rss>\n`
  );
}

async function main() {
  const stories = await fetchStories();

  mkdirSync(DIST, { recursive: true });

  const sitemap = buildSitemap(stories);
  writeFileSync(resolve(DIST, "sitemap.xml"), sitemap, "utf8");
  console.log(
    `[sitemap] Wrote sitemap.xml (${STATIC_ROUTES.length + SPEAKING_TOPICS.length + (stories?.length ?? 0)} URLs).`
  );

  const rss = buildRss(stories);
  if (rss) {
    writeFileSync(resolve(DIST, "rss.xml"), rss, "utf8");
    console.log(`[sitemap] Wrote rss.xml (${Math.min(stories.length, 30)} items).`);
  } else {
    console.log("[sitemap] Skipping rss.xml (no essays available).");
  }
}

main().catch((e) => {
  console.error("[sitemap] Fatal error:", e);
  // Fail-open — don't kill the build.
  process.exit(0);
});
