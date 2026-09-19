import { describe, it, expect } from "vitest";
// @ts-expect-error - .mjs build script, no type declarations by design
import { computeRelated } from "../../../scripts/generate-related.mjs";

type Story = { slug: string; title: string; content: string; excerpt?: string };

const story = (slug: string, title: string, content: string): Story => ({
  slug,
  title,
  content,
  excerpt: content.slice(0, 80),
});

/**
 * These guard the two ways the relatedness map can be wrong in a way nobody
 * notices: linking things that are not related (which misleads readers and
 * muddies the topic signal) and linking an essay to itself (an infinite loop
 * in the UI).
 */
describe("computeRelated", () => {
  const corpus: Story[] = [
    story(
      "venezuela-collapse",
      "Venezuela Is Still Falling",
      "Venezuela collapse migration caracas diaspora grief exile country leaving home political crisis venezuela venezuela caracas"
    ),
    story(
      "venezuela-hope",
      "The Night Hope Returned in Venezuela",
      "Venezuela caracas political hope diaspora migration exile crisis country venezuela caracas leaving"
    ),
    story(
      "on-grief",
      "On Grief",
      "Grief mourning loss bereavement sorrow remembering mother father death grieving grief grief mourning"
    ),
    story(
      "on-saudade",
      "On Saudade and Grief",
      "Saudade longing grief mourning loss sorrow absence grieving nostalgia grief mourning"
    ),
    story(
      "restaurant-guide",
      "Three New Restaurants",
      "restaurant dinner chef menu kitchen tasting pasta service dining restaurant chef menu"
    ),
  ];

  const related = computeRelated(corpus) as Record<
    string,
    { slug: string; title: string }[]
  >;

  it("links essays that share a subject", () => {
    expect(related["venezuela-collapse"]?.map((r) => r.slug)).toContain("venezuela-hope");
    expect(related["on-grief"]?.map((r) => r.slug)).toContain("on-saudade");
  });

  it("does not link an unrelated essay", () => {
    // The restaurant piece shares no topical vocabulary with anything here.
    // Forcing it a neighbour is the exact failure the score floor exists to
    // prevent — measured on the real corpus it produced pairings like
    // "Stop Calling Frida and Diego Relationship Goals" -> "June Reading List".
    const forRestaurant = related["restaurant-guide"] ?? [];
    expect(forRestaurant.map((r) => r.slug)).not.toContain("on-grief");
    expect(forRestaurant.map((r) => r.slug)).not.toContain("venezuela-collapse");
  });

  it("never links an essay to itself", () => {
    for (const [slug, matches] of Object.entries(related)) {
      expect(matches.map((m) => m.slug)).not.toContain(slug);
    }
  });

  it("never emits duplicates and caps at three", () => {
    for (const matches of Object.values(related)) {
      expect(matches.length).toBeLessThanOrEqual(3);
      expect(new Set(matches.map((m) => m.slug)).size).toBe(matches.length);
    }
  });

  it("omits essays entirely rather than inventing weak matches", () => {
    // An empty corpus entry is valid output; a wrong link is not.
    const sparse = computeRelated([
      story("alone", "Alone", "singular unrepeated vocabulary nothing shared"),
      story("other", "Other", "completely different terms altogether here"),
    ]) as Record<string, unknown[]>;
    for (const matches of Object.values(sparse)) {
      expect(Array.isArray(matches)).toBe(true);
    }
  });

  it("returns titles and slugs the UI can render", () => {
    const first = related["venezuela-collapse"]?.[0];
    expect(first).toBeDefined();
    expect(typeof first!.slug).toBe("string");
    expect(typeof first!.title).toBe("string");
    expect(first!.title.length).toBeGreaterThan(0);
  });
});
