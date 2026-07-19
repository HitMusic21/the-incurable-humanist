import { Link, useParams } from "react-router-dom";
import Card from "@/components/Card";
import SectionTitle from "@/components/SectionTitle";
import SubscribeCTA from "@/components/SubscribeCTA";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";
import { useAnalytics } from "@/hooks/useAnalytics";
import { articleGraphForSite } from "@/lib/schema";

type Topic = (typeof SITE.speakingTopics)[number];

function serviceNode(topic: Topic) {
  return {
    "@type": "Service",
    serviceType: "Speaking Engagement",
    name: topic.title,
    description: topic.blurb,
    provider: { "@id": `${SITE.siteUrl}/about#denise` },
    areaServed: "US",
    audience: {
      "@type": "Audience",
      audienceType: topic.audience,
    },
    url: `${SITE.siteUrl}/speak/${topic.slug}`,
    keywords: [...topic.keywords].join(", "),
  };
}

export default function TopicLanding() {
  const { topic: topicSlug } = useParams<{ topic: string }>();
  const topic = SITE.speakingTopics.find((t) => t.slug === topicSlug);
  const { track, events } = useAnalytics();

  if (!topic) {
    return (
      <section className="container mt-16 max-w-2xl pb-24">
        <Card className="p-8 md:p-12 text-center">
          <h1 className="font-serif text-accent2 text-[28px] mb-4">Topic not found.</h1>
          <Link
            to="/speak"
            className="inline-flex items-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 transition font-medium"
          >
            All speaking topics
          </Link>
        </Card>
      </section>
    );
  }

  const canonical = `${SITE.siteUrl}/speak/${topic.slug}`;
  const bookingSubject = encodeURIComponent(`Speaking inquiry — ${topic.title}`);
  const bookingBody = encodeURIComponent(
    `Hi Denise,\n\nI'd like to invite you to speak on "${topic.title}" at [event / organization] on [date]. A few details:\n\n• Audience: \n• Format: \n• Location: \n• Budget: \n\nLooking forward.\n`
  );
  const mailto = `mailto:${SITE.bookingEmail}?subject=${bookingSubject}&body=${bookingBody}`;

  return (
    <>
      <SEO
        title={`${topic.title} — Speaking with Denise Rodriguez Dao`}
        description={topic.blurb.slice(0, 300)}
        canonical={canonical}
        jsonLd={[
          ...articleGraphForSite({ path: `/speak/${topic.slug}`, pageName: topic.title }),
          serviceNode(topic),
        ]}
      />

      <SectionTitle>Speak</SectionTitle>

      <section className="container mt-8 max-w-3xl">
        <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-3 font-medium text-center">
          Signature topic
        </div>
        <h1 className="font-serif text-accent2 text-[36px] md:text-[48px] leading-[1.05] text-center">
          {topic.title}
        </h1>
        <p className="mt-4 text-center text-[17px] md:text-[19px] italic text-muted-ink leading-relaxed max-w-2xl mx-auto">
          {topic.subtitle}
        </p>
      </section>

      <section className="container mt-12 max-w-4xl">
        <Card className="p-8 md:p-12">
          <p className="text-[17px] md:text-[18px] text-ink leading-[1.75] max-w-[62ch] mx-auto text-justify hyphens-auto [text-wrap:pretty]">
            {topic.blurb}
          </p>

          <div className="mt-8 pt-8 border-t border-line/50 flex flex-wrap gap-3 justify-center">
            <a
              href={mailto}
              onClick={() =>
                track(events.SPEAKER_INQUIRY, {
                  placement: `speak-topic-${topic.slug}`,
                  topic: topic.slug,
                })
              }
              aria-label={`Email ${SITE.bookingEmail} — ${topic.title}`}
              className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 active:brightness-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent2 transition font-medium whitespace-nowrap cursor-pointer"
            >
              Email Denise about this talk
            </a>
            <Link
              to="/speak"
              className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill border border-accent text-accent hover:bg-accent hover:text-white transition font-medium whitespace-nowrap"
            >
              All speaking topics
            </Link>
          </div>
        </Card>
      </section>

      <section className="container mt-10 max-w-3xl">
        <div className="text-[11px] uppercase tracking-[0.14em] text-muted-ink mb-3 font-medium text-center">
          Best fit for
        </div>
        <p className="text-center text-[15px] md:text-[16px] text-muted-ink max-w-xl mx-auto">
          {topic.audience}
        </p>
      </section>

      <section className="container mt-16 max-w-3xl pb-24">
        <SubscribeCTA
          variant="end-of-post"
          placement={`speak-topic-${topic.slug}-footer`}
          headline="Read Denise's writing first."
          sub="The essays are the syllabus. Free PDF of the best five, then Sunday-morning delivery."
        />
      </section>
    </>
  );
}
