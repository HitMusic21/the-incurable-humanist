import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Card from "@/components/Card";
import SEO from "@/components/SEO";
import { SITE } from "@/config/site";
import { useAnalytics } from "@/hooks/useAnalytics";
import { withUTM } from "@/lib/utm";

// One share text so every channel says the same thing — makes the referral
// attribution funnel clean to read in PostHog.
const SHARE_MESSAGE =
  "A newsletter I love: The Incurable Humanist, by Denise Rodriguez Dao — grief, migration, art. Free.";

function referralUrl(): string {
  return withUTM(SITE.siteUrl, {
    source: "website",
    medium: "referral",
    campaign: "reader-magnet",
    content: "thank-you",
  });
}

function twitterShareUrl(url: string, text: string): string {
  const q = new URLSearchParams({ url, text });
  return `https://twitter.com/intent/tweet?${q.toString()}`;
}
function whatsappShareUrl(url: string, text: string): string {
  const q = new URLSearchParams({ text: `${text} ${url}` });
  return `https://wa.me/?${q.toString()}`;
}
function emailShareUrl(url: string, text: string): string {
  const subject = "You might like this newsletter";
  const body = `${text}\n\n${url}`;
  const q = new URLSearchParams({ subject, body });
  return `mailto:?${q.toString()}`;
}

export default function Subscribed() {
  const [params] = useSearchParams();
  const isMagnetFlow = params.get("magnet") === "1";
  const { track, events } = useAnalytics();

  useEffect(() => {
    if (isMagnetFlow) {
      // Tier 4 dashboard: funnel step after confirmation-click → magnet delivery.
      track(events.LEAD_MAGNET_CONFIRMED, { source: "confirm-redirect" });
    }
  }, [isMagnetFlow, track, events]);

  const url = referralUrl();
  const channels: {
    key: "twitter" | "whatsapp" | "email";
    label: string;
    href: string;
    external: boolean;
  }[] = [
    { key: "twitter", label: "Share on X", href: twitterShareUrl(url, SHARE_MESSAGE), external: true },
    { key: "whatsapp", label: "WhatsApp", href: whatsappShareUrl(url, SHARE_MESSAGE), external: true },
    { key: "email", label: "Email a friend", href: emailShareUrl(url, SHARE_MESSAGE), external: false },
  ];

  return (
    <>
      <SEO
        title="You're in — The Incurable Humanist"
        description="Thanks for confirming your subscription to The Incurable Humanist."
        canonical="https://theincurablehumanist.com/subscribed"
        noindex
      />

      <section className="container mt-16 max-w-2xl pb-24">
        <Card className="p-8 md:p-12 text-center">
          <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-4 font-medium">
            {isMagnetFlow ? "Confirmed" : "Almost there"}
          </div>
          <h1 className="font-serif text-accent2 text-[32px] md:text-[40px] leading-tight mb-5">
            {isMagnetFlow ? "The reader is on its way." : "Check your inbox."}
          </h1>
          <p className="text-[17px] md:text-[18px] text-muted-ink leading-relaxed max-w-lg mx-auto">
            {isMagnetFlow
              ? "We just emailed you a link to Denise's 5-essay starter reader. The next Sunday-morning essay follows in a few days."
              : "We sent a confirmation link. Click it to unlock the free 5-essay starter reader and join the Sunday-morning list."}
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/archive"
              className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 transition font-medium"
            >
              Browse the archive
            </Link>
            <Link
              to="/about"
              className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill border border-accent text-accent hover:bg-accent hover:text-white transition font-medium"
            >
              About Denise
            </Link>
          </div>

          {/* Referral share — only surfaced post-confirmation, when trust is highest. */}
          {isMagnetFlow && (
            <div className="mt-12 pt-10 border-t border-line/50">
              <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-3 font-medium">
                Pass it along
              </div>
              <p className="text-[15px] text-muted-ink mb-5 max-w-md mx-auto">
                Know someone who'd love this? One share does more for a small
                newsletter than any ad ever will.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-2">
                {channels.map((c) => (
                  <a
                    key={c.key}
                    href={c.href}
                    {...(c.external
                      ? { target: "_blank", rel: "noopener noreferrer" }
                      : {})}
                    onClick={() =>
                      track(events.REFERRAL_SHARE_CLICK, {
                        channel: c.key,
                        placement: "subscribed-thank-you",
                      })
                    }
                    className="inline-flex items-center gap-2 px-5 h-10 rounded-pill border border-line/60 bg-white text-[13px] text-ink hover:border-accent hover:text-accent transition"
                  >
                    {c.label}
                  </a>
                ))}
              </div>
            </div>
          )}

          <p className="mt-10 text-[12px] text-muted-ink/80">
            Trouble finding the email? Check your Promotions or Spam folder.
          </p>
        </Card>
      </section>
    </>
  );
}
