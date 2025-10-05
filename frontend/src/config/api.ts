// Detect environment and set API base URL
const getApiBaseUrl = () => {
  // In production, API is served from same domain
  if (import.meta.env.PROD) {
    return '';
  }
  // In development, use localhost backend
  return 'http://localhost:8000';
};

export const API_CONFIG = {
  baseUrl: getApiBaseUrl(),
  endpoints: {
    newsletter: {
      articles: "/api/newsletter/articles",
    },
    auth: {
      register: "/api/auth/register",
      login: "/api/auth/login",
    },
  },
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
