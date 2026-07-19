// Central UTM tagging + capture helper.
// Rule: only for OUTBOUND links. Never tag internal navigation (breaks GA4 session attribution).
// All values must be lowercase — GA4 is case-sensitive.

export type UtmSource =
  | "website"
  | "tiktok"
  | "instagram"
  | "facebook"
  | "youtube"
  | "linkedin"
  | "x"
  | "substack"
  | "newsletter"
  | "email"
  | "press"
  | "bio-link";

export type UtmMedium =
  | "organic-social"
  | "paid-social"
  | "email"
  | "bio-link"
  | "referral"
  | "cta";

export type UtmParams = {
  source: UtmSource;
  medium: UtmMedium;
  campaign?: string;
  content?: string;
};

/**
 * Append lowercase UTM params to an outbound URL. Preserves existing query.
 * Silently returns the input unchanged if it isn't parseable as a URL.
 */
export function withUTM(url: string, params: UtmParams): string {
  try {
    const u = new URL(url);
    u.searchParams.set("utm_source", params.source.toLowerCase());
    u.searchParams.set("utm_medium", params.medium.toLowerCase());
    if (params.campaign) u.searchParams.set("utm_campaign", params.campaign.toLowerCase());
    if (params.content) u.searchParams.set("utm_content", params.content.toLowerCase());
    return u.toString();
  } catch {
    return url;
  }
}

// -----------------------------------------------------------------------------
// Incoming UTM capture — persist attribution across a browsing session so it
// rides along on the lead-capture POST even if the user browses a few pages
// before subscribing.
// -----------------------------------------------------------------------------

export type StoredUtm = {
  source: string | null;
  medium: string | null;
  campaign: string | null;
  content: string | null;
  term: string | null;
};

const STORAGE_KEY = "tih_utm";

const KNOWN_SOURCES = new Set<string>([
  "website", "tiktok", "instagram", "facebook", "youtube", "linkedin",
  "x", "substack", "newsletter", "email", "press", "bio-link",
]);

/**
 * Read UTM params off `window.location.search` and persist them for the
 * lifetime of the browser session. Safe to call multiple times — later
 * captures overwrite earlier ones (last-touch attribution).
 *
 * No-op on SSR / when sessionStorage is unavailable.
 */
export function captureIncomingUTMs(): StoredUtm | null {
  if (typeof window === "undefined") return null;
  try {
    const params = new URLSearchParams(window.location.search);
    const source = params.get("utm_source");
    const medium = params.get("utm_medium");
    const campaign = params.get("utm_campaign");
    const content = params.get("utm_content");
    const term = params.get("utm_term");

    // Only persist if at least one param is present — don't clobber a prior
    // capture with an empty landing.
    if (!source && !medium && !campaign && !content && !term) {
      return getStoredUTMs();
    }

    if (source && import.meta.env.DEV && !KNOWN_SOURCES.has(source.toLowerCase())) {
      console.warn(
        `[utm] Unknown utm_source="${source}". Add to KNOWN_SOURCES in src/lib/utm.ts.`
      );
    }

    const stored: StoredUtm = { source, medium, campaign, content, term };
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    return stored;
  } catch {
    return null;
  }
}

export function getStoredUTMs(): StoredUtm | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StoredUtm;
  } catch {
    return null;
  }
}
