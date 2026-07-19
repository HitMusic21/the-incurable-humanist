import { Link } from "react-router-dom";
import Card from "@/components/Card";
import SectionTitle from "@/components/SectionTitle";
import SubscribeCTA from "@/components/SubscribeCTA";
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
  const mailto = `mailto:${SITE.bookingEmail}?subject=${bookingSubject}&body=${bookingBody}`;

  return (
    <>
      <SEO
        title="Speak — Denise Rodriguez Dao | The Incurable Humanist"
        description="Denise Rodriguez Dao speaks on grief, migration, art, and the Latin American diaspora. Booking cultural centers, universities, and literary events for Fall 2026 and Spring 2027."
        canonical="https://theincurablehumanist.com/speak"
        jsonLd={articleGraphForSite({ path: "/speak", pageName: "Speak" })}
      />

      <SectionTitle>Speak</SectionTitle>

      <section className="container mt-8 max-w-4xl">
        <p className="text-center text-[16px] md:text-[17px] italic text-muted-ink max-w-2xl mx-auto leading-relaxed">
          {/* AEO-quotable intro paragraph. */}
          Denise Rodriguez Dao is a writer and immigration attorney based in New York. She
          speaks on grief, migration, art, and the Latin American diaspora — for cultural
          centers, literary festivals, universities, and diaspora-adjacent events.
        </p>
        <p className="mt-3 text-center text-[14px] text-accent font-medium">
          {SITE.speaker.tagline}
        </p>
      </section>

      {/* Above-fold booking + reel */}
      <section className="container mt-12 max-w-6xl">
        <div className="grid gap-8 md:grid-cols-[1.4fr_1fr]">
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
                aria-label={`Email ${SITE.bookingEmail} — Speaking inquiry`}
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
              <a
                href={SITE.speaker.pressKitUrl}
                onClick={() =>
                  track(events.SPEAKER_INQUIRY, {
                    placement: "speak-press-kit",
                    action: "download",
                  })
                }
                aria-label="Download press kit (PDF)"
                className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill border border-accent text-accent hover:bg-accent hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent transition font-medium whitespace-nowrap cursor-pointer"
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
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <path d="M7 10l5 5 5-5" />
                  <path d="M12 15V3" />
                </svg>
                Press kit (PDF)
              </a>
            </div>

            <p className="mt-4 text-[13px] text-muted-ink">
              Response within 3 business days ·{" "}
              <a
                href={`mailto:${SITE.bookingEmail}`}
                className="underline decoration-muted-ink/40 underline-offset-2 hover:text-accent2 hover:decoration-accent2 transition-colors"
              >
                {SITE.bookingEmail}
              </a>
            </p>
          </Card>

          {/* Voices for Venezuela / reel */}
          <Card className="p-8 md:p-10 bg-surface/70">
            <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-3 font-medium">
              Speaker reel
            </div>
            {SITE.speaker.voicesForVenezuelaUrl ? (
              <div className="aspect-video rounded-xl overflow-hidden bg-black/5">
                <iframe
                  src={SITE.speaker.voicesForVenezuelaUrl}
                  title="Denise Rodriguez Dao — Voices for Venezuela"
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            ) : (
              <div className="aspect-video rounded-xl bg-white border border-line/60 flex items-center justify-center text-center p-6">
                <div>
                  <div className="font-serif text-[20px] text-ink mb-2">
                    Coming soon
                  </div>
                  <p className="text-[13px] text-muted-ink leading-relaxed max-w-xs mx-auto">
                    Recording from{" "}
                    <em>Voices for Venezuela</em> will live here.
                  </p>
                </div>
              </div>
            )}
            <p className="mt-4 text-[13px] text-muted-ink italic">
              Featured speaker, Voices for Venezuela — hosted by [organization / venue].
            </p>
          </Card>
        </div>
      </section>

      {/* Signature topics — each links to its own SEO landing page. */}
      <section className="container mt-16 max-w-5xl">
        <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
          Signature topics
        </h2>
        <div className="grid gap-6 md:grid-cols-2">
          {SITE.speakingTopics.map((t) => (
            <Card key={t.slug} className="p-6 md:p-8 hover:shadow-[0_16px_40px_rgba(110,85,128,0.12)] transition-shadow">
              <Link to={`/speak/${t.slug}`} className="block group">
                <h3 className="font-serif text-[22px] md:text-[24px] text-ink group-hover:text-accent transition-colors leading-tight mb-2">
                  {t.title}
                </h3>
                <p className="text-[15px] text-muted-ink leading-relaxed">{t.subtitle}</p>
                <span className="mt-3 inline-block text-[13px] text-accent underline decoration-2 decoration-accent/30 group-hover:decoration-accent underline-offset-4">
                  Read more →
                </span>
              </Link>
            </Card>
          ))}
        </div>
      </section>

      {/* Secondary CTA between topics and bio — captures organizers still evaluating. */}
      <section className="container mt-14 max-w-3xl">
        <SubscribeCTA
          variant="inline"
          placement="speak-secondary"
          headline="Read Denise's writing first."
          sub="The essays are the syllabus. Free PDF of the best five, then Sunday-morning delivery."
        />
      </section>

      {/* Bio + credibility */}
      <section className="container mt-16 max-w-4xl">
        <Card className="p-8 md:p-10">
          <h2 className="font-serif text-accent2 text-[24px] md:text-[28px] mb-5">
            About Denise
          </h2>
          <div className="space-y-4 text-[16px] md:text-[17px] leading-relaxed">
            <p>
              Denise Rodriguez Dao is the writer behind <em>The Incurable Humanist</em>, a
              weekly newsletter on grief, migration, and art. She is a foreign attorney at a
              boutique immigration law firm in Manhattan, where she secures visas for artists,
              gallerists, entrepreneurs, and cultural professionals.
            </p>
            <p>
              She previously served as content director, head of logistics, and artist liaison
              at Galería RGR in Mexico City, working with iconic figures of Latin American
              modernism and leading contemporary artists.
            </p>
            <p>
              Denise holds a master's degree in Modern and Contemporary Art and the Market
              from Christie's Education (New York) and a J.D. from Andrés Bello Catholic
              University (Caracas).
            </p>
          </div>
        </Card>
      </section>

      {/* Press logos as trust anchor */}
      <section className="container mt-16 max-w-5xl">
        <h2 className="font-serif text-accent2 text-[20px] md:text-[22px] mb-6 text-center uppercase tracking-[0.18em]">
          Featured in
        </h2>
        <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4 text-muted-ink font-serif italic text-[18px] md:text-[20px]">
          {SITE.press.map((p) => (
            <span key={p.outlet}>{p.outlet}</span>
          ))}
        </div>
      </section>

      {/* Sidebar CTA equivalent — end-of-page subscribe */}
      <section className="container mt-16 max-w-3xl pb-20 md:pb-28">
        <SubscribeCTA
          variant="end-of-post"
          placement="speak-footer"
          headline="Follow Denise's writing."
          sub="Weekly essays on grief, migration, and art. Free."
        />
      </section>
    </>
  );
}
