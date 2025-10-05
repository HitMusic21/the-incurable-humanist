import { usePostHog } from 'posthog-js/react';
import { analytics, ANALYTICS_EVENTS, type AnalyticsEvent } from '@/lib/analytics';

export function useAnalytics() {
  const posthog = usePostHog();

  const track = (eventName: AnalyticsEvent | string, properties?: Record<string, any>) => {
    analytics.track(eventName, properties);
  };

  const identify = (userId: string, traits?: Record<string, any>) => {
    analytics.identify(userId, traits);
  };

  const reset = () => {
    analytics.reset();
  };

  const setUserProperties = (properties: Record<string, any>) => {
    analytics.setUserProperties(properties);
  };

  const pageView = (pageName?: string) => {
    analytics.pageView(pageName);
  };

  return {
    track,
    identify,
    reset,
    setUserProperties,
    pageView,
    posthog,
    events: ANALYTICS_EVENTS,
  };
}