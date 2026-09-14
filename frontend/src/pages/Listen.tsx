import Card from "@/components/Card";
import SectionTitle from "@/components/SectionTitle";
import SpotifyPlaylist from "@/components/SpotifyPlaylist";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";
import { withUTM } from "@/lib/utm";
import { articleGraphForSite } from "@/lib/schema";

export default function Listen() {
  const substackAudioUrl = withUTM(`${SITE.substackUrl}/s/audio`, {
    source: "website",
    medium: "referral",
    campaign: "listen-page",
  });

  return (
    <>
      <SEO
        title="Listen — The Incurable Humanist"
        description="Audio essays by Denise Rodriguez Dao on grief, migration, and art. Plus: a curated Spotify playlist tied to recurring themes in the newsletter."
        canonical="https://theincurablehumanist.com/listen"
        jsonLd={articleGraphForSite({ path: "/listen", pageName: "Listen" })}
      />

      <SectionTitle>Listening</SectionTitle>

      {/* Audio essays */}
      <section className="container mt-14 max-w-4xl">
        <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
          Audio essays
        </h2>
        <Card className="p-8 md:p-10 text-center">
          <p className="text-[16px] text-muted-ink leading-relaxed mb-6">
            Every essay is also available in audio, read by Denise&mdash;whether you prefer
            to read or listen.
          </p>
          <a
            href={substackAudioUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 active:brightness-95 transition font-medium"
          >
            Listen on Substack
          </a>
        </Card>
      </section>

      {/* Spotify playlist — feature-flagged */}
      <section className="container mt-14 max-w-4xl">
        <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
          Playlists
        </h2>
        {SITE.spotifyPlaylistId ? (
          <Card className="p-4 md:p-6">
            <SpotifyPlaylist
              playlistId={SITE.spotifyPlaylistId}
              title="The Incurable Humanist — playlist on Spotify"
            />
          </Card>
        ) : (
          <Card className="p-8 md:p-10 text-center">
            <div className="font-serif text-[20px] md:text-[22px] text-ink mb-2">
              Coming soon
            </div>
            <p className="text-[15px] text-muted-ink leading-relaxed max-w-lg mx-auto">
              A curated playlist tied to the essays — the music that runs alongside the
              writing. It will live here once it's built.
            </p>
          </Card>
        )}
      </section>

      {/* The "New essay every Sunday." subscribe box was removed at Denise's
          request (Aug 2026). The page now ends after the playlist. */}
      <div className="pb-20 md:pb-28" />
    </>
  );
}
