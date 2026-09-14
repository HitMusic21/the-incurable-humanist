import SocialIconRow from "@/components/SocialIconRow";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";
import { articleGraphForSite } from "@/lib/schema";

function HeroBlock() {
  return (
    <section className="min-h-screen bg-bg relative overflow-hidden">
      {/* The portrait column is capped at 1.1fr (not 1.5fr) and the whole grid
          is max-w-[1600px] centered. Reason: the source portrait is 1215x1778
          (aspect 0.68) inside an h-screen frame, so object-cover discards
          height as the column grows WIDER than the image's aspect ratio.
          Measured before the cap: 36% of the portrait cropped at 2000px and
          25% at 768px — the face was cut at the chin. object-position cannot
          fix this; it only pans within whatever is left. */}
      <div className="relative min-h-screen mx-auto max-w-[1600px] lg:grid lg:grid-cols-[1.1fr_1fr] lg:items-stretch">
        {/* Portrait Column.
            Below lg the grid is single-column, so the portrait spans the full
            viewport width. On a 768px tablet that frame is wider relative to
            the image's 0.68 aspect than a phone's, so ~25% is cropped.
            REDUCING the height makes this WORSE (measured: 78vh took it to
            41%) because it widens the frame's ratio further. Taller is better
            here — hence min-h-screen rather than a capped height. */}
        <div className="relative h-screen md:min-h-screen lg:h-screen lg:z-10">
          {/* Cap the IMAGE's width on tablet (not its height) and centre it.
              Narrowing the frame moves its ratio back toward the image's 0.68,
              which is what actually recovers the crop; the surrounding column
              still spans full width so the gradients below stay edge-to-edge. */}
          <div className="relative h-full overflow-hidden mx-auto w-full md:max-w-[560px] lg:max-w-none">
            {/* object-position is anchored high so any residual crop comes off
                the bottom (shoulders) rather than cutting the face at the chin. */}
            <img
              src="/founder.jpg"
              alt="Denise Rodriguez Dao, author of The Incurable Humanist, in a close portrait against a dark background"
              className="h-full w-full object-cover object-[center_top] md:object-[center_15%] lg:object-[center_20%]"
            />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-bg/95 lg:to-transparent" />
            <div className="hidden lg:block absolute inset-0 bg-gradient-to-r from-transparent via-transparent via-60% to-bg/40" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center_35%,transparent_0%,transparent_50%,rgba(249,247,243,0.1)_100%)]" />
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-accent2 to-transparent opacity-60" />
        </div>

        {/* Content Column */}
        {/* Negative top margin pulls the card up over the portrait. md is a
            smaller pull than sm on purpose: the tablet portrait is width-capped
            (max-w-[560px]) so the face sits higher in the frame, and -55vh
            covered the mouth and chin. */}
        <div className="relative -mt-[50vh] sm:-mt-[52vh] md:-mt-[30vh] lg:mt-0 z-30 lg:flex lg:items-center lg:justify-start lg:-ml-28 xl:-ml-32">
          <div className="px-5 sm:px-10 lg:px-8 xl:px-10 pb-12 lg:pb-0">
            <div className="bg-surface rounded-[32px] shadow-[0_24px_48px_rgba(154,122,137,0.2)] lg:shadow-[0_40px_80px_rgba(154,122,137,0.35),0_16px_32px_rgba(0,0,0,0.12)] p-7 sm:p-10 lg:p-12 xl:p-14 border border-line/30 lg:border-line/50 max-w-xl lg:max-w-none">
              {/* HANDWRITING LOGO PLACEHOLDER — swap in the grandmother's handwriting SVG once provided. */}
              <div className="w-20 h-1 bg-gradient-to-r from-accent2 via-accent to-accent2/80 rounded-full mb-7 sm:mb-8 lg:mb-10" />

              <h1 className="font-serif text-accent font-medium leading-[0.92] tracking-tight">
                <span className="block text-[42px] sm:text-[56px] lg:text-[52px] xl:text-[64px]">
                  The Incurable
                </span>
                <span className="block text-[42px] sm:text-[56px] lg:text-[52px] xl:text-[64px] mt-1 lg:mt-0.5">
                  Humanist
                </span>
              </h1>

              <div className="mt-6 sm:mt-7 lg:mt-8 text-[13px] sm:text-[14px] uppercase tracking-[0.18em] text-muted-ink font-medium">
                {SITE.hero.byline}
              </div>

              <div className="mt-4 sm:mt-5 mb-4 sm:mb-5 w-16 h-px bg-gradient-to-r from-line to-transparent" />

              {/* heroTagline, not positioning: the latter still carries
                  "— and what gets inherited anyway" for meta descriptions and
                  JSON-LD, which Denise kept. Only the visible copy changed. */}
              <p className="text-[17px] sm:text-[21px] lg:text-[20px] xl:text-[22px] italic text-ink/70 leading-relaxed font-light max-w-md">
                {SITE.heroTagline}
              </p>

              {/* The Read / Listen / Book doors and the 5-essay reader CTA that
                  sat below them were removed at Denise's request (Aug 2026).
                  They were coupled: "Read" was a button, not a link, whose only
                  job was toggling that CTA open. Navigation to those
                  destinations now lives in the header nav.

                  The margin below is tighter than it was: mt-8/9/10 was spacing
                  the social row away from that CTA. With the CTA gone the same
                  value read as an empty hole between the tagline and CONNECT. */}

              {/* Social links */}
              <div className="mt-6 sm:mt-7 pt-5 sm:pt-6 border-t border-line/40">
                <div className="text-[11px] sm:text-[12px] uppercase tracking-[0.14em] text-muted-ink mb-4 font-medium">
                  Connect
                </div>
                <SocialIconRow
                  className="flex flex-wrap items-center gap-3"
                  buttonClassName="hover:scale-110 hover:bg-accent2/90 transition-all duration-300"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <>
      <SEO
        title="The Incurable Humanist — Denise Rodriguez Dao"
        description="Denise Rodriguez Dao writes The Incurable Humanist, a weekly newsletter on grief, migration, and art — and what gets inherited anyway."
        canonical="https://theincurablehumanist.com/"
        jsonLd={articleGraphForSite({ path: "/", pageName: "Home" })}
      />
      <HeroBlock />
    </>
  );
}
