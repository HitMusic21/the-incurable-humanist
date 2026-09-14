import { useEffect, useState, type ReactNode } from "react";
import { getStoredConsent } from "@/lib/analytics";
import { useAnalytics } from "@/hooks/useAnalytics";

type Props = {
  /** Rendered only once the reader has asked for (or already consented to) the embed. */
  children: ReactNode;
  /** Shown on the facade button. Should name the thing, not the vendor. */
  title: string;
  /** Vendor name as it appears in the cookie warning, e.g. "Spotify", "YouTube". */
  vendor: string;
  /** Reserves the embed's height so swapping in the iframe does not shift layout. */
  minHeight: number;
  /** Distinguishes facades in analytics — e.g. "listen-playlist", "speak-reel". */
  placement: string;
  /** Value sent as the `destination` property. Defaults to a lowercased vendor. */
  destination?: string;
};

/**
 * Click-to-load gate for a third-party embed.
 *
 * The iframe is NOT rendered until the reader asks for it. Loading it eagerly
 * pulls in the vendor's player and its cookies on every page view, before
 * anyone has interacted — the same category of third-party tag that
 * ConsentBanner gates for GA4/Meta/TikTok, so it follows the same rule. It also
 * keeps a few hundred KB of third-party JS off pages most visitors scroll past.
 *
 * Readers who have already granted consent skip the facade entirely; the embed
 * loads as normal. Consent changes are picked up live via the `tih:consent-*`
 * events that setConsent() already dispatches.
 *
 * Extracted from SpotifyPlaylist when the /speak YouTube reel needed the same
 * behaviour (Sep 2026) — the gating logic was never Spotify-specific, and two
 * copies would drift the moment the consent rules changed.
 */
export default function ConsentFacade({
  children,
  title,
  vendor,
  minHeight,
  placement,
  destination,
}: Props) {
  // Reads storage rather than hasConsent(): that returns an in-memory flag
  // which App's bootConsent() effect populates *after* this initializer runs,
  // so a returning reader who already consented would still see the facade.
  const [loaded, setLoaded] = useState(() => getStoredConsent()?.granted === true);
  const { track, events } = useAnalytics();

  useEffect(() => {
    const grant = () => setLoaded(true);
    const deny = () => setLoaded(false);
    window.addEventListener("tih:consent-granted", grant);
    window.addEventListener("tih:consent-denied", deny);
    return () => {
      window.removeEventListener("tih:consent-granted", grant);
      window.removeEventListener("tih:consent-denied", deny);
    };
  }, []);

  if (loaded) return <>{children}</>;

  return (
    <button
      type="button"
      onClick={() => {
        track(events.EXTERNAL_LINK_CLICK, {
          destination: destination ?? vendor.toLowerCase(),
          placement,
        });
        setLoaded(true);
      }}
      style={{ minHeight }}
      className="group flex w-full cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-line bg-surface px-6 py-10 text-center transition-colors hover:border-accent/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
      aria-label={`Load ${title}. Playing loads content from ${vendor}, which sets its own cookies.`}
    >
      <span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent2 text-white transition group-hover:brightness-105">
        {/* Play triangle — matches the SVG-not-emoji rule in CLAUDE.md. */}
        <svg
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-6 w-6 translate-x-[2px]"
          aria-hidden="true"
        >
          <path d="M8 5v14l11-7z" />
        </svg>
      </span>
      <span className="font-serif text-[20px] md:text-[22px] text-ink">{title}</span>
      <span className="max-w-sm text-[14px] leading-relaxed text-muted-ink">
        Loads the player from {vendor}, which sets its own cookies.
      </span>
    </button>
  );
}
