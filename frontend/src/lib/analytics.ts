import posthog from 'posthog-js';

// Consent state: analytics.track() is a no-op until granted.
// Marketing pixels (GA4, Meta, TikTok) are only injected after grant — see loadMarketingTags().
let consentGranted = false;

const CONSENT_KEY = 'tih_consent_v1';
const CONSENT_TTL_MS = 365 * 24 * 60 * 60 * 1000; // 12 months (2026 EU rule)

type ConsentRecord = { granted: boolean; timestamp: number };

export function getStoredConsent(): ConsentRecord | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(CONSENT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ConsentRecord;
    if (Date.now() - parsed.timestamp > CONSENT_TTL_MS) return null; // expired
    return parsed;
  } catch {
    return null;
  }
}

export function setConsent(granted: boolean) {
  consentGranted = granted;
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(
      CONSENT_KEY,
      JSON.stringify({ granted, timestamp: Date.now() })
    );
  } catch {}
  if (granted) {
    loadMarketingTags();
    window.dispatchEvent(new CustomEvent('tih:consent-granted'));
  } else {
    window.dispatchEvent(new CustomEvent('tih:consent-denied'));
  }
}

export function hasConsent(): boolean {
  return consentGranted;
}

// Initialize consent state from storage — called once on app boot.
export function bootConsent() {
  const stored = getStoredConsent();
  if (stored?.granted) {
    consentGranted = true;
    loadMarketingTags();
  }
}

// TODO(setup): replace pixel IDs when TikTok pixel is created.
const GA4_ID = 'G-E0YFH2FWLN';
const META_PIXEL_ID = '809214198133257';
const TIKTOK_PIXEL_ID = 'REPLACE_WITH_TIKTOK_PIXEL_ID';

let marketingTagsLoaded = false;

function loadMarketingTags() {
  if (marketingTagsLoaded || typeof window === 'undefined') return;
  marketingTagsLoaded = true;

  // Google Analytics (gtag.js)
  const gaScript = document.createElement('script');
  gaScript.async = true;
  gaScript.src = `https://www.googletagmanager.com/gtag/js?id=${GA4_ID}`;
  document.head.appendChild(gaScript);
  (window as any).dataLayer = (window as any).dataLayer || [];
  function gtag(...args: any[]) {
    (window as any).dataLayer.push(args);
  }
  (window as any).gtag = gtag;
  gtag('js', new Date());
  gtag('config', GA4_ID);

  // Meta Pixel
  (function (f: any, b: Document, e: string, v: string) {
    if (f.fbq) return;
    const n: any = (f.fbq = function () {
      n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
    });
    if (!f._fbq) f._fbq = n;
    n.push = n;
    n.loaded = true;
    n.version = '2.0';
    n.queue = [];
    const t = b.createElement(e) as HTMLScriptElement;
    t.async = true;
    t.src = v;
    const s = b.getElementsByTagName(e)[0];
    s.parentNode!.insertBefore(t, s);
  })(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
  (window as any).fbq('init', META_PIXEL_ID);
  (window as any).fbq('track', 'PageView');

  // TikTok Pixel — Dec 2025 update enables organic attribution.
  if (TIKTOK_PIXEL_ID && TIKTOK_PIXEL_ID !== 'REPLACE_WITH_TIKTOK_PIXEL_ID') {
    (function (w: any, d: Document, t: string) {
      w.TiktokAnalyticsObject = t;
      const ttq = (w[t] = w[t] || []);
      ttq.methods = [
        'page','track','identify','instances','debug','on','off','once','ready','alias','group','enableCookie','disableCookie',
      ];
      ttq.setAndDefer = function (t: any, e: string) {
        t[e] = function () {
          t.push([e].concat(Array.prototype.slice.call(arguments, 0)));
        };
      };
      for (let i = 0; i < ttq.methods.length; i++) ttq.setAndDefer(ttq, ttq.methods[i]);
      ttq.instance = function (t: string) {
        const e = ttq._i[t] || [];
        for (let n = 0; n < ttq.methods.length; n++) ttq.setAndDefer(e, ttq.methods[n]);
        return e;
      };
      ttq.load = function (e: string, n?: any) {
        const r = 'https://analytics.tiktok.com/i18n/pixel/events.js';
        ttq._i = ttq._i || {};
        ttq._i[e] = [];
        ttq._i[e]._u = r;
        ttq._t = ttq._t || {};
        ttq._t[e] = +new Date();
        ttq._o = ttq._o || {};
        ttq._o[e] = n || {};
        const o = d.createElement('script') as HTMLScriptElement;
        o.type = 'text/javascript';
        o.async = true;
        o.src = r + '?sdkid=' + e + '&lib=' + t;
        const a = d.getElementsByTagName('script')[0];
        a.parentNode!.insertBefore(o, a);
      };
      ttq.load(TIKTOK_PIXEL_ID);
      ttq.page();
    })(window, document, 'ttq');
  }
}

// Mirror a subset of PostHog conversion events into GA4 / Meta / TikTok so
// each platform gets attribution for the same signup / booking.
function mirrorConversionEvent(eventName: string, properties?: Record<string, any>) {
  if (!consentGranted || typeof window === 'undefined') return;
  const w = window as any;
  const shouldMirror =
    eventName === 'newsletter_signup' || eventName === 'speaker_inquiry';
  if (!shouldMirror) return;

  if (w.gtag) {
    w.gtag('event', eventName, properties || {});
  }
  if (w.fbq) {
    w.fbq('trackCustom', eventName, properties || {});
  }
  if (w.ttq) {
    // TikTok "SubmitForm" is the closest standard event for a newsletter signup.
    w.ttq.track(eventName === 'newsletter_signup' ? 'SubmitForm' : 'Contact', properties || {});
  }
}

// PostHog utility functions — consent-gated.
export const analytics = {
  identify: (userId: string, traits?: Record<string, any>) => {
    if (typeof window === 'undefined' || !consentGranted) return;
    posthog.identify(userId, traits);
  },

  track: (eventName: string, properties?: Record<string, any>) => {
    if (typeof window === 'undefined') return;
    if (!consentGranted) return;
    posthog.capture(eventName, properties);
    mirrorConversionEvent(eventName, properties);
  },

  reset: () => {
    if (typeof window === 'undefined') return;
    posthog.reset();
  },

  setUserProperties: (properties: Record<string, any>) => {
    if (typeof window === 'undefined' || !consentGranted) return;
    posthog.people.set(properties);
  },

  pageView: (pageName?: string) => {
    if (typeof window === 'undefined' || !consentGranted) return;
    posthog.capture('$pageview', {
      page_name: pageName,
      page_url: window.location.href,
    });
  },
};

// Common event names for consistency.
export const ANALYTICS_EVENTS = {
  PAGE_VIEW: 'page_view',
  CONTACT_FORM_SUBMIT: 'contact_form_submit',
  CONTACT_FORM_ERROR: 'contact_form_error',
  NEWSLETTER_SIGNUP: 'newsletter_signup',
  EXTERNAL_LINK_CLICK: 'external_link_click',
  SOCIAL_LINK_CLICK: 'social_link_click',
  PRESS_ARTICLE_CLICK: 'press_article_click',
  SPEAKER_INQUIRY: 'speaker_inquiry',
  ESSAY_CLICK: 'essay_click',
  BIO_LINK_CLICK: 'bio_link_click',
  SECTION_VIEW: 'section_view',
  SCROLL_TO_BOTTOM: 'scroll_to_bottom',
  REFERRAL_SHARE_CLICK: 'referral_share_click',
  LEAD_MAGNET_CONFIRMED: 'lead_magnet_confirmed',
  ESSAY_SCROLL_75: 'essay_scroll_75',
  ESSAY_READ_COMPLETE: 'essay_read_complete',
} as const;

export type AnalyticsEvent = typeof ANALYTICS_EVENTS[keyof typeof ANALYTICS_EVENTS];
