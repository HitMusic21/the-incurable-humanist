import { SPEAKING_TOPICS } from "@/data/speakingTopics.mjs";

export const SITE = {
  brand: "THE INCURABLE HUMANIST",
  nav: [
    { label: "ARCHIVE", to: "/archive" },
    { label: "LISTEN", to: "/listen" },
    { label: "SPEAK", to: "/speak" },
    { label: "ABOUT", to: "/about" }
  ],
  email: "info@theincurablehumanist.com",
  bookingEmail: "booking@theincurablehumanist.com",
  substackUrl: "https://theincurablehumanist.substack.com",
  substackSubscribeUrl: "https://theincurablehumanist.substack.com/subscribe",
  // Playlist ID only — Listen.tsx builds the /embed/ URL from it. Storing the
  // share URL instead is the common mistake: pasted straight into an iframe it
  // renders the full web player rather than the embed.
  spotifyPlaylistId: "0G5Z5masq2ajzCP6nUHCBd" as string | null,
  youtubeUrl: null as string | null,
  siteUrl: "https://theincurablehumanist.com",
  socials: {
    instagram: "https://www.instagram.com/theincurablehumanist/",
    tiktok: "https://www.tiktok.com/@theincurablehumanist",
    facebook: "https://www.facebook.com/profile.php?id=61581842306462",
    linkedin: "https://www.linkedin.com/company/the-incurable-humanist/about/",
    x: "https://x.com/TheIncurableHum"
  },
  press: [
    {
      outlet: "The Art Gorgeous",
      title: "Denise Dao Is The Powerhouse Promoting Latin American Art",
      dek: "Feature article highlighting Denise's role in promoting Latin American artists and cultural advocacy work.",
      href: "https://theartgorgeous.com/denise-dao-is-the-powerhouse-promoting-latin-american-art/"
    },
    {
      outlet: "Click Magazine NYC",
      title: "For the Love of Art",
      dek: "An in-depth profile exploring Denise's passion for art and her multifaceted career bridging law and culture.",
      href: "https://clickmagazinenyc.com/for-the-love-of-art/denisedaoart"
    },
    {
      outlet: "La Guía de Caracas",
      title: "Denise Rodriguez Dao Promoviendo Arte",
      dek: "Coverage of Denise's art promotion work and cultural contributions in Latin American communities.",
      href: "http://laguiadecaracas.net/41802/denise-rodriguez-dao-promoviendo-arte/"
    }
  ],
  hero: {
    title: "The Incurable Humanist",
    byline: "By Denise Rodriguez Dao",
    tagline: "Exploring grief, migration, and art"
  },
  // TODO(copy): confirm final wording with Denise.
  positioning:
    "Grief, migration, and art — and what gets inherited anyway.",
  // TODO(content): replace with the three "truest expression" essays + the Venezuela piece.
  // Order below is the intended editorial ranking on the Archive page.
  bestOfEssays: [
    {
      theme: "Grief",
      title: "[TODO: Grief essay title]",
      dek: "[TODO: one-sentence editorial dek — why this essay is the truest expression of grief in the archive.]",
      href: "https://theincurablehumanist.substack.com/"
    },
    {
      theme: "Migration",
      title: "[TODO: Migration essay title]",
      dek: "[TODO: one-sentence editorial dek.]",
      href: "https://theincurablehumanist.substack.com/"
    },
    {
      theme: "Art",
      title: "[TODO: Art essay title]",
      dek: "[TODO: one-sentence editorial dek.]",
      href: "https://theincurablehumanist.substack.com/"
    },
    {
      theme: "Venezuela",
      title: "[TODO: Venezuela essay title]",
      dek: "[TODO: the piece that performed best — one-sentence dek.]",
      href: "https://theincurablehumanist.substack.com/"
    }
  ],
  // TODO(content): confirm exact wording of the four signature topics.
  speaker: {
    tagline: "Booking Fall 2026 and Spring 2027 dates now.",
    topics: [
      {
        title: "Grief as Inheritance",
        dek: "What we carry when we lose a parent — and why the losing itself is a form of migration."
      },
      {
        title: "Migration as a Form of Grief",
        dek: "The private ledger of leaving: Caracas to Mexico City to New York, and what stays behind."
      },
      {
        title: "Art as the Lifesaver",
        dek: "How art — writing, painting, cooking, music — becomes the tool through which we endure and transform loss."
      },
      {
        title: "Latin American Art & the Diaspora",
        dek: "A conversation between the gallery and the courtroom: representing artists, gallerists, and cultural workers navigating displacement."
      }
    ],
    // TODO(asset): add press-kit.pdf to /public/ once Denise provides it.
    pressKitUrl: "/press-kit.pdf",
    // TODO(asset): add Voices for Venezuela clip URL once recording is available.
    voicesForVenezuelaUrl: null as string | null
  },
  // SEO landing pages per speaking topic — each becomes /speak/<slug> with
  // its own Article/Service JSON-LD. Single source of truth in
  // src/data/speakingTopics.mjs so build scripts (generate-sitemap.mjs +
  // prerender.mjs) consume the same list without a TS toolchain.
  speakingTopics: SPEAKING_TOPICS,
};
