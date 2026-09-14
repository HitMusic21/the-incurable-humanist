import { describe, expect, it } from "vitest";

// Vite's ?raw suffix inlines the file as a string at transform time. Used
// instead of node:fs so this test needs no Node type declarations — the
// browser tsconfig that covers src/ does not include them.
import indexHtml from "../../../index.html?raw";

import {
  articleNode,
  breadcrumbNode,
  pageTitle,
  personNode,
  serviceNode,
  toIsoUtc,
  websiteNode,
  WEBSITE_ID,
} from "../schemaNodes.mjs";

describe("entity @ids", () => {
  it("WEBSITE_ID has no trailing slash before the fragment", () => {
    // index.html once hardcoded ".com/#website" while schema.ts and
    // prerender.mjs emitted ".com#website". Different @id strings mean
    // consumers see two unrelated WebSite entities instead of one.
    expect(WEBSITE_ID).toBe("https://theincurablehumanist.com#website");
    expect(WEBSITE_ID).not.toContain(".com/#");
  });

  it("websiteNode and Article isPartOf reference the same WebSite", () => {
    const article = articleNode({ title: "T", url: "https://x/e/s" });
    expect((article.isPartOf as { "@id": string })["@id"]).toBe(websiteNode()["@id"]);
  });

  it("articleNode carries its own @id", () => {
    // Without one, the prerendered graph and the runtime graph SEO.tsx swaps
    // in describe two unrelated Article entities.
    expect(articleNode({ title: "T", url: "https://x/e/s" })["@id"]).toBe(
      "https://x/e/s#article"
    );
  });
});

describe("personNode", () => {
  it("carries the full E-E-A-T signal set", () => {
    // prerender.mjs used to emit a stub with only @type/@id/name/url, and
    // because it overwrites index.html's block, every prerendered page shipped
    // a Person with no sameAs. Verified live before the fix: /about's Person
    // had exactly ["@id","@type","name","url"].
    const p = personNode();
    expect(p.sameAs).toHaveLength(8);
    expect(p.jobTitle).toBeTruthy();
    expect(p.description).toBeTruthy();
    expect(p.knowsAbout).toBeTruthy();
    expect(p.alumniOf).toHaveLength(2);
    expect(p.image).toContain("https://");
  });

  it("is referenced as author and publisher by articleNode", () => {
    const a = articleNode({ title: "T", url: "https://x/e/s" });
    expect((a.author as { "@id": string })["@id"]).toBe(personNode()["@id"]);
    expect((a.publisher as { "@id": string })["@id"]).toBe(personNode()["@id"]);
  });
});

describe("toIsoUtc", () => {
  it("appends Z to a naive backend timestamp", () => {
    // The backend serves naive microsecond values; 73 of 83 sitemap <lastmod>
    // entries shipped without a timezone, which is not valid W3C Datetime.
    expect(toIsoUtc("2026-08-30T23:52:58.302128")).toBe("2026-08-30T23:52:58Z");
  });

  it("is idempotent on values that already have a designator", () => {
    expect(toIsoUtc("2026-08-30T23:52:58Z")).toBe("2026-08-30T23:52:58Z");
    expect(toIsoUtc("2026-08-30T23:52:58+00:00")).toBe("2026-08-30T23:52:58+00:00");
  });

  it("normalizes a SQLite space separator", () => {
    expect(toIsoUtc("2026-08-30 23:52:58")).toBe("2026-08-30T23:52:58Z");
  });

  it("passes falsy values through so callers can fall back", () => {
    expect(toIsoUtc(undefined as never)).toBeUndefined();
  });

  it("flows through articleNode dates", () => {
    const a = articleNode({
      title: "T",
      url: "https://x/e/s",
      published: "2026-08-25T12:01:37.123456",
      modified: "2026-08-30T23:52:58.302128",
    });
    expect(a.datePublished).toBe("2026-08-25T12:01:37Z");
    expect(a.dateModified).toBe("2026-08-30T23:52:58Z");
  });
});

describe("pageTitle", () => {
  it("leaves a short headline intact", () => {
    expect(pageTitle("Neon Summer Skin")).toBe("Neon Summer Skin — The Incurable Humanist");
  });

  it("truncates a long headline on a word boundary", () => {
    // 28 of 73 essay titles overflowed once the suffix was appended; the worst
    // reached 159 characters.
    const long =
      "All the Way to the River feels empty because what Elizabeth Gilbert describes is liquid love";
    const out = pageTitle(long);
    expect(out.length).toBeLessThanOrEqual(61);
    expect(out).toContain("…");
    expect(out.endsWith(" — The Incurable Humanist")).toBe(true);
    // Cut on a word boundary: the kept text is a whole-word prefix of the
    // original, never a word sliced mid-way.
    const kept = out.slice(0, out.indexOf("…"));
    expect(long.startsWith(kept)).toBe(true);
    expect(long[kept.length]).toBe(" ");
  });

  it("never truncates the schema headline", () => {
    const long = "A".repeat(200);
    expect(articleNode({ title: long, url: "https://x/e/s" }).headline).toBe(long);
  });
});

describe("serviceNode", () => {
  it("describes a speaking engagement provided by the Person", () => {
    const s = serviceNode({ title: "Grief", url: "https://x/speak/g", blurb: "b" });
    expect(s["@type"]).toBe("Service");
    expect(s.serviceType).toBe("Speaking Engagement");
    expect((s.provider as { "@id": string })["@id"]).toBe(personNode()["@id"]);
  });
});

describe("breadcrumbNode", () => {
  it("numbers positions from 1 and absolutizes paths", () => {
    const b = breadcrumbNode([
      { name: "Home", path: "/" },
      { name: "Writing", path: "/archive" },
    ]);
    const items = b.itemListElement as Array<{ position: number; item: string }>;
    expect(items[0].position).toBe(1);
    expect(items[1].item).toBe("https://theincurablehumanist.com/archive");
  });
});

describe("index.html drift guard", () => {
  it("the hardcoded no-JS block still matches the builders", () => {
    // index.html carries a hand-written JSON-LD block as the no-JS fallback for
    // `/` (Vite cannot template it without a plugin). It is the one copy that
    // cannot import schemaNodes.mjs, so this test is what stops it drifting —
    // which is exactly how the trailing-slash @id bug survived.
    const match = indexHtml.match(/id="tih-jsonld-page"[^>]*>([\s\S]*?)<\/script>/);
    expect(match).toBeTruthy();

    const graph = JSON.parse(match![1])["@graph"] as Array<Record<string, unknown>>;
    const person = graph.find((n) => n["@type"] === "Person")!;
    const website = graph.find((n) => n["@type"] === "WebSite")!;

    expect(website["@id"]).toBe(websiteNode()["@id"]);
    expect(website.url).toBe(websiteNode().url);
    expect(person["@id"]).toBe(personNode()["@id"]);
    expect(person.sameAs).toEqual(personNode().sameAs);
    expect(person.jobTitle).toBe(personNode().jobTitle);
    expect(person.description).toBe(personNode().description);
  });
});
