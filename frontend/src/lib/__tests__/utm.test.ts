import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { captureIncomingUTMs, getStoredUTMs, withUTM } from "@/lib/utm";

describe("withUTM", () => {
  it("appends lowercase UTM params to a URL", () => {
    const out = withUTM("https://example.com/path", {
      source: "instagram",
      medium: "organic-social",
      campaign: "Launch-Week",
      content: "Story-A",
    });
    const u = new URL(out);
    expect(u.searchParams.get("utm_source")).toBe("instagram");
    expect(u.searchParams.get("utm_medium")).toBe("organic-social");
    expect(u.searchParams.get("utm_campaign")).toBe("launch-week");
    expect(u.searchParams.get("utm_content")).toBe("story-a");
  });

  it("returns the input unchanged when not a valid URL", () => {
    expect(
      withUTM("not-a-url", { source: "website", medium: "cta" })
    ).toBe("not-a-url");
  });
});

describe("captureIncomingUTMs / getStoredUTMs", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    // jsdom lets us mutate window.location via history API.
    window.history.replaceState({}, "", "/");
  });

  afterEach(() => {
    window.sessionStorage.clear();
  });

  it("persists UTM params from the URL to sessionStorage", () => {
    window.history.replaceState(
      {},
      "",
      "/?utm_source=tiktok&utm_medium=organic-social&utm_campaign=grief-arc"
    );
    const captured = captureIncomingUTMs();
    expect(captured?.source).toBe("tiktok");
    expect(captured?.campaign).toBe("grief-arc");

    const stored = getStoredUTMs();
    expect(stored?.source).toBe("tiktok");
    expect(stored?.medium).toBe("organic-social");
  });

  it("does not clobber a prior capture when the URL has no UTMs", () => {
    window.sessionStorage.setItem(
      "tih_utm",
      JSON.stringify({
        source: "instagram",
        medium: null,
        campaign: null,
        content: null,
        term: null,
      })
    );
    window.history.replaceState({}, "", "/some/inner/page");
    captureIncomingUTMs();
    expect(getStoredUTMs()?.source).toBe("instagram");
  });

  it("warns in dev when an unknown utm_source is captured", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    // import.meta.env.DEV is true in vitest runs.
    window.history.replaceState({}, "", "/?utm_source=fake_source");
    captureIncomingUTMs();
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it("stays silent for allow-listed utm_source values", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    window.history.replaceState({}, "", "/?utm_source=instagram&utm_medium=organic-social");
    captureIncomingUTMs();
    expect(warn).not.toHaveBeenCalled();
    warn.mockRestore();
  });
});
