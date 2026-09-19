import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "@/components/Card";
import { useAnalytics } from "@/hooks/useAnalytics";

type Related = { slug: string; title: string; excerpt: string | null };

/**
 * "Keep reading" — 2-3 topically related essays at the end of an essay.
 *
 * Before this existed, ZERO of the 75 essays linked to any other essay: the
 * only route between them was back out to /archive. That left every essay a
 * dead end for readers and an island for crawlers, with no internal link graph
 * to express which pieces belong together.
 *
 * The pairings are computed at build time by scripts/generate-related.mjs
 * (TF-IDF over title + body) and shipped as a static JSON map. Fetched rather
 * than bundled: it is ~30KB covering all 75 essays and only this component
 * needs it, so bundling it would put it in the critical path of every route.
 *
 * Renders NOTHING when an essay has no sufficiently-related sibling. That is
 * deliberate — roughly one essay in six has no genuine match, and a weak
 * recommendation is worse than none for both the reader and the topic signal.
 */
export default function RelatedEssays({ slug }: { slug: string }) {
  const [related, setRelated] = useState<Related[]>([]);
  const { track, events } = useAnalytics();

  useEffect(() => {
    let alive = true;
    setRelated([]);
    fetch("/related-essays.json")
      .then((r) => (r.ok ? r.json() : {}))
      .then((map: Record<string, Related[]>) => {
        if (!alive) return;
        setRelated(Array.isArray(map?.[slug]) ? map[slug] : []);
      })
      // Fail silent: the essay itself is unaffected, and a missing
      // recommendations strip is not worth an error state.
      .catch(() => setRelated([]));
    return () => {
      alive = false;
    };
  }, [slug]);

  if (related.length === 0) return null;

  return (
    <section className="container mt-16 max-w-5xl pb-20 md:pb-28">
      <h2 className="font-serif text-accent2 text-[26px] md:text-[30px] mb-6 text-center">
        Keep reading
      </h2>
      <div className="grid gap-6 md:grid-cols-3">
        {related.map((essay) => (
          <Card
            key={essay.slug}
            className="p-6 hover:shadow-[0_16px_40px_rgba(110,85,128,0.12)] transition-shadow"
          >
            <Link
              to={`/essays/${essay.slug}`}
              onClick={() =>
                track(events.ESSAY_CLICK, { slug: essay.slug, placement: "related-essays" })
              }
              className="font-serif text-[20px] md:text-[21px] text-ink hover:text-accent transition-colors leading-tight block"
            >
              {essay.title}
            </Link>
            {essay.excerpt && (
              <p className="mt-3 text-[15px] text-muted-ink leading-relaxed line-clamp-4">
                {essay.excerpt}
              </p>
            )}
          </Card>
        ))}
      </div>
    </section>
  );
}
