export const API_CONFIG = {
  baseUrl: "http://localhost:8000",
  endpoints: {
    newsletter: {
      articles: "/newsletter/articles",
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
