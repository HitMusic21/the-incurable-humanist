import Card from "@/components/Card";
import PressItemCard from "@/components/PressItemCard";
import SectionTitle from "@/components/SectionTitle";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";
import { articleGraphForSite } from "@/lib/schema";

/**
 * Press coverage.
 *
 * /press was a retired route that 301'd to /archive, where the press cards
 * actually lived. Denise asked for it back as a page of its own (Aug 2026), so
 * the cards moved here and both redirects — the Worker's `_REDIRECTS` entry and
 * the client-side <Navigate> — were removed. Without removing the Worker one
 * the 301 fires before React ever loads and this file never renders.
 *
 * Outlet names still appear as a "Featured in" strip on /speak and /links; both
 * read the same SITE.press array, so adding an outlet fans out to all three.
 */
export default function Press() {
  return (
    <>
      <SEO
        title="Press — Denise Rodriguez Dao | The Incurable Humanist"
        description="Denise Rodriguez Dao in the press: Observer, The Art Gorgeous, Singulart Magazine, and La Guía de Caracas on Latin American art, migration, and cultural advocacy."
        canonical="https://theincurablehumanist.com/press"
        jsonLd={articleGraphForSite({ path: "/press", pageName: "Press" })}
      />

      <SectionTitle>Press</SectionTitle>

      <section className="container mt-8 max-w-4xl">
        <p className="text-center text-[16px] md:text-[17px] italic text-muted-ink max-w-2xl mx-auto leading-relaxed">
          Writing and conversations about Denise&rsquo;s work in Latin American art,
          migration, and cultural advocacy.
        </p>
      </section>

      <section className="container mt-12 max-w-5xl pb-20 md:pb-28">
        {SITE.press.length > 0 ? (
          <div className="space-y-8 md:space-y-10">
            {SITE.press.map((p) => (
              <PressItemCard key={p.href} {...p} />
            ))}
          </div>
        ) : (
          // Defensive: the page is in the nav and the sitemap, so it must not
          // render as a bare heading if the array is ever emptied.
          <Card className="p-10 md:p-12 text-center">
            <p className="text-[16px] text-muted-ink leading-relaxed">
              Press coverage will appear here.
            </p>
          </Card>
        )}
      </section>
    </>
  );
}
