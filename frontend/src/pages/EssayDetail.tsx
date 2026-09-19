import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import SEO from "@/components/SEO";
import Card from "@/components/Card";
import RelatedEssays from "@/components/RelatedEssays";
import { API_CONFIG, type StoryDetail as StoryDetailData } from "@/config/api";
import { articleNode, articleGraphForSite, pageTitle } from "@/lib/schema";
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
            Browse the writing
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

  // The excerpt IS the lead paragraph, truncated at 300 chars with an ellipsis
  // (see excerpt_from in html_sanitize.py). Rendering it as a dek directly
  // above the body therefore shows the same sentence twice in a row, the
  // second time in full. Suppress the dek when it is merely a prefix of the
  // opening paragraph; keep it when the author has written a real standfirst.
  const firstParagraph = (story.content.match(/<p>(.*?)<\/p>/s)?.[1] ?? "")
    .replace(/<[^>]+>/g, "")
    .trim();
  const dekIsRedundant =
    !!story.excerpt &&
    firstParagraph.startsWith(story.excerpt.replace(/…$/, "").trim().slice(0, 60));

  // Substack's cover image is usually also the essay's first inline image, so
  // rendering both shows the same photo twice. Measured across the corpus:
  // 47 of 73 essays duplicate it, 26 have a genuinely distinct cover.
  //
  // Suppressing the duplicate also removes the page's worst layout shift. The
  // body copy's <img> carries width/height, but this one cannot — the API
  // exposes no dimensions for cover_image_url — so with `w-full h-auto` the
  // browser reserves zero height and reflows the whole article once the image
  // arrives. Measured CLS on essay pages was 0.49-0.74 against a 0.1 budget.
  const coverIsDuplicate =
    !!story.cover_image_url && story.content.includes(story.cover_image_url);
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
      {/* pageTitle truncates for the <title> tag only — 28 of 73 essay
          titles overflowed the ~60-char search-result budget once the site
          suffix was appended. The full headline stays in JSON-LD and OG. */}
      <SEO
        title={pageTitle(story.title)}
        description={description || `${story.title} — an essay by Denise Rodriguez Dao.`}
        canonical={canonical}
        ogImage={story.cover_image_url || undefined}
        jsonLd={jsonLd}
      />

      <article className="container mt-12 max-w-3xl pb-16">
        <header className="mb-10">
          <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-4 font-medium">
            <Link to="/archive" className="hover:underline underline-offset-4">
              Writing
            </Link>
            {publishedLabel && <span className="text-muted-ink"> · {publishedLabel}</span>}
            {story.read_time_minutes && (
              <span className="text-muted-ink"> · {story.read_time_minutes} min read</span>
            )}
          </div>
          <h1 className="font-serif text-accent2 text-[36px] md:text-[48px] leading-[1.1]">
            {story.title}
          </h1>
          {story.excerpt && !dekIsRedundant && (
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

        {story.cover_image_url && !coverIsDuplicate && (
          // The cover is the LCP element on an essay page. fetchPriority tells
          // the browser to race it ahead of the rest of the tree; without it
          // the image is discovered only once React has mounted, since the tag
          // lives inside the component.
          <img
            src={story.cover_image_url}
            alt=""
            fetchPriority="high"
            decoding="async"
            /* The API exposes no dimensions for cover_image_url, so reserve the
               space with an aspect ratio instead. Without it `h-auto` reserves
               zero height and the whole article reflows when the image lands.
               object-cover keeps a differently-shaped image from distorting. */
            style={{ aspectRatio: "16 / 9" }}
            className="w-full h-auto object-cover rounded-xl shadow-soft mb-10"
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

      {/* The end-of-essay SubscribeCTA ("Read the next one in your inbox.")
          was removed at Denise's request (Sep 2026). Essay pages carry no
          on-site capture now; the exit-intent modal and the footer are the
          remaining surfaces.

          RelatedEssays took that slot instead. It is not a replacement CTA —
          it asks nothing of the reader — it fixes the separate problem that
          every essay was a dead end, linking to no other essay on the site.
          It renders nothing (including no spacing) when an essay has no
          related sibling, so the fallback padding below still applies. */}
      <RelatedEssays slug={story.slug} />
      <div className="pb-24" />
    </>
  );
}
