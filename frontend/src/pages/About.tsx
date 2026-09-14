import SectionTitle from "@/components/SectionTitle";
import Card from "@/components/Card";
import SEO from "@/components/SEO";
import { articleGraphForSite } from "@/lib/schema";

export default function About() {
  return (
    <>
      <SEO
        title="About — Denise Rodriguez Dao | The Incurable Humanist"
        description="Denise Rodriguez Dao is a writer and immigration consultant based in New York. She writes The Incurable Humanist, a weekly newsletter on grief, migration, and art."
        canonical="https://theincurablehumanist.com/about"
        jsonLd={articleGraphForSite({ path: "/about", pageName: "About" })}
      />
      <SectionTitle>About</SectionTitle>

      {/* One card, portrait first, no section subtitles — Denise's Aug 2026
          revision. The prose was previously split across two cards headed "The
          Incurable Humanist" and "Denise Rodriguez Dao"; those headings are
          gone and the six paragraphs now run continuously, as she wrote them.
          The page's own <SectionTitle>About</SectionTitle> remains the h1. */}
      <section className="container mt-10 pb-20 md:pb-28 max-w-4xl">
        <Card className="p-10 md:p-12 lg:p-14">
          {/* Portrait sits above all the prose. It is the LCP element on this
              page, so it carries intrinsic dimensions: without them the browser
              reserves no height and the whole card reflows when the image
              lands — the same defect fixed on essay pages in Sep 2026. */}
          <div className="mx-auto mb-10 md:mb-12 w-full max-w-[420px] md:max-w-[520px]">
            <img
              src="/denisehome.jpeg"
              alt="Denise Rodriguez Dao, who writes The Incurable Humanist, in burgundy blouse with books"
              width={2832}
              height={4240}
              fetchPriority="high"
              decoding="async"
              className="w-full h-auto rounded-xl shadow-soft"
            />
          </div>

          {/* Long-form prose per docs/UI_DESIGN_SYSTEM.md: 62ch measure,
              centred, ragged-right. Justification and hyphenation were
              removed Sep 2026 — the author read hyphenated line breaks as
              words being cut off. Do not swap this for max-w-3xl. */}
          <div className="max-w-[62ch] mx-auto space-y-8 text-[17px] md:text-[18px] leading-[1.75] [text-wrap:pretty]">
            <p>
              Welcome to the curious world of <em>The Incurable Humanist</em>, a space to
              explore grief, migration, and art.
            </p>

            <p>
              Oops! You&rsquo;ve already gone down the rabbit hole into the unexpected
              connections between memory and culture, philosophy and history, and the ways we
              navigate loss and change.
            </p>

            <p>
              My dearest incurable humanist, I imagine that you, like me, are always
              overthinking, asking questions, and looking beyond the surface.
            </p>

            <p>
              Having lived in Caracas, Mexico City, and now based in New York City, I have
              become fascinated by memory, migration, and the lives behind the statistics. My
              family background spans Venezuela, Spain, Peru, El Salvador, Lebanon, and the
              United States, so I grew up surrounded by different traditions and perspectives.
            </p>

            <p>
              I hold a JD from Universidad Católica Andrés Bello and a Master&rsquo;s degree in
              Modern and Contemporary Art and the Market from Christie&rsquo;s Education New
              York. I am an immigration consultant with experience in contemporary art
              and the creative industries, where I have worked with artists, collectors,
              entrepreneurs, musicians, and leaders across art and entertainment.
            </p>

            <p>
              Come in! There is always room for another incurable humanist.
            </p>
          </div>
        </Card>
      </section>
    </>
  );
}
