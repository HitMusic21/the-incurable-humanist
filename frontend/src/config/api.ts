// API base URL + endpoint map.
//
// Prod: `/api` — nginx (see frontend/nginx.conf.template) proxies /api/* to
//       the backend Cloud Run service, stripping the /api prefix. So calling
//       "/api/leads/subscribe" from the SPA hits the backend at /leads/subscribe.
// Dev:  `http://localhost:8000` — Vite dev server → local backend directly, no
//       proxy. Endpoint strings don't include the /api prefix, so dev calls
//       hit the backend's canonical routes (/leads/subscribe, /auth/login, …).
// Override: VITE_API_URL wins in either environment (useful for pointing at
//       staging or a custom port).

const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (import.meta.env.PROD) {
    return '/api';
  }
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();

export const API_CONFIG = {
  baseUrl: API_BASE_URL,
  endpoints: {
    newsletter: {
      articles: "/newsletter/articles",
    },
    auth: {
      register: "/auth/register",
      login: "/auth/login",
    },
    leads: {
      subscribe: "/leads/subscribe",
    },
    stories: {
      list: "/stories",
      detail: (slug: string) => `/stories/${encodeURIComponent(slug)}`,
      adminById: (id: number | string) => `/stories/id/${encodeURIComponent(String(id))}`,
    },
  },
};

// Server-side story shape returned by /stories endpoints.
export type StoryPublic = {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  meta_description: string | null;
  cover_image_url: string | null;
  canonical_url: string | null;
  // Substack permalink this essay was synced from. Drives the "first published
  // on Substack" credit line — NOT the canonical URL, which stays on-site.
  source_url: string | null;
  read_time_minutes: number | null;
  status: string;
  published_at: string | null;
  updated_at: string;
};

export type StoryDetail = StoryPublic & {
  content: string;
  content_warning: string | null;
  view_count: number;
};

export type StoryListResponse = {
  stories: StoryPublic[];
  total_count: number;
};

export type NewsletterArticle = {
  title: string;
  link: string;
  description: string;
  published: string;
};

export type NewsletterArticlesResponse = {
  articles: NewsletterArticle[];
};
