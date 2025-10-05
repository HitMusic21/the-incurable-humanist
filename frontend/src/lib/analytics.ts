import posthog from 'posthog-js';

// PostHog utility functions
export const analytics = {
  // Identify a user
  identify: (userId: string, traits?: Record<string, any>) => {
    if (typeof window !== 'undefined') {
      posthog.identify(userId, traits);
    }
  },

  // Track custom events
  track: (eventName: string, properties?: Record<string, any>) => {
    if (typeof window !== 'undefined') {
      posthog.capture(eventName, properties);
    }
  },

  // Reset user session (useful for logout)
  reset: () => {
    if (typeof window !== 'undefined') {
      posthog.reset();
    }
  },

  // Set user properties
  setUserProperties: (properties: Record<string, any>) => {
    if (typeof window !== 'undefined') {
      posthog.people.set(properties);
    }
  },

  // Page view tracking (automatic with PostHog, but can be called manually)
  pageView: (pageName?: string) => {
    if (typeof window !== 'undefined') {
      posthog.capture('$pageview', {
        page_name: pageName,
        page_url: window.location.href,
      });
    }
  },
};

// Common event names for consistency
export const ANALYTICS_EVENTS = {
  // Navigation
  PAGE_VIEW: 'page_view',
  
  // Contact & Forms
  CONTACT_FORM_SUBMIT: 'contact_form_submit',
  CONTACT_FORM_ERROR: 'contact_form_error',
  NEWSLETTER_SIGNUP: 'newsletter_signup',
  
  // User interactions
  EXTERNAL_LINK_CLICK: 'external_link_click',
  SOCIAL_LINK_CLICK: 'social_link_click',
  PRESS_ARTICLE_CLICK: 'press_article_click',
  
  // Content engagement
  SECTION_VIEW: 'section_view',
  SCROLL_TO_BOTTOM: 'scroll_to_bottom',
} as const;

export type AnalyticsEvent = typeof ANALYTICS_EVENTS[keyof typeof ANALYTICS_EVENTS];