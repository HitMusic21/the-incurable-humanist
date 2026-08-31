import SectionTitle from "@/components/SectionTitle";
import Card from "@/components/Card";
import SEO from "@/components/SEO";
import { articleGraphForSite } from "@/lib/schema";

/**
 * Privacy policy.
 *
 * Kept factually tied to what `src/lib/analytics.ts` actually does — PostHog on
 * consent, GA4/Meta/TikTok lazy-loaded only after grant, consent stored in
 * localStorage under `tih_consent_v1` with a 12-month TTL. If the analytics
 * stack changes, this page has to change with it; a policy that describes
 * tooling the site no longer uses is worse than none.
 */
export default function Privacy() {
  return (
    <>
      <SEO
        title="Privacy — The Incurable Humanist"
        description="How The Incurable Humanist handles analytics, cookies, and newsletter data — what is collected, why, and how to opt out."
        canonical="https://theincurablehumanist.com/privacy"
        jsonLd={articleGraphForSite({ path: "/privacy", pageName: "Privacy" })}
      />
      <SectionTitle>Privacy</SectionTitle>

      <section className="container mt-10 pb-20 md:pb-28 max-w-4xl">
        <Card className="p-10 md:p-12 lg:p-14">
          <div className="max-w-[62ch] mx-auto space-y-8 text-[17px] md:text-[18px] leading-[1.75] text-justify hyphens-auto [text-wrap:pretty]">
            <p>
              This site is a personal publication. It collects as little as possible, and
              nothing at all until you say yes.
            </p>

            <h2 className="font-serif text-accent2 text-[24px] md:text-[27px] !mt-12 mb-2 text-left">
              Analytics and cookies
            </h2>

            <p>
              Nothing is tracked until you accept the banner. If you decline, or simply
              ignore it, no analytics or marketing scripts are loaded and the site works
              exactly the same.
            </p>

            <p>
              If you accept, this site uses <strong>PostHog</strong> for product analytics
              (which pages are read, which links are followed) and loads{" "}
              <strong>Google Analytics 4</strong>, the <strong>Meta Pixel</strong>, and the{" "}
              <strong>TikTok Pixel</strong>. Those three are advertising tools and are only
              ever injected after consent — they are not present in the page otherwise.
            </p>

            <p>
              Your choice is stored in your browser&rsquo;s local storage under the key{" "}
              <code>tih_consent_v1</code> and expires after twelve months, at which point
              you will be asked again.
            </p>

            <h2 className="font-serif text-accent2 text-[24px] md:text-[27px] !mt-12 mb-2 text-left">
              The newsletter
            </h2>

            <p>
              If you subscribe, your email address is stored so the newsletter can be sent
              to you, and the referring page and any campaign parameters in the link you
              arrived from are recorded so it is possible to know which writing brought
              people here. Delivery is handled by SendGrid. Every email includes an
              unsubscribe link, and unsubscribing is honoured immediately.
            </p>

            <h2 className="font-serif text-accent2 text-[24px] md:text-[27px] !mt-12 mb-2 text-left">
              What is never done
            </h2>

            <p>
              Your data is not sold and it is not shared with anyone beyond the services
              named above, each of which is used only to run this site. There is no
              advertising network buying this list.
            </p>

            <h2 className="font-serif text-accent2 text-[24px] md:text-[27px] !mt-12 mb-2 text-left">
              Changing your mind
            </h2>

            <p>
              To withdraw consent, clear this site&rsquo;s data in your browser settings and
              the banner will appear again on your next visit. To be removed from the
              newsletter, use the unsubscribe link in any email. For anything else —
              including a request to delete data already held — write to{" "}
              <a
                className="underline underline-offset-4 decoration-accent/60 hover:decoration-accent"
                href="mailto:hello@theincurablehumanist.com"
              >
                hello@theincurablehumanist.com
              </a>
              .
            </p>
          </div>
        </Card>
      </section>
    </>
  );
}
