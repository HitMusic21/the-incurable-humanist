// JSON-LD schema builders. Wrap outputs in a single @graph per page.
// Person schema with sameAs solves the "disconnected entity" HCU problem.
//
// The node builders themselves live in ./schemaNodes.mjs so that the bare-Node
// build scripts (scripts/prerender.mjs, scripts/generate-sitemap.mjs) can
// import the SAME code. They previously kept private copies, which drifted:
// prerender's personNode() lost sameAs/jobTitle/alumniOf, and since it
// overwrites index.html's JSON-LD block, every prerendered page shipped a
// stripped-down Person. This file stays the import site for React code.

export {
  articleNode,
  breadcrumbNode,
  pageTitle,
  personNode,
  serviceNode,
  toIsoUtc,
  websiteNode,
  PERSON_ID,
  SITE_URL,
  WEBSITE_ID,
} from "./schemaNodes.mjs";

export type { ArticleNodeInput, ServiceNodeInput } from "./schemaNodes.mjs";

import { breadcrumbNode, personNode, websiteNode } from "./schemaNodes.mjs";

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
