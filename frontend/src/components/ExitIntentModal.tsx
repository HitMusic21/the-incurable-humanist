import { useCallback, useEffect, useState } from "react";
import SubscribeCTA from "./SubscribeCTA";

const SESSION_KEY = "tih_exit_shown";
const MIN_DWELL_MS = 8000; // don't ambush first-paint bounces

function alreadyShownThisSession(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.sessionStorage.getItem(SESSION_KEY) === "1";
  } catch {
    return true; // fail-closed: don't nag if storage is unavailable
  }
}

function markShown() {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(SESSION_KEY, "1");
  } catch {
    /* ignore */
  }
}

/**
 * Fires the subscribe CTA in a modal when the mouse leaves the viewport at
 * the top edge (classic exit-intent). Once per session, ≥8s after mount.
 *
 * On touch devices the `mouseleave` trigger never fires — that's fine, the
 * inline CTAs cover mobile. No fallback trigger to avoid nagging mobile users.
 */
export default function ExitIntentModal() {
  const [open, setOpen] = useState(false);
  const [mountedAt] = useState(() => Date.now());

  const dismiss = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (alreadyShownThisSession()) return;

    function onMouseOut(e: MouseEvent) {
      if (Date.now() - mountedAt < MIN_DWELL_MS) return;
      // Only the top edge — leaving through the side is typically tab-switching.
      if (e.clientY > 0) return;
      // Ignore transitions between child elements.
      if (e.relatedTarget) return;

      markShown();
      setOpen(true);
      document.removeEventListener("mouseout", onMouseOut);
    }

    document.addEventListener("mouseout", onMouseOut);
    return () => document.removeEventListener("mouseout", onMouseOut);
  }, [mountedAt]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") dismiss();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, dismiss]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="exit-intent-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4"
      onClick={dismiss}
    >
      <div
        className="w-full max-w-lg bg-surface rounded-2xl shadow-[0_24px_48px_rgba(0,0,0,0.24)] border border-line/60 p-6 md:p-8 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={dismiss}
          aria-label="Close"
          className="absolute top-3 right-3 w-8 h-8 rounded-full flex items-center justify-center text-muted-ink hover:text-ink hover:bg-line/30 transition"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            className="w-4 h-4"
            aria-hidden="true"
          >
            <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
          </svg>
        </button>

        <div className="text-[11px] uppercase tracking-[0.18em] text-accent mb-3 font-medium">
          Before you go
        </div>
        <h2
          id="exit-intent-title"
          className="font-serif text-accent2 text-[26px] md:text-[30px] leading-tight mb-4"
        >
          Take the 5-essay reader with you.
        </h2>

        <SubscribeCTA
          variant="inline"
          placement="exit-intent"
          headline=""
          sub="A free PDF of Denise's best pieces — plus the weekly essay. No spam."
          autoFocus
        />
      </div>
    </div>
  );
}
