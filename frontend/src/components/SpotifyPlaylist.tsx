import { useEffect, useState } from "react";
import { getStoredConsent } from "@/lib/analytics";
import { useAnalytics } from "@/hooks/useAnalytics";

type Props = {
  playlistId: string;
  /** Accessible name for the player. Should name the playlist, not just "Spotify". */
  title: string;
  /** 352 = full playlist view, 152 = compact single row. Spotify's own values. */
  height?: number;
};

/**
 * Spotify playlist embed behind a click-to-load facade.
 *
 * The iframe is NOT rendered until the reader asks for it. Loading it eagerly
 * pulls in Spotify's player and its cookies on every page view, before anyone
 * has interacted — the same category of third-party tag that ConsentBanner
 * gates for GA4/Meta/TikTok, so it follows the same rule. It also keeps a few
 * hundred KB of third-party JS off a page most visitors scroll past.
 *
 * Readers who have already granted consent skip the facade entirely; the
 * embed loads as normal. Consent changes are picked up live via the
 * `tih:consent-*` events that setConsent() already dispatches.
 */
export default function SpotifyPlaylist({ playlistId, title, height = 352 }: Props) {
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

  if (loaded) {
    return (
      /*
        Attributes mirror what Spotify's oEmbed endpoint returns for this
        playlist. Do not trim them: dropping `encrypted-media` silently
        downgrades the player to 30-second previews — a console warning, not an
        error, so it is easy to ship broken.
      */
      <iframe
        src={`https://open.spotify.com/embed/playlist/${playlistId}`}
        title={title}
        width="100%"
        height={height}
        className="w-full rounded-xl border-0"
        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
        allowFullScreen
        loading="lazy"
      />
    );
  }

  return (
    <button
      type="button"
      onClick={() => {
        track(events.EXTERNAL_LINK_CLICK, { destination: "spotify", placement: "listen-playlist" });
        setLoaded(true);
      }}
      style={{ minHeight: height }}
      className="group flex w-full cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-line bg-surface px-6 py-10 text-center transition-colors hover:border-accent/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
      aria-label={`Load ${title}. Playing loads content from Spotify, which sets its own cookies.`}
    >
      <span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent2 text-white transition group-hover:brightness-105">
        {/* Play triangle — matches the SVG-not-emoji rule in CLAUDE.md. */}
        <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6 translate-x-[2px]" aria-hidden="true">
          <path d="M8 5v14l11-7z" />
        </svg>
      </span>
      <span className="font-serif text-[20px] md:text-[22px] text-ink">{title}</span>
      <span className="max-w-sm text-[14px] leading-relaxed text-muted-ink">
        Loads the player from Spotify, which sets its own cookies.
      </span>
    </button>
  );
}
