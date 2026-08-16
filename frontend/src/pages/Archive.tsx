import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "@/components/Card";
import SectionTitle from "@/components/SectionTitle";
import PressItemCard from "@/components/PressItemCard";
import SubscribeCTA from "@/components/SubscribeCTA";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";
import { API_CONFIG, type StoryPublic } from "@/config/api";
import { articleGraphForSite, articleNode } from "@/lib/schema";
import { withUTM } from "@/lib/utm";
import { formatDate } from "@/lib/date";
import { useAnalytics } from "@/hooks/useAnalytics";

// How many essays to show before the "Load more" control. The full corpus is
// ~71 rows — small enough to fetch in one request and slice client-side.
const PAGE_SIZE = 12;

function useOnSiteEssays() {
  const [stories, setStories] = useState<StoryPublic[]>([]);
  useEffect(() => {
    let alive = true;
    fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stories.list}?status=published&limit=100`)
      .then((r) => (r.ok ? r.json() : { stories: [] }))
      .then((data) => {
        if (!alive) return;
        setStories(Array.isArray(data?.stories) ? data.stories : []);
      })
      .catch(() => setStories([]));
    return () => {
      alive = false;
    };
  }, []);
  return stories;
}

// The best-of list ships with unfilled placeholder rows until Denise picks the
// essays. Rendering them leaks "[TODO: …]" onto a live page.
const bestOfEssays = SITE.bestOfEssays.filter((e) => !e.title.startsWith("[TODO"));

export default function Archive() {
  const onSiteEssays = useOnSiteEssays();
  const [visible, setVisible] = useState(PAGE_SIZE);
  const { track, events } = useAnalytics();

  // Essays are hosted here now, so every Article node points on-site. The old
  // Substack-feed nodes were removed with the feed itself — advertising
  // off-site URLs for content we host would undercut our own canonical.
  const onSiteJsonLd = onSiteEssays.slice(0, 10).map((s) =>
    articleNode({
      title: s.title,
      url: `${SITE.siteUrl}/essays/${s.slug}`,
      description: s.meta_description || s.excerpt || undefined,
      published: s.published_at || undefined,
      modified: s.updated_at,
      image: s.cover_image_url || undefined,
    })
  );

  return (
    <>
      <SEO
        title="Archive — The Incurable Humanist"
        description="A curated archive of essays by Denise Rodriguez Dao on grief, migration, and art. Start with the essays that most fully express the work, then read the full collection."
        canonical="https://theincurablehumanist.com/archive"
        jsonLd={[
          ...articleGraphForSite({ path: "/archive", pageName: "Archive" }),
          ...onSiteJsonLd,
        ]}
      />

      <SectionTitle>Archive</SectionTitle>

      <section className="container mt-8 max-w-4xl">
        <p className="text-center text-[16px] md:text-[17px] italic text-muted-ink max-w-2xl mx-auto leading-relaxed">
          {/* AEO-quotable intro paragraph. */}
          Denise Rodriguez Dao writes The Incurable Humanist — a weekly newsletter on grief,
          migration, and art. Below: the essays that most fully express the work, followed by
          the latest pieces and a note on press coverage.
        </p>
      </section>

      {/* Primary CTA — above the fold of the archive list. Highest-intent surface. */}
      <section className="container mt-10 max-w-3xl">
        <SubscribeCTA
          variant="primary"
          placement="archive-primary"
          headline="Start with the 5-essay reader."
          sub="A free PDF of Denise's best pieces on grief, migration, and art — then the weekly Sunday essay."
        />
      </section>

      {/*
        Every essay, hosted here. Previously this section sat below a "Recent
        from Substack" list that linked away; the essays are now synced on-site,
        so the outbound list is gone and this is the primary reading surface.
      */}
      {onSiteEssays.length > 0 && (
        <section className="container mt-16 max-w-5xl">
          <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
            Essays
          </h2>
          <div className="grid gap-6 md:grid-cols-2">
            {onSiteEssays.slice(0, visible).map((s) => {
              const published = formatDate(s.published_at);
              return (
                <Card
                  key={s.slug}
                  className="p-6 md:p-8 hover:shadow-[0_16px_40px_rgba(110,85,128,0.12)] transition-shadow"
                >
                  {(published || s.read_time_minutes) && (
                    <div className="font-serif text-[15px] italic text-accent/80 mb-2">
                      {published}
                      {published && s.read_time_minutes ? " · " : ""}
                      {s.read_time_minutes ? `${s.read_time_minutes} min read` : ""}
                    </div>
                  )}
                  <Link
                    to={`/essays/${s.slug}`}
                    onClick={() =>
                      track(events.ESSAY_CLICK, {
                        slug: s.slug,
                        placement: "archive-onsite",
                      })
                    }
                    className="font-serif text-[22px] md:text-[24px] text-ink hover:text-accent transition-colors leading-tight block"
                  >
                    {s.title}
                  </Link>
                  {s.excerpt && (
                    <p className="mt-3 text-[15px] text-muted-ink leading-relaxed">{s.excerpt}</p>
                  )}
                </Card>
              );
            })}
          </div>

          {visible < onSiteEssays.length && (
            <div className="mt-10 text-center">
              <button
                type="button"
                onClick={() => setVisible((n) => n + PAGE_SIZE)}
                className="inline-flex h-12 items-center rounded-pill border border-line bg-surface px-6 font-medium text-ink transition-colors hover:border-accent/40 hover:text-accent cursor-pointer whitespace-nowrap focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
              >
                Load more essays
                <span className="ml-2 text-muted-ink">
                  ({onSiteEssays.length - visible} more)
                </span>
              </button>
            </div>
          )}
        </section>
      )}

      {/* Best-of */}
      {bestOfEssays.length > 0 && (
      <section className="container mt-16 max-w-5xl">
        <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
          Start here — Best of
        </h2>
        <div className="grid gap-6 md:grid-cols-2">
          {bestOfEssays.map((essay) => {
            const href = withUTM(essay.href, {
              source: "website",
              medium: "referral",
              campaign: "archive-best-of",
              content: essay.theme.toLowerCase(),
            });
            return (
              <Card
                key={essay.theme}
                className="p-6 md:p-8 hover:shadow-[0_16px_40px_rgba(110,85,128,0.12)] transition-shadow"
              >
                <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-2 font-medium">
                  {essay.theme}
                </div>
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-serif text-[22px] md:text-[24px] text-ink hover:text-accent transition-colors leading-tight block"
                >
                  {essay.title}
                </a>
                <p className="mt-3 text-[15px] text-muted-ink leading-relaxed">
                  {essay.dek}
                </p>
              </Card>
            );
          })}
        </div>
      </section>
      )}

      {/* End-of-best-of CTA */}
      <section className="container mt-10 max-w-3xl">
        <SubscribeCTA
          variant="end-of-post"
          placement="archive-after-best-of"
          headline="Read the next one in your inbox."
          sub="Weekly, on Sunday mornings. Grief, migration, art. Free."
        />
      </section>

      {/* In the press */}
      <section className="container mt-20 max-w-5xl pb-20 md:pb-28">
        <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
          In the press
        </h2>
        <div className="space-y-8 md:space-y-10">
          {SITE.press.map((p) => (
            <PressItemCard key={p.title} {...p} />
          ))}
        </div>

        <div className="mt-14">
          <SubscribeCTA
            variant="end-of-post"
            placement="archive-footer"
            headline="Keep reading."
            sub="One essay a week. No spam. Substack delivers it."
          />
        </div>
      </section>
    </>
  );
}
