// Type declarations for schemaNodes.mjs — the runtime source lives in
// schemaNodes.mjs so Node build scripts (prerender, generate-sitemap) can
// import it without a TS toolchain or Vite's `@/` alias.

export type SchemaNode = Record<string, unknown>;

export type BreadcrumbItem = { name: string; path: string };

export type ArticleNodeInput = {
  title: string;
  url: string;
  description?: string;
  published?: string;
  modified?: string;
  image?: string;
};

export type ServiceNodeInput = {
  title: string;
  url: string;
  blurb?: string;
};

export const SITE_URL: string;
export const PERSON_ID: string;
export const WEBSITE_ID: string;
export const POSITIONING: string;
export const SAME_AS: readonly string[];

export function personNode(): SchemaNode;
export function websiteNode(): SchemaNode;
export function breadcrumbNode(items: BreadcrumbItem[]): SchemaNode;
export function articleNode(input: ArticleNodeInput): SchemaNode;
export function serviceNode(input: ServiceNodeInput): SchemaNode;

export function toIsoUtc(value: string): string;
export function toIsoUtc(value: undefined | null): undefined;

export function pageTitle(headline: string, suffix?: string, max?: number): string;
