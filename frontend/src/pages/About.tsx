import SectionTitle from "@/components/SectionTitle";
import Card from "@/components/Card";
import SEO from "@/components/SEO";
import SubscribeCTA from "@/components/SubscribeCTA";
import { articleGraphForSite } from "@/lib/schema";

export default function About() {
  return (
    <>
      <SEO
        title="About — Denise Rodriguez Dao | The Incurable Humanist"
        description="Denise Rodriguez Dao is a writer and business immigration consultant based in New York. She writes The Incurable Humanist, a weekly newsletter on grief, migration, and art."
        canonical="https://theincurablehumanist.com/about"
        jsonLd={articleGraphForSite({ path: "/about", pageName: "About" })}
      />
      <SectionTitle>About</SectionTitle>

      <section className="container mt-10 pb-20 md:pb-28 max-w-4xl">
        {/* Main Content Card */}
        <Card className="p-10 md:p-12 lg:p-14 mb-10 md:mb-14">
          <h2 className="font-serif text-accent2 text-[32px] md:text-[38px] text-center mb-10 md:mb-12 leading-tight">
            The Incurable Humanist
          </h2>

          <div className="space-y-8 text-[17px] md:text-[18px] leading-[1.75] max-w-[62ch] mx-auto text-justify hyphens-auto [text-wrap:pretty]">
            <p>
              Welcome to the curious world of <em>The Incurable Humanist</em>, a space to
              explore grief, migration, and art.
            </p>

            <p>
              Oops! You&rsquo;ve already gone down the rabbit hole into the unexpected
              connections between memory and culture, philosophy and history, and the ways we
              navigate loss and change.
            </p>

            {/* Visual Break with Accent Line */}
            <div className="py-6 md:py-8">
              <div className="mx-auto h-[2px] w-[56px] rounded bg-accent" />
            </div>

            <p>
              My dearest incurable humanist, I imagine that you, like me, are always
              overthinking, asking questions, and looking beyond the surface.
            </p>
          </div>
        </Card>

        {/* Founder Bio Card */}
        <Card className="p-10 md:p-12 lg:p-14">
          <h2 className="font-serif text-accent2 text-[32px] md:text-[38px] text-center mb-10 md:mb-12 leading-tight">
            Denise Rodriguez Dao
          </h2>

          {/* Founder Portrait */}
          <div className="mx-auto mb-10 md:mb-12 w-full max-w-[420px] md:max-w-[520px]">
            <img
              src="/denisehome.jpeg"
              alt="Denise Rodriguez Dao, who writes The Incurable Humanist, in burgundy blouse with books"
              className="w-full h-auto rounded-xl shadow-soft"
            />
          </div>

          <div className="max-w-[62ch] mx-auto space-y-8 text-[17px] md:text-[18px] leading-[1.75] text-justify hyphens-auto [text-wrap:pretty]">
            <p>
              Having lived in Caracas, Mexico City, and now based in New York City, I have
              become fascinated by memory, migration, and the lives behind the statistics. My
              family background spans Venezuela, Spain, Peru, El Salvador, Lebanon, and the
              United States, so I grew up surrounded by different traditions and perspectives.
            </p>

            <p>
              I hold a JD from Universidad Católica Andrés Bello and a Master&rsquo;s degree in
              Modern and Contemporary Art and the Market from Christie&rsquo;s Education New
              York. I am a business immigration consultant with experience in contemporary art
              and the
              creative industries, where I have worked with artists, collectors, entrepreneurs,
              musicians, and leaders across art and entertainment.
            </p>

            <p>
              I&rsquo;m glad you are here! There is always room for another incurable humanist.
            </p>
          </div>
        </Card>

        {/* End-of-post CTA — About is prime intent-to-subscribe surface. */}
        <div className="mt-12">
          <SubscribeCTA
            variant="end-of-post"
            placement="about-footer"
            headline="Follow Denise's writing."
            sub="Weekly essays on grief, migration, and art. Start with the free 5-essay reader."
          />
        </div>
      </section>
    </>
  );
}
