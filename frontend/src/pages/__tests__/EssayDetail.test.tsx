import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import EssayDetail from "@/pages/EssayDetail";

const SAMPLE = {
  id: 1,
  title: "A Test Essay",
  slug: "a-test-essay",
  excerpt: "The subtitle line.",
  meta_description: "Meta description for a test essay.",
  cover_image_url: null,
  canonical_url: null,
  status: "published",
  published_at: "2026-06-01T12:00:00Z",
  updated_at: "2026-06-15T12:00:00Z",
  content: "<p>Hello <em>world</em>.</p>",
  content_warning: null,
  view_count: 42,
};

function renderAtSlug(slug: string) {
  return render(
    <MemoryRouter initialEntries={[`/essays/${slug}`]}>
      <Routes>
        <Route path="/essays/:slug" element={<EssayDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("EssayDetail", () => {
  beforeEach(() => {
    // Reset DOM between tests — SEO component leaves head mutations behind.
    document.head.querySelectorAll('[id="tih-jsonld-page"]').forEach((n) => n.remove());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders story content + meta from the API", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(SAMPLE), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    renderAtSlug(SAMPLE.slug);

    await waitFor(() =>
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SAMPLE.title)
    );
    expect(screen.getByText(/subtitle line/i)).toBeInTheDocument();
    // Tiptap HTML gets rendered as real markup.
    expect(document.querySelector(".essay-content em")?.textContent).toBe("world");

    // <SEO> mutates <head> imperatively — assert on document.title + JSON-LD.
    await waitFor(() =>
      expect(document.title).toBe(`${SAMPLE.title} — The Incurable Humanist`)
    );
    const jsonLd = document.getElementById("tih-jsonld-page");
    expect(jsonLd).not.toBeNull();
    const graph = JSON.parse(jsonLd!.textContent || "{}")["@graph"];
    const article = graph.find((n: { "@type": string }) => n["@type"] === "Article");
    expect(article?.headline).toBe(SAMPLE.title);
  });

  it("renders a friendly 404 when the API returns 404", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("nope", { status: 404 }));
    renderAtSlug("missing-slug");
    await screen.findByText(/that essay isn't here/i);
  });

  it("uses canonical_url when the story mirrors an off-site source", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          ...SAMPLE,
          canonical_url: "https://theincurablehumanist.substack.com/p/off-site",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );
    renderAtSlug(SAMPLE.slug);
    await waitFor(() => {
      const link = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
      expect(link?.href).toBe("https://theincurablehumanist.substack.com/p/off-site");
    });
  });
});
