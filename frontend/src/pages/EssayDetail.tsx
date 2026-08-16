import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import SEO from "@/components/SEO";
import SubscribeCTA from "@/components/SubscribeCTA";
import Card from "@/components/Card";
import { API_CONFIG, type StoryDetail as StoryDetailData } from "@/config/api";
import { articleNode, articleGraphForSite } from "@/lib/schema";
import { formatDate } from "@/lib/date";
import { SITE } from "@/config/site";
import { useScrollDepth } from "@/hooks/useScrollDepth";

type State =
  | { kind: "loading" }
  | { kind: "ready"; story: StoryDetailData }
  | { kind: "not_found" }
  | { kind: "error"; message: string };

function useStory(slug: string | undefined): State {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!slug) {
      setState({ kind: "not_found" });
      return;
    }
    let alive = true;
    fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stories.detail(slug)}`)
      .then((r) => {
        if (r.status === 404) return null;
        if (!r.ok) throw new Error(`GET /stories/${slug} → ${r.status}`);
        return r.json() as Promise<StoryDetailData>;
      })
      .then((data) => {
        if (!alive) return;
        setState(data ? { kind: "ready", story: data } : { kind: "not_found" });
      })
      .catch((e) => {
        if (!alive) return;
        setState({ kind: "error", message: e instanceof Error ? e.message : "unknown" });
      });
    return () => {
      alive = false;
    };
  }, [slug]);

  return state;
}

export default function EssayDetail() {
  const { slug } = useParams<{ slug: string }>();
  const state = useStory(slug);
  // Consent-gated — no-op until the visitor has opted in.
  useScrollDepth({ properties: { slug: slug ?? "" } });

  if (state.kind === "loading") {
    return (
      <section className="container mt-16 max-w-3xl">
        <p className="text-center text-[15px] text-muted-ink">Loading…</p>
      </section>
    );
  }

  if (state.kind === "not_found") {
    return (
      <section className="container mt-16 max-w-3xl pb-24">
        <Card className="p-8 md:p-12 text-center">
          <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-3 font-medium">
            Not found
          </div>
          <h1 className="font-serif text-accent2 text-[28px] md:text-[34px] mb-4">
            That essay isn't here.
          </h1>
          <p className="text-[15px] text-muted-ink mb-6">
            It may have been retired, or the link may be off by a character.
          </p>
          <Link
            to="/archive"
            className="inline-flex items-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 transition font-medium"
          >
            Browse the archive
          </Link>
        </Card>
      </section>
    );
  }

  if (state.kind === "error") {
    return (
      <section className="container mt-16 max-w-3xl pb-24">
        <p className="text-center text-[15px] text-muted-ink">
          We couldn't load this essay. Try again in a moment.
        </p>
      </section>
    );
  }

  const { story } = state;
  const ownUrl = `${SITE.siteUrl}/essays/${story.slug}`;
  const canonical = story.canonical_url && story.canonical_url.length > 0
    ? story.canonical_url
    : ownUrl;
  const description = story.meta_description || story.excerpt || undefined;
  const publishedIso = story.published_at || undefined;

  const jsonLd = [
    ...articleGraphForSite({ path: `/essays/${story.slug}`, pageName: story.title }),
    articleNode({
      title: story.title,
      url: ownUrl,
      description,
      published: publishedIso,
      modified: story.updated_at,
      image: story.cover_image_url || undefined,
    }),
  ];

  const publishedLabel = formatDate(story.published_at);

  return (
    <>
      <SEO
        title={`${story.title} — The Incurable Humanist`}
        description={description || `${story.title} — an essay by Denise Rodriguez Dao.`}
        canonical={canonical}
        ogImage={story.cover_image_url || undefined}
        jsonLd={jsonLd}
      />

      <article className="container mt-12 max-w-3xl pb-16">
        <header className="mb-10">
          <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-4 font-medium">
            <Link to="/archive" className="hover:underline underline-offset-4">
              Archive
            </Link>
            {publishedLabel && <span className="text-muted-ink"> · {publishedLabel}</span>}
            {story.read_time_minutes && (
              <span className="text-muted-ink"> · {story.read_time_minutes} min read</span>
            )}
          </div>
          <h1 className="font-serif text-accent2 text-[36px] md:text-[48px] leading-[1.1]">
            {story.title}
          </h1>
          {story.excerpt && (
            <p className="mt-5 text-[18px] md:text-[19px] italic text-muted-ink leading-relaxed">
              {story.excerpt}
            </p>
          )}
          {story.content_warning && (
            <p className="mt-5 text-[13px] uppercase tracking-widest text-accent">
              Content note: {story.content_warning}
            </p>
          )}
        </header>

        {story.cover_image_url && (
          <img
            src={story.cover_image_url}
            alt=""
            className="w-full h-auto rounded-xl shadow-soft mb-10"
          />
        )}

        {/*
          Tiptap output is trusted-author HTML (created via /admin behind
          get_current_author). If we ever accept guest posts, sanitize with
          DOMPurify before rendering.
        */}
        <div
          className="essay-content max-w-[62ch] mx-auto text-[17px] md:text-[18px] leading-[1.8] text-ink [text-wrap:pretty]"
          dangerouslySetInnerHTML={{ __html: story.content }}
        />

        {/*
          Credit line reads source_url, not canonical_url: the on-site page is
          canonical (so this essay is what search engines index), and source_url
          records where it first appeared.
        */}
        {(story.source_url || story.canonical_url) && (
          <p className="mt-10 max-w-[62ch] mx-auto text-[13px] text-muted-ink italic">
            This essay was first published on{" "}
            <a
              href={story.source_url || story.canonical_url || undefined}
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 hover:text-accent"
            >
              Substack
            </a>
            .
          </p>
        )}
      </article>

      <section className="container max-w-3xl pb-24">
        <SubscribeCTA
          variant="end-of-post"
          placement={`essay-${story.slug}-footer`}
          headline="Read the next one in your inbox."
          sub="Weekly essays on grief, migration, and art. Start with the free 5-essay reader."
        />
      </section>
    </>
  );
}
