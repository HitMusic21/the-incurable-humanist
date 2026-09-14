// Single source of truth for JSON-LD @graph nodes.
//
// Consumed by:
//   - src/lib/schema.ts       (React runtime — re-exports these, so TS callers
//                              are unchanged)
//   - scripts/prerender.mjs   (build-time, bare Node — no TS toolchain)
//   - scripts/generate-sitemap.mjs (toIsoUtc only)
//
// Written as .mjs for the same reason as src/data/speakingTopics.mjs: bare Node
// build scripts must import it without a TS compile step and without Vite's
// `@/` alias, which Node cannot resolve. The sibling .d.mts types it for TS.
//
// WHY THIS MODULE EXISTS
// ----------------------
// prerender.mjs used to carry its OWN personNode() returning only
// @type/@id/name/url. Because its inject() strips the id="tih-jsonld-page"
// block out of index.html and replaces it, every prerendered page shipped a
// Person with no sameAs, no jobTitle, no alumniOf — silently undoing the entity
// consolidation that index.html's block exists to provide. Only the homepage,
// which prerender does not touch, kept the rich node. Verified live before the
// fix: /about's Person had exactly ["@id","@type","name","url"].
//
// Keep the site constants below in sync with src/config/site.ts. They are
// duplicated rather than imported because site.ts is TypeScript and imports the
// `@/` alias; a vitest test (indexHtmlSchema.test.ts) asserts index.html's
// hardcoded block still matches what these builders emit.

export const SITE_URL = "https://theincurablehumanist.com";
export const PERSON_ID = `${SITE_URL}/about#denise`;
// No trailing slash before the fragment. index.html hardcoded
// "…com/#website", which is a DIFFERENT @id string than every other producer
// emits, so consumers saw two unrelated WebSite entities instead of one.
export const WEBSITE_ID = `${SITE_URL}#website`;

export const POSITIONING = "Grief, migration, and art — and what gets inherited anyway.";

export const SAME_AS = [
  "https://www.instagram.com/theincurablehumanist/",
  "https://www.tiktok.com/@theincurablehumanist",
  "https://www.facebook.com/profile.php?id=61581842306462",
  "https://www.linkedin.com/company/the-incurable-humanist/about/",
  "https://x.com/TheIncurableHum",
  "https://theincurablehumanist.substack.com",
];

export function personNode() {
  return {
    "@type": "Person",
    "@id": PERSON_ID,
    name: "Denise Rodriguez Dao",
    givenName: "Denise",
    familyName: "Rodriguez Dao",
    url: `${SITE_URL}/about`,
    image: `${SITE_URL}/founder.jpg`,
    jobTitle: "Writer, Business Immigration Consultant",
    description:
      "Denise Rodriguez Dao writes The Incurable Humanist, a weekly newsletter on grief, migration, and art. She is a business immigration consultant working with artists, collectors, entrepreneurs, and leaders across art and entertainment.",
    knowsAbout: ["Grief", "Migration", "Art", "Latin American Art", "Diaspora"],
    alumniOf: [
      { "@type": "EducationalOrganization", name: "Christie's Education, New York" },
      { "@type": "EducationalOrganization", name: "Andrés Bello Catholic University" },
    ],
    sameAs: SAME_AS,
  };
}

export function websiteNode() {
  return {
    "@type": "WebSite",
    "@id": WEBSITE_ID,
    url: SITE_URL,
    name: "The Incurable Humanist",
    description: POSITIONING,
    publisher: { "@id": PERSON_ID },
    inLanguage: "en-US",
  };
}

export function breadcrumbNode(items) {
  return {
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: `${SITE_URL}${item.path}`,
    })),
  };
}

export function articleNode(input) {
  return {
    "@type": "Article",
    // Stable node identity. Without an @id, the prerendered graph and the
    // runtime graph SEO.tsx swaps in describe two unrelated Article entities
    // rather than one.
    "@id": `${input.url}#article`,
    headline: input.title,
    url: input.url,
    ...(input.description ? { description: input.description } : {}),
    ...(input.published ? { datePublished: toIsoUtc(input.published) } : {}),
    ...(input.modified ? { dateModified: toIsoUtc(input.modified) } : {}),
    // Self-hosted essay images are root-relative paths; schema.org consumers
    // read these detached from the page, so they must be absolute.
    ...(input.image
      ? { image: input.image.startsWith("/") ? `${SITE_URL}${input.image}` : input.image }
      : {}),
    author: { "@id": PERSON_ID },
    publisher: { "@id": PERSON_ID },
    mainEntityOfPage: input.url,
    isPartOf: { "@id": WEBSITE_ID },
  };
}

// Moved verbatim from prerender.mjs, which was its only producer. The /speak
// topic pages are evergreen offerings, not dated occurrences, so Service is
// correct here and Event would be wrong (Event requires a startDate/location
// per instance).
export function serviceNode({ title, url, blurb }) {
  return {
    "@type": "Service",
    serviceType: "Speaking Engagement",
    name: title,
    description: blurb,
    provider: { "@id": PERSON_ID },
    url,
  };
}

/**
 * Normalize a backend timestamp to UTC with a Z designator.
 *
 * D1 stores datetimes as ISO-8601 TEXT (SQLite has no datetime type) and the
 * backend serves naive microsecond values like "2026-08-30T23:52:58.302128".
 * Both schema.org and the sitemap protocol want a W3C Datetime, which requires
 * a timezone designator whenever a time is present. The backend writes UTC, so
 * appending Z is correct rather than a guess.
 *
 * Returns the input unchanged when it already carries a designator, and
 * undefined/null through, so callers can `|| now`.
 */
export function toIsoUtc(value) {
  if (!value) return value;
  const s = String(value);
  if (/[Zz]$|[+-]\d{2}:?\d{2}$/.test(s)) return s;
  return s.replace(" ", "T").replace(/\.\d+$/, "") + "Z";
}

/**
 * Truncate a headline for the <title> tag only.
 *
 * Search results cut around 60 characters and the site suffix costs ~25, so an
 * unbounded `${title} — The Incurable Humanist` overflows badly: 28 of 73
 * essays exceeded 70 characters, the worst at 159. The full headline is kept
 * intact in JSON-LD and OG tags, which have no length limit.
 */
export function pageTitle(headline, suffix = " — The Incurable Humanist", max = 60) {
  const room = max - suffix.length;
  if (headline.length <= room) return headline + suffix;
  return headline.slice(0, room).replace(/\s+\S*$/, "") + "…" + suffix;
}
