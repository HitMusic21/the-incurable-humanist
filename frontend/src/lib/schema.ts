// JSON-LD schema builders. Wrap outputs in a single @graph per page.
// Person schema with sameAs solves the "disconnected entity" HCU problem.

import { SITE } from "@/config/site";

const SITE_URL = SITE.siteUrl;
const PERSON_ID = `${SITE_URL}/about#denise`;
const WEBSITE_ID = `${SITE_URL}#website`;

export function personNode() {
  return {
    "@type": "Person",
    "@id": PERSON_ID,
    name: "Denise Rodriguez Dao",
    givenName: "Denise",
    familyName: "Rodriguez Dao",
    url: `${SITE_URL}/about`,
    image: `${SITE_URL}/founder.jpg`,
    jobTitle: "Writer, Immigration Attorney",
    description:
      "Denise Rodriguez Dao writes The Incurable Humanist, a weekly newsletter on grief, migration, and art. She is a foreign attorney at a boutique immigration law firm in Manhattan.",
    knowsAbout: ["Grief", "Migration", "Art", "Latin American Art", "Diaspora"],
    alumniOf: [
      {
        "@type": "EducationalOrganization",
        name: "Christie's Education, New York",
      },
      {
        "@type": "EducationalOrganization",
        name: "Andrés Bello Catholic University",
      },
    ],
    sameAs: [
      SITE.socials.instagram,
      SITE.socials.tiktok,
      SITE.socials.facebook,
      SITE.socials.linkedin,
      SITE.socials.x,
      SITE.substackUrl,
    ].filter(Boolean),
  };
}

export function websiteNode() {
  return {
    "@type": "WebSite",
    "@id": WEBSITE_ID,
    url: SITE_URL,
    name: "The Incurable Humanist",
    description: SITE.positioning,
    publisher: { "@id": PERSON_ID },
    inLanguage: "en-US",
  };
}

export function breadcrumbNode(items: Array<{ name: string; path: string }>) {
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

export type ArticleNodeInput = {
  title: string;
  url: string;
  description?: string;
  published?: string;
  modified?: string;
  image?: string;
};

export function articleNode(input: ArticleNodeInput) {
  return {
    "@type": "Article",
    headline: input.title,
    url: input.url,
    ...(input.description ? { description: input.description } : {}),
    ...(input.published ? { datePublished: input.published } : {}),
    ...(input.modified ? { dateModified: input.modified } : {}),
    ...(input.image ? { image: input.image } : {}),
    author: { "@id": PERSON_ID },
    publisher: { "@id": PERSON_ID },
    mainEntityOfPage: input.url,
    isPartOf: { "@id": WEBSITE_ID },
  };
}

/**
 * Convenience: build a full @graph for a standard page (Person + WebSite + Breadcrumb).
 * Returns an array (never a bare @graph) so the SEO component can concatenate per-page article nodes.
 */
export function articleGraphForSite(page: { path: string; pageName: string }) {
  const items = [{ name: "Home", path: "/" }];
  if (page.path !== "/") {
    items.push({ name: page.pageName, path: page.path });
  }
  return [personNode(), websiteNode(), breadcrumbNode(items)];
}
