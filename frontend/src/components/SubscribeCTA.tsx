import { useEffect, useRef, useState } from "react";
import { useAnalytics } from "@/hooks/useAnalytics";
import { SITE } from "@/config/site";
import { API_CONFIG } from "@/config/api";
import { withUTM, getStoredUTMs } from "@/lib/utm";

type Variant = "inline" | "end-of-post" | "primary";

type Props = {
  variant?: Variant;
  placement: string;
  autoFocus?: boolean;
  headline?: string;
  sub?: string;
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Status = "idle" | "loading" | "success" | "error";

export default function SubscribeCTA({
  variant = "inline",
  placement,
  autoFocus,
  headline,
  sub,
}: Props) {
  const { track, events } = useAnalytics();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus && inputRef.current) inputRef.current.focus();
  }, [autoFocus]);

  const fallbackSubscribeLink = withUTM(SITE.substackSubscribeUrl, {
    source: "website",
    medium: "cta",
    campaign: "site-cta-fallback",
    content: placement,
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);
    if (!EMAIL_RE.test(email)) {
      setStatus("error");
      setErrorMsg("Please enter a valid email address.");
      return;
    }
    setStatus("loading");

    const utm = getStoredUTMs();
    const body = {
      email,
      source: placement,
      magnet_requested: true,
      referrer_url: typeof document !== "undefined" ? document.referrer || null : null,
      utm: utm
        ? {
            source: utm.source,
            medium: utm.medium,
            campaign: utm.campaign,
            content: utm.content,
            term: utm.term,
          }
        : null,
    };

    try {
      const res = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.leads.subscribe}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        // Rate limit surfaces here (429) — bubble a friendly message.
        throw new Error(`Signup responded ${res.status}`);
      }

      track(events.NEWSLETTER_SIGNUP, {
        placement,
        variant,
        source: "custom-form",
        utm_source: utm?.source ?? null,
      });
      setStatus("success");
    } catch (err) {
      track("newsletter_signup_error", {
        placement,
        variant,
        error: err instanceof Error ? err.message : "unknown",
      });
      setStatus("error");
      setErrorMsg(
        "We couldn't reach the newsletter service. Try subscribing directly on Substack."
      );
    }
  }

  const container = {
    inline:
      "rounded-2xl border border-line/60 bg-white/70 p-5 md:p-6 shadow-soft",
    "end-of-post":
      "rounded-2xl border border-line/60 bg-surface/70 p-6 md:p-8 my-10 shadow-soft",
    primary:
      "rounded-2xl border border-accent/30 bg-white p-6 md:p-8 shadow-[0_16px_40px_rgba(110,85,128,0.14)]",
  }[variant];

  if (status === "success") {
    return (
      <div className={container} role="status" aria-live="polite">
        <div className="font-serif text-[22px] md:text-[26px] text-accent mb-2">
          Check your inbox.
        </div>
        <p className="text-[15px] text-muted-ink leading-relaxed">
          We just sent you a confirmation link. Click it to unlock the free
          <em> 5-essay starter reader</em> — and to join the Sunday-morning list.
        </p>
      </div>
    );
  }

  return (
    <div className={container}>
      {headline ? (
        <div className="font-serif text-[22px] md:text-[26px] text-ink mb-1">
          {headline}
        </div>
      ) : (
        variant !== "inline" && (
          <div className="font-serif text-[22px] md:text-[26px] text-ink mb-1">
            Start with the 5-essay reader.
          </div>
        )
      )}
      {sub && (
        <p className="text-[14px] text-muted-ink mb-4 leading-relaxed">{sub}</p>
      )}
      {!sub && variant !== "inline" && (
        <p className="text-[14px] text-muted-ink mb-4 leading-relaxed">
          A free PDF of Denise's best five pieces on grief, migration, and art —
          plus the weekly Sunday essay. Unsubscribe anytime.
        </p>
      )}

      <form
        onSubmit={handleSubmit}
        className="flex flex-col sm:flex-row gap-2 sm:gap-3"
      >
        <label className="sr-only" htmlFor={`email-${placement}`}>
          Your email address
        </label>
        <input
          id={`email-${placement}`}
          ref={inputRef}
          type="email"
          inputMode="email"
          autoComplete="email"
          required
          placeholder="you@example.com"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (status === "error") setStatus("idle");
          }}
          disabled={status === "loading"}
          className="flex-1 h-12 px-4 rounded-pill border border-line bg-white text-ink placeholder-muted-ink/70 focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/30 transition"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="inline-flex items-center justify-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white font-medium shadow-soft hover:brightness-105 active:brightness-95 disabled:opacity-70 transition"
        >
          {status === "loading" ? "Sending…" : "Send me the reader"}
        </button>
      </form>

      {errorMsg && (
        <div className="mt-3 text-[13px] text-accent" role="alert">
          {errorMsg}{" "}
          <a
            href={fallbackSubscribeLink}
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 text-accent2 hover:text-accent"
          >
            Open Substack →
          </a>
        </div>
      )}

      {status !== "loading" && !errorMsg && (
        <p className="mt-3 text-[12px] text-muted-ink/80">
          Free · Weekly · Unsubscribe anytime
        </p>
      )}
    </div>
  );
}
