import ConsentFacade from "@/components/ConsentFacade";

type Props = {
  playlistId: string;
  /** Accessible name for the player. Should name the playlist, not just "Spotify". */
  title: string;
  /** 352 = full playlist view, 152 = compact single row. Spotify's own values. */
  height?: number;
};

/**
 * Spotify playlist embed behind a click-to-load consent facade.
 *
 * The gating behaviour — and why it exists — lives in ConsentFacade, which the
 * /speak YouTube reel shares.
 */
export default function SpotifyPlaylist({ playlistId, title, height = 352 }: Props) {
  return (
    <ConsentFacade
      title={title}
      vendor="Spotify"
      minHeight={height}
      placement="listen-playlist"
    >
      {/*
        Attributes mirror what Spotify's oEmbed endpoint returns for this
        playlist. Do not trim them: dropping `encrypted-media` silently
        downgrades the player to 30-second previews — a console warning, not an
        error, so it is easy to ship broken.
      */}
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
    </ConsentFacade>
  );
}
