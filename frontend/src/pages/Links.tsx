import { useEffect, useState } from "react";
import SubscribeCTA from "@/components/SubscribeCTA";
import SEO from "@/components/SEO";
import ConsentBanner from "@/components/ConsentBanner";
import { SITE } from "@/config/site";
import { API_CONFIG } from "@/config/api";
import { useAnalytics } from "@/hooks/useAnalytics";
import { withUTM } from "@/lib/utm";
import { bootConsent } from "@/lib/analytics";

type Article = {
  title: string;
  link: string;
  description: string;
  published: string;
};

/**
 * Bio-link landing page for TikTok / Instagram / YouTube etc.
 * Deliberately minimal chrome — no App shell wrapper.
 * Structure: (1) subscribe CTA first, (2) trust element, (3) explore.
 * noindex: this page is for direct bio-link traffic, not organic search.
 */
export default function Links() {
  const { track, events } = useAnalytics();
  const [articles, setArticles] = useState<Article[]>([]);
  const [source, setSource] = useState<string>("bio-link");

  useEffect(() => {
    bootConsent();
    // Read ?src=tiktok from the URL so we can label the funnel.
    try {
      const src = new URLSearchParams(window.location.search).get("src");
      if (src) setSource(src.toLowerCase());
    } catch {
      // Ignore — malformed URLs shouldn't crash the bio-link page.
    }
  }, []);

  useEffect(() => {
    fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.newsletter.articles}`)
      .then((r) => (r.ok ? r.json() : { articles: [] }))
      .then((data) => setArticles(Array.isArray(data?.articles) ? data.articles.slice(0, 3) : []))
      .catch(() => setArticles([]));
  }, []);

  const outboundLink = (url: string, content: string) =>
    withUTM(url, {
      source: (source as "tiktok" | "instagram" | "facebook" | "youtube" | "linkedin" | "x" | "bio-link") ||
        "bio-link",
      medium: "bio-link",
      campaign: "links-page",
      content,
    });

  const trackClick = (destination: string, content: string) =>
    track(events.BIO_LINK_CLICK, {
      source,
      destination,
      content,
    });

  return (
    <div className="min-h-dvh bg-bg text-ink py-10 px-5">
      <SEO
        title="Links · The Incurable Humanist"
        description="Denise Rodriguez Dao — quick links to the newsletter, essays, and everywhere else."
        canonical="https://theincurablehumanist.com/links"
        noindex
      />

      <div className="max-w-md mx-auto flex flex-col items-center">
        {/* HANDWRITING LOGO PLACEHOLDER */}
        <div className="w-16 h-1 bg-gradient-to-r from-accent2 via-accent to-accent2/80 rounded-full mb-6" />
        <h1 className="font-serif text-accent text-[32px] leading-tight text-center">
          The Incurable Humanist
        </h1>
        <p className="mt-2 text-[14px] text-muted-ink text-center">
          By Denise Rodriguez Dao — grief, migration, art.
        </p>

        {/* 1. Subscribe first */}
        <div className="w-full mt-8">
          <SubscribeCTA
            variant="primary"
            placement={`links-${source}`}
            headline="Get the newsletter."
            sub="Weekly essays. Free. Delivered by Substack."
            autoFocus={false}
          />
        </div>

        {/* 2. Trust — press outlets + Voices for Venezuela */}
        <div className="w-full mt-8">
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-ink text-center mb-3">
            Featured in
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-muted-ink font-serif italic text-[14px]">
            {SITE.press.map((p) => (
              <span key={p.outlet}>{p.outlet}</span>
            ))}
          </div>
        </div>

        {/* 3. Explore — latest essays + socials */}
        <div className="w-full mt-8 space-y-3">
          {articles.map((a) => (
            <a
              key={a.link}
              href={outboundLink(a.link, "latest-essay")}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackClick(a.link, "latest-essay")}
              className="block rounded-2xl border border-line/60 bg-white/70 px-5 py-4 hover:bg-white hover:border-accent/40 hover:shadow-[0_10px_24px_rgba(110,85,128,0.10)] transition"
            >
              <div className="text-[11px] uppercase tracking-[0.14em] text-accent mb-1 font-medium">
                Latest essay
              </div>
              <div className="font-serif text-[18px] text-ink leading-tight">
                {a.title}
              </div>
            </a>
          ))}

          <a
            href={outboundLink("https://theincurablehumanist.com/speak", "speak")}
            onClick={() => trackClick("/speak", "speak")}
            className="block rounded-2xl border border-line/60 bg-white/70 px-5 py-4 hover:bg-white hover:border-accent/40 transition"
          >
            <div className="font-serif text-[18px] text-ink">Book a talk →</div>
          </a>

          <a
            href={outboundLink("https://theincurablehumanist.com/listen", "listen")}
            onClick={() => trackClick("/listen", "listen")}
            className="block rounded-2xl border border-line/60 bg-white/70 px-5 py-4 hover:bg-white hover:border-accent/40 transition"
          >
            <div className="font-serif text-[18px] text-ink">Audio essays →</div>
          </a>

          <a
            href={outboundLink(SITE.socials.instagram, "instagram")}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => trackClick(SITE.socials.instagram, "instagram")}
            className="block rounded-2xl border border-line/60 bg-white/70 px-5 py-4 hover:bg-white hover:border-accent/40 transition"
          >
            <div className="font-serif text-[18px] text-ink">Instagram</div>
          </a>

          <a
            href={outboundLink(SITE.socials.tiktok, "tiktok")}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => trackClick(SITE.socials.tiktok, "tiktok")}
            className="block rounded-2xl border border-line/60 bg-white/70 px-5 py-4 hover:bg-white hover:border-accent/40 transition"
          >
            <div className="font-serif text-[18px] text-ink">TikTok</div>
          </a>
        </div>

        <p className="mt-10 text-[12px] text-muted-ink/70 text-center">
          © {new Date().getFullYear()} Denise Rodriguez Dao
        </p>
      </div>
      <ConsentBanner />
    </div>
  );
}
