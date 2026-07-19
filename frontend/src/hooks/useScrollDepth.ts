import { useEffect } from "react";
import { useAnalytics } from "./useAnalytics";

type Options = {
  /** Fires with these properties so PostHog can slice by slug/placement/etc. */
  properties?: Record<string, unknown>;
  /** Milliseconds of dwell required at the bottom before firing the read-complete event. */
  dwellMs?: number;
};

const READ_COMPLETE_DWELL_DEFAULT = 5000;

/**
 * Fires two milestones per page mount:
 *   essay_scroll_75      — user has scrolled ≥ 75% of the document height
 *   essay_read_complete  — user reached the bottom AND stayed there `dwellMs` ms
 *
 * Both events are one-shot per mount and consent-gated (analytics.track() is
 * already a no-op until consent is granted, so we don't repeat that here).
 * Reads document scroll — assumes the essay is the primary scroller (no
 * inner-overflow container). If that changes, take a ref instead.
 */
export function useScrollDepth(options: Options = {}): void {
  const { track, events } = useAnalytics();
  const props = options.properties ?? {};
  const dwellMs = options.dwellMs ?? READ_COMPLETE_DWELL_DEFAULT;

  useEffect(() => {
    if (typeof window === "undefined") return;

    let firedSeventyFive = false;
    let firedRead = false;
    let bottomTimer: ReturnType<typeof setTimeout> | null = null;

    function scrollRatio(): number {
      const doc = document.documentElement;
      const scrolled = window.scrollY || doc.scrollTop || 0;
      const viewport = window.innerHeight || doc.clientHeight || 0;
      const total = doc.scrollHeight || 0;
      // A page shorter than the viewport is trivially "fully read" — ignore.
      if (total <= viewport) return 0;
      return (scrolled + viewport) / total;
    }

    function clearBottomTimer() {
      if (bottomTimer) {
        clearTimeout(bottomTimer);
        bottomTimer = null;
      }
    }

    function onScroll() {
      const ratio = scrollRatio();
      if (!firedSeventyFive && ratio >= 0.75) {
        firedSeventyFive = true;
        track(events.ESSAY_SCROLL_75 ?? "essay_scroll_75", { ratio: 0.75, ...props });
      }
      // Bottom = within 1% of the end (accounts for sub-pixel rounding + rubber banding).
      const atBottom = ratio >= 0.99;
      if (firedRead) return;
      if (atBottom) {
        if (!bottomTimer) {
          bottomTimer = setTimeout(() => {
            firedRead = true;
            track(events.ESSAY_READ_COMPLETE ?? "essay_read_complete", props);
          }, dwellMs);
        }
      } else {
        // Left the bottom before dwell elapsed — reset.
        clearBottomTimer();
      }
    }

    // Fire once on mount in case the page is already scrolled (browser back button, hash link).
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      clearBottomTimer();
    };
    // props is stable-ish per page; caller passes a memoized object if they change slugs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
