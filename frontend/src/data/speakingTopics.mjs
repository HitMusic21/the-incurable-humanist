// Single source of truth for the /speak/<slug> landing pages.
//
// Consumed by three places:
//   - src/config/site.ts        (React runtime — TopicLanding renders these)
//   - scripts/generate-sitemap.mjs   (build-time — emits <url> per slug)
//   - scripts/prerender.mjs          (build-time — writes dist/speak/<slug>/index.html
//                                     with per-topic meta + Service JSON-LD)
//
// Written as .mjs so Node build scripts can import it directly with no
// TS-compile step; TS/Vite consumes it via the sibling .d.mts type declaration.
// Adding a topic here automatically fans out to all three consumers.

/** @type {ReadonlyArray<import('./speakingTopics').SpeakingTopic>} */
export const SPEAKING_TOPICS = [
  {
    slug: "grief-and-inheritance",
    title: "Grief and Inheritance",
    subtitle: "What we carry when we lose a parent.",
    audience:
      "Cultural centers, literary festivals, grief-adjacent programming, higher-ed.",
    blurb:
      "A talk on grief as inheritance — the private ledger of what a parent leaves behind, and the ways that loss reshapes the rest of a life. Draws on Denise's essays for The Incurable Humanist and her family's history between Caracas, Mexico City, and New York.",
    keywords: ["grief", "loss", "inheritance", "personal essay", "latina writer"],
  },
  {
    slug: "migration-as-grief",
    title: "Migration as a Form of Grief",
    subtitle: "The private ledger of leaving.",
    audience: "Universities, diaspora programming, immigration-focused convenings.",
    blurb:
      "Migration reshuffles love, language, and belonging. This talk traces the emotional architecture of leaving — Caracas to Mexico City to New York — and how the losses of migration become the raw material of art.",
    keywords: ["migration", "diaspora", "venezuela", "latin american literature"],
  },
  {
    slug: "art-as-lifesaver",
    title: "Art as the Lifesaver",
    subtitle: "How making becomes a way of surviving.",
    audience: "Museums, galleries, arts residencies, creative-industry conferences.",
    blurb:
      "Painting, writing, cooking, music — art in any form is the tool through which we endure loss and transform it into meaning. Drawing on Denise's years at Galería RGR in Mexico City and her writing on Latin American modernism.",
    keywords: ["art", "creativity", "resilience", "latin american art"],
  },
  {
    slug: "latin-american-art-and-diaspora",
    title: "Latin American Art & the Diaspora",
    subtitle: "The gallery and the courtroom in conversation.",
    audience: "Cultural institutions, law schools, arts-legal audiences.",
    blurb:
      "A conversation between the gallery and the courtroom: what it takes to represent artists, gallerists, and cultural workers moving between countries — and why the work of moving is itself an act of cultural preservation.",
    keywords: [
      "latin american art",
      "immigration law",
      "artist visas",
      "cultural policy",
    ],
  },
];
