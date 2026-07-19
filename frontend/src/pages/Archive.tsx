import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "@/components/Card";
import SectionTitle from "@/components/SectionTitle";
import NewsletterArticleCard from "@/components/NewsletterArticleCard";
import PressItemCard from "@/components/PressItemCard";
import SubscribeCTA from "@/components/SubscribeCTA";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";
import { API_CONFIG, type StoryPublic } from "@/config/api";
import { articleGraphForSite, articleNode } from "@/lib/schema";
import { withUTM } from "@/lib/utm";
import { useAnalytics } from "@/hooks/useAnalytics";

type SubstackArticle = {
  title: string;
  link: string;
  description: string;
  published: string;
};

function useOnSiteEssays() {
  const [stories, setStories] = useState<StoryPublic[]>([]);
  useEffect(() => {
    let alive = true;
    fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stories.list}?status=published&limit=20`)
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

function useSubstackFeed() {
  const [articles, setArticles] = useState<SubstackArticle[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.newsletter.articles}`)
      .then((r) => {
        if (!r.ok) throw new Error(`Feed responded ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (!alive) return;
        // Backend returns { articles: [], total_count }.
        const list = Array.isArray(data?.articles) ? data.articles : [];
        setArticles(list);
      })
      .catch((e) => {
        if (!alive) return;
        setError(e instanceof Error ? e.message : "unknown");
      });
    return () => {
      alive = false;
    };
  }, []);

  return { articles, error };
}

export default function Archive() {
  const { articles, error } = useSubstackFeed();
  const onSiteEssays = useOnSiteEssays();
  const { track, events } = useAnalytics();

  const feedJsonLd =
    articles && articles.length > 0
      ? articles.slice(0, 10).map((a) =>
          articleNode({
            title: a.title,
            url: a.link,
            description: a.description,
            published: a.published,
          })
        )
      : [];

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
        description="A curated archive of essays by Denise Rodriguez Dao on grief, migration, and art. Start with the four essays that most fully express the work; then browse recent pieces from Substack."
        canonical="https://theincurablehumanist.com/archive"
        jsonLd={[
          ...articleGraphForSite({ path: "/archive", pageName: "Archive" }),
          ...onSiteJsonLd,
          ...feedJsonLd,
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

      {/* On-site essays — appears only when there's something to show. */}
      {onSiteEssays.length > 0 && (
        <section className="container mt-16 max-w-5xl">
          <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
            Essays
          </h2>
          <div className="grid gap-6 md:grid-cols-2">
            {onSiteEssays.slice(0, 12).map((s) => (
              <Card key={s.slug} className="p-6 md:p-8 hover:shadow-[0_16px_40px_rgba(110,85,128,0.12)] transition-shadow">
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
                  <p className="mt-3 text-[15px] text-muted-ink leading-relaxed">
                    {s.excerpt}
                  </p>
                )}
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Best-of */}
      <section className="container mt-16 max-w-5xl">
        <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
          Start here — Best of
        </h2>
        <div className="grid gap-6 md:grid-cols-2">
          {SITE.bestOfEssays.map((essay) => {
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

      {/* End-of-best-of CTA */}
      <section className="container mt-10 max-w-3xl">
        <SubscribeCTA
          variant="end-of-post"
          placement="archive-after-best-of"
          headline="Read the next one in your inbox."
          sub="Weekly, on Sunday mornings. Grief, migration, art. Free."
        />
      </section>

      {/* Recent from Substack */}
      <section className="container mt-16 max-w-5xl">
        <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
          Recent essays
        </h2>
        {error && (
          <p className="text-center text-[15px] text-muted-ink">
            The live feed is temporarily unavailable. Read the latest directly on{" "}
            <a
              href={withUTM(SITE.substackUrl, {
                source: "website",
                medium: "referral",
                campaign: "archive-feed-fallback",
              })}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline underline-offset-2"
            >
              Substack
            </a>
            .
          </p>
        )}
        {!articles && !error && (
          <p className="text-center text-[15px] text-muted-ink">Loading…</p>
        )}
        {articles && articles.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2">
            {articles.slice(0, 8).map((a) => (
              <NewsletterArticleCard
                key={a.link}
                title={a.title}
                link={withUTM(a.link, {
                  source: "website",
                  medium: "referral",
                  campaign: "archive-recent",
                })}
                description={a.description}
                published={a.published}
              />
            ))}
          </div>
        )}
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
