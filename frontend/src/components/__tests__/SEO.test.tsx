import { describe, it, expect, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import SEO from "../SEO";

/**
 * Guards the robots directives that gate Google Discover.
 *
 * Discover is an image-led surface: without `max-image-preview:large` Google
 * may show only a thumbnail, which in practice means no Discover placement at
 * all. The directive costs nothing and is the single cheapest requirement for
 * the surface, so it must not be dropped when this meta tag is next edited.
 *
 * This file was empty (0 bytes) before Sep 2026 — SEO.tsx mutates document.head
 * imperatively and had no coverage whatsoever.
 */

const renderSEO = (props: Parameters<typeof SEO>[0]) =>
  render(
    <MemoryRouter>
      <SEO {...props} />
    </MemoryRouter>
  );

const robots = () =>
  document.querySelector('meta[name="robots"]')?.getAttribute("content") ?? "";

afterEach(() => {
  cleanup();
  document.head.querySelectorAll('meta[name="robots"]').forEach((n) => n.remove());
});

describe("SEO robots directives", () => {
  it("opts indexable pages into large image previews (Discover)", () => {
    renderSEO({ title: "T", description: "D", canonical: "https://x.test/a" });
    expect(robots()).toContain("index, follow");
    expect(robots()).toContain("max-image-preview:large");
  });

  it("removes the snippet and video preview limits", () => {
    renderSEO({ title: "T", description: "D", canonical: "https://x.test/a" });
    expect(robots()).toContain("max-snippet:-1");
    expect(robots()).toContain("max-video-preview:-1");
  });

  it("keeps noindex pages fully excluded", () => {
    // /links is noindex by design. A noindex page must NOT advertise image
    // previews — that would be contradictory, and Discover must not surface it.
    renderSEO({
      title: "T",
      description: "D",
      canonical: "https://x.test/links",
      noindex: true,
    });
    expect(robots()).toBe("noindex, nofollow");
    expect(robots()).not.toContain("max-image-preview");
  });

  it("writes exactly one robots tag", () => {
    renderSEO({ title: "T", description: "D", canonical: "https://x.test/a" });
    expect(document.querySelectorAll('meta[name="robots"]').length).toBe(1);
  });
});
