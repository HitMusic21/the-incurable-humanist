import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render } from "@testing-library/react";
import React from "react";
import { useScrollDepth } from "@/hooks/useScrollDepth";

// Mock the analytics hook so we can assert on track() calls without hitting
// PostHog or the consent gate.
const trackMock = vi.fn();
vi.mock("@/hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    track: trackMock,
    events: {
      ESSAY_SCROLL_75: "essay_scroll_75",
      ESSAY_READ_COMPLETE: "essay_read_complete",
    },
  }),
}));

function Harness({ dwellMs }: { dwellMs?: number }) {
  useScrollDepth({ properties: { slug: "test" }, dwellMs });
  return <div data-testid="target" />;
}

function setScrollGeometry({
  scrollTop,
  clientHeight,
  scrollHeight,
}: {
  scrollTop: number;
  clientHeight: number;
  scrollHeight: number;
}) {
  Object.defineProperty(window, "scrollY", { value: scrollTop, writable: true, configurable: true });
  Object.defineProperty(document.documentElement, "scrollTop", {
    value: scrollTop,
    writable: true,
    configurable: true,
  });
  Object.defineProperty(document.documentElement, "clientHeight", {
    value: clientHeight,
    writable: true,
    configurable: true,
  });
  Object.defineProperty(document.documentElement, "scrollHeight", {
    value: scrollHeight,
    writable: true,
    configurable: true,
  });
  Object.defineProperty(window, "innerHeight", {
    value: clientHeight,
    writable: true,
    configurable: true,
  });
}

describe("useScrollDepth", () => {
  beforeEach(() => {
    trackMock.mockReset();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("fires essay_scroll_75 once when the reader crosses 75%", () => {
    render(<Harness />);
    // Total page 1000, viewport 200, at scrollTop 700 → (700+200)/1000 = 0.9.
    setScrollGeometry({ scrollTop: 700, clientHeight: 200, scrollHeight: 1000 });
    act(() => window.dispatchEvent(new Event("scroll")));

    const seventyFive = trackMock.mock.calls.filter((c) => c[0] === "essay_scroll_75");
    expect(seventyFive).toHaveLength(1);
    expect(seventyFive[0][1]).toMatchObject({ ratio: 0.75, slug: "test" });

    // Fire again — should NOT double.
    act(() => window.dispatchEvent(new Event("scroll")));
    expect(trackMock.mock.calls.filter((c) => c[0] === "essay_scroll_75")).toHaveLength(1);
  });

  it("fires essay_read_complete only after dwell at the bottom", () => {
    vi.useFakeTimers();
    render(<Harness dwellMs={2000} />);
    // At bottom immediately.
    setScrollGeometry({ scrollTop: 800, clientHeight: 200, scrollHeight: 1000 });
    act(() => window.dispatchEvent(new Event("scroll")));

    // Before dwell elapses, no read_complete yet.
    expect(trackMock.mock.calls.some((c) => c[0] === "essay_read_complete")).toBe(false);

    act(() => {
      vi.advanceTimersByTime(2100);
    });
    expect(trackMock.mock.calls.some((c) => c[0] === "essay_read_complete")).toBe(true);
  });

  it("cancels the read timer if the user scrolls back up before dwell", () => {
    vi.useFakeTimers();
    render(<Harness dwellMs={2000} />);
    setScrollGeometry({ scrollTop: 800, clientHeight: 200, scrollHeight: 1000 });
    act(() => window.dispatchEvent(new Event("scroll")));

    // Scroll back up before the 2s dwell.
    act(() => {
      vi.advanceTimersByTime(500);
    });
    setScrollGeometry({ scrollTop: 300, clientHeight: 200, scrollHeight: 1000 });
    act(() => window.dispatchEvent(new Event("scroll")));

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(trackMock.mock.calls.some((c) => c[0] === "essay_read_complete")).toBe(false);
  });
});
