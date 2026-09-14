import Card from "@/components/Card";
import PillButton from "@/components/PillButton";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";

export default function NotFound() {
  return (
    <>
      {/* noindex is load-bearing. The Worker's SPA fallback serves unmatched
          paths as 200 + shell (it cannot tell a typo from /subscribed or
          /links, which are real routes), so without this every mistyped URL
          would be an indexable soft-404. */}
      <SEO
        title="Page not found — The Incurable Humanist"
        description="That page doesn't exist or has been moved."
        canonical={`${SITE.siteUrl}/404`}
        noindex
      />
    <section className="container py-20 md:py-28 lg:py-36 text-center max-w-3xl">
      <Card className="p-10 md:p-12 lg:p-14">
        <h1 className="font-serif text-accent text-[64px] md:text-[80px] mb-4">404</h1>
        <h2 className="font-serif text-accent2 text-[28px] md:text-[32px] mb-6">
          Page Not Found
        </h2>
        <p className="text-[17px] md:text-[18px] text-muted-ink mb-8 leading-relaxed">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="py-6">
          <div className="mx-auto h-[2px] w-[56px] rounded bg-accent" />
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mt-8">
          <PillButton as="link" to="/">
            Go Home
          </PillButton>
          <PillButton as="link" to="/about">
            Learn More
          </PillButton>
        </div>
      </Card>
    </section>
    </>
  );
}
