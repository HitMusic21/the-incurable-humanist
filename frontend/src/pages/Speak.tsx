import Card from "@/components/Card";
import ConsentFacade from "@/components/ConsentFacade";
import SectionTitle from "@/components/SectionTitle";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";
import { useAnalytics } from "@/hooks/useAnalytics";
import { articleGraphForSite } from "@/lib/schema";

export default function Speak() {
  const { track, events } = useAnalytics();
  const bookingSubject = encodeURIComponent("Speaking inquiry — The Incurable Humanist");
  const bookingBody = encodeURIComponent(
    "Hi Denise,\n\nI'd like to invite you to speak at [event / organization] on [date]. A few details:\n\n• Audience: \n• Format: \n• Location: \n• Budget: \n\nLooking forward.\n"
  );
  // Denise redirected speaking enquiries to the general inbox (Sep 2026);
  // SITE.email already held that address.
  const mailto = `mailto:${SITE.email}?subject=${bookingSubject}&body=${bookingBody}`;

  return (
    <>
      <SEO
        title="Speaking — Denise Rodriguez Dao | The Incurable Humanist"
        description="Denise Rodriguez Dao speaks on grief, migration, art, and the Latin American diaspora. Booking cultural centers, universities, and literary events for Fall 2026 and Spring 2027."
        canonical="https://theincurablehumanist.com/speak"
        jsonLd={articleGraphForSite({ path: "/speak", pageName: "Speaking" })}
      />

      <SectionTitle>Speaking</SectionTitle>

      <section className="container mt-8 max-w-4xl">
        <p className="text-center text-[16px] md:text-[17px] italic text-muted-ink max-w-2xl mx-auto leading-relaxed">
          {/* AEO-quotable intro paragraph. */}
          Denise Rodriguez Dao is a writer and immigration consultant based in New
          York. She
          speaks on grief, migration, art, and the Latin American diaspora.
        </p>
        <p className="mt-3 text-center text-[14px] text-accent font-medium">
          {SITE.speaker.tagline}
        </p>
      </section>

      {/* Above-fold booking + reel.

          items-start, not the grid default of stretch: with the press-kit
          button, the response-time line and everything below this row removed
          (Sep 2026), stretching left the shorter card with a tall band of
          empty cream below its content. Each card is now its own height. */}
      <section className="container mt-12 max-w-6xl">
        <div className="grid items-start gap-8 md:grid-cols-[1.4fr_1fr]">
          <Card className="p-8 md:p-10">
            <h2 className="font-serif text-accent text-[28px] md:text-[34px] leading-tight mb-4">
              Bring The Incurable Humanist to your stage.
            </h2>
            <p className="text-[16px] md:text-[17px] text-muted-ink leading-relaxed mb-6">
              Talks, panels, and readings — tailored to your audience. Denise combines the
              lived material of her essays with a lawyer's clarity and a curator's eye.
            </p>

            <div className="flex flex-col sm:flex-row flex-wrap gap-3">
              <a
                href={mailto}
                onClick={() =>
                  track(events.SPEAKER_INQUIRY, { placement: "speak-hero-mailto" })
                }
                aria-label={`Email ${SITE.email} — Speaking inquiry`}
                className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 active:brightness-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent2 transition font-medium whitespace-nowrap cursor-pointer"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.75"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4"
                  aria-hidden="true"
                >
                  <rect x="3" y="5" width="18" height="14" rx="2" />
                  <path d="m3 7 9 6 9-6" />
                </svg>
                Email Denise
              </a>
              {/* The "Press kit (PDF)" button was removed at Denise's request
                  (Sep 2026). It had pointed at /press-kit.pdf, an asset that
                  was never added, so it 404'd for its whole life. */}
            </div>

            {/* "Response within 3 business days" was removed at Denise's
                request. The address itself stays: the pill carries the short
                label "Email Denise", and the UI design system requires the
                full address be readable somewhere outside it. */}
            <p className="mt-4 text-[13px] text-muted-ink">
              <a
                href={`mailto:${SITE.email}`}
                className="underline decoration-muted-ink/40 underline-offset-2 hover:text-accent2 hover:decoration-accent2 transition-colors"
              >
                {SITE.email}
              </a>
            </p>
          </Card>

          {/* Voices for Venezuela / reel */}
          <Card className="p-8 md:p-10 bg-surface/70">
            <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-3 font-medium">
              Speaker reel
            </div>
            {/* Gated the same way as the Spotify player on /listen — an eager
                YouTube iframe would set third-party cookies on page view, which
                is exactly what ConsentBanner exists to prevent. */}
            {SITE.speaker.voicesForVenezuelaUrl && (
              <ConsentFacade
                title="Denise Rodriguez Dao — Voices for Venezuela"
                vendor="YouTube"
                minHeight={200}
                placement="speak-reel"
              >
                <div className="aspect-video rounded-xl overflow-hidden bg-black/5">
                  <iframe
                    src={SITE.speaker.voicesForVenezuelaUrl}
                    title="Denise Rodriguez Dao — Voices for Venezuela"
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              </ConsentFacade>
            )}
            {/* The caption here read "hosted by [organization / venue]" — an
                unfilled placeholder that was rendering to production. */}
            <p className="mt-4 text-[13px] text-muted-ink italic">
              Featured speaker, Voices for Venezuela.
            </p>
          </Card>
        </div>
      </section>

      {/* Everything that used to sit below the reel was removed at Denise's
          request (Sep 2026): the "Signature topics" grid, the "Read Denise's
          writing first." and "Follow Denise's writing." subscribe CTAs, the
          "About Denise" bio card, and the "Featured in" outlet row.

          NOTE: the topics grid was the ONLY in-site link to the four
          /speak/:topic landing pages. They are still prerendered, still in the
          sitemap and still server-rendered by the Worker, but are now
          orphaned — reachable by URL and search only. Flagged to Denise; if
          that is intended they should be retired properly rather than left
          unlinked. */}
      <div className="pb-20 md:pb-28" />
    </>
  );
}
