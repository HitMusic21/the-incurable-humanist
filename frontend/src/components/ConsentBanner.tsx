import { useEffect, useState } from "react";
import { getStoredConsent, setConsent } from "@/lib/analytics";

// EU/UK language codes — approximate detection via navigator.language.
// This is a best-effort hint, not a legal geo-fence. Users can always change
// their choice via the footer "Cookie preferences" link (TODO: add link).
const EU_UK_PREFIXES = [
  "at", "be", "bg", "hr", "cy", "cz", "da", "de", "et", "el", "es",
  "fi", "fr", "hu", "ga", "it", "lv", "lt", "mt", "nl", "pl", "pt",
  "ro", "sk", "sl", "sv", "en-gb", "en-ie", "en-mt", "cy-gb",
];

function detectEUUK(): boolean {
  if (typeof navigator === "undefined") return false;
  const langs = [navigator.language, ...(navigator.languages || [])].filter(Boolean);
  return langs.some((l) => {
    const norm = l.toLowerCase();
    return EU_UK_PREFIXES.some((p) => norm === p || norm.startsWith(`${p}-`) || norm.startsWith(`${p}_`));
  });
}

type Mode = "eu-full" | "us-minimal" | "hidden";

export default function ConsentBanner() {
  const [mode, setMode] = useState<Mode>("hidden");

  useEffect(() => {
    const stored = getStoredConsent();
    if (stored) return; // already decided within TTL
    setMode(detectEUUK() ? "eu-full" : "us-minimal");
  }, []);

  if (mode === "hidden") return null;

  if (mode === "eu-full") {
    return (
      <div
        role="dialog"
        aria-labelledby="consent-title"
        aria-describedby="consent-desc"
        className="fixed inset-x-0 bottom-0 z-[100] p-4 md:p-6 pointer-events-none"
      >
        <div className="mx-auto max-w-3xl pointer-events-auto rounded-2xl border border-line bg-white shadow-[0_24px_48px_rgba(0,0,0,0.14)] p-5 md:p-6">
          <div id="consent-title" className="font-serif text-[20px] md:text-[22px] text-ink mb-2">
            Analytics & cookies
          </div>
          <p id="consent-desc" className="text-[14px] md:text-[15px] text-muted-ink leading-relaxed mb-4">
            We use PostHog, Google Analytics, and social pixels to understand what's working.
            None of this is required to read the site — you can decline and everything still
            works.{" "}
            {/* TODO(legal): add /privacy link once policy page exists. */}
          </p>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <button
              onClick={() => {
                setConsent(false);
                setMode("hidden");
              }}
              className="flex-1 h-11 rounded-pill border border-line text-ink hover:border-accent hover:text-accent transition font-medium"
            >
              Reject all
            </button>
            <button
              onClick={() => {
                setConsent(true);
                setMode("hidden");
              }}
              className="flex-1 h-11 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 transition font-medium"
            >
              Accept
            </button>
          </div>
        </div>
      </div>
    );
  }

  // US / other: minimal notice with a single dismiss action.
  // Default to consent granted (US CCPA is opt-out) but expose a clear opt-out.
  return (
    <div
      role="dialog"
      aria-labelledby="consent-title-us"
      className="fixed inset-x-0 bottom-0 z-[100] p-4 md:p-6 pointer-events-none"
    >
      <div className="mx-auto max-w-2xl pointer-events-auto rounded-2xl border border-line bg-white shadow-[0_24px_48px_rgba(0,0,0,0.10)] p-4 md:p-5 flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <p id="consent-title-us" className="text-[13px] md:text-[14px] text-muted-ink leading-relaxed flex-1">
          We use analytics to improve the site. You can opt out — we won't sell or share your data.
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setConsent(false);
              setMode("hidden");
            }}
            className="h-10 px-4 rounded-pill border border-line text-ink hover:border-accent hover:text-accent transition text-[13px] font-medium"
          >
            Opt out
          </button>
          <button
            onClick={() => {
              setConsent(true);
              setMode("hidden");
            }}
            className="h-10 px-4 rounded-pill bg-accent2 text-white hover:brightness-105 transition text-[13px] font-medium"
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
}
