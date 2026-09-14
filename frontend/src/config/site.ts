import { SPEAKING_TOPICS } from "@/data/speakingTopics.mjs";
import { PRESS } from "@/data/press.mjs";

export const SITE = {
  brand: "THE INCURABLE HUMANIST",
  // Drives BOTH the header (shell/App.tsx) and the footer (components/Footer.tsx).
  // Privacy is deliberately absent — it is a footer-tier link, added there directly.
  // "WRITING" keeps the /archive URL: that path carries the site's inbound links,
  // sits at sitemap priority 0.9, and is the breadcrumb parent of all 73 essays.
  // The label changed; the URL did not.
  nav: [
    { label: "HOME", to: "/" },
    { label: "ABOUT", to: "/about" },
    { label: "WRITING", to: "/archive" },
    { label: "SPEAKING", to: "/speak" },
    { label: "LISTENING", to: "/listen" },
    { label: "PRESS", to: "/press" }
  ],
  // Single contact address. `bookingEmail: "booking@…"` was removed Sep 2026
  // when Denise redirected speaking enquiries here — /speak and the four
  // /speak/:topic pages had been its only consumers.
  email: "info@theincurablehumanist.com",
  substackUrl: "https://theincurablehumanist.substack.com",
  substackSubscribeUrl: "https://theincurablehumanist.substack.com/subscribe",
  // Playlist IDs only — SpotifyPlaylist.tsx builds the /embed/ URL from each.
  // Storing the share URL instead is the common mistake: pasted straight into
  // an iframe it renders the full web player rather than the embed.
  //
  // A LIST, not a single ID: Denise added the Autumn playlist alongside the
  // original rather than replacing it, and expects both on /listen. Titles are
  // the real Spotify names (checked against the oEmbed endpoint), so they match
  // what a reader sees after clicking through.
  //
  // Order is render order. Newest first — the seasonal playlist is the current
  // one and the evergreen list keeps its place below.
  spotifyPlaylists: [
    { id: "4eXyRJSfghSHfTblbGzB5T", title: "The Incurable Humanist's Autumn Playlist" },
    { id: "0G5Z5masq2ajzCP6nUHCBd", title: "The Incurable Humanist" },
  ],
  siteUrl: "https://theincurablehumanist.com",
  // Rendered as icons by Footer.tsx and Home.tsx, and mirrored into the
  // Person node's `sameAs` in src/lib/schemaNodes.mjs — add to both or the
  // entity graph drifts from what the page shows.
  socials: {
    instagram: "https://www.instagram.com/theincurablehumanist/",
    tiktok: "https://www.tiktok.com/@theincurablehumanist",
    facebook: "https://www.facebook.com/profile.php?id=61581842306462",
    linkedin: "https://www.linkedin.com/company/the-incurable-humanist/about/",
    x: "https://x.com/TheIncurableHum",
    youtube: "https://www.youtube.com/@TheIncurableHumanist",
    // Denise sent a pin.it link, which is a BOARD INVITE — it redirects to
    // ?invite_code=…&sender=… and would invite every visitor to collaborate
    // on her board. This is the bare profile the invite resolves to.
    pinterest: "https://www.pinterest.com/0ab2scauec8t3vil0u5l871wkeudxo/"
  },
  // Press coverage lives in src/data/press.mjs so the Node build scripts and
  // the Python Worker can read the same list — see that file's header.
  press: PRESS,
  hero: {
    title: "The Incurable Humanist",
    byline: "By Denise Rodriguez Dao",
    tagline: "Exploring grief, migration, and art"
  },
  // TODO(copy): confirm final wording with Denise.
  // `positioning` is the DESCRIPTIVE string: it feeds meta descriptions, OG and
  // Twitter tags, and the WebSite node's `description` in JSON-LD. It is not
  // rendered as visible page copy.
  positioning:
    "Grief, migration, and art — and what gets inherited anyway.",
  // `heroTagline` is what a reader actually sees on the homepage. Split from
  // `positioning` in Aug 2026 when Denise asked to drop "— and what gets
  // inherited anyway" from the visible copy while keeping it in search results.
  // Changing one no longer silently changes the other.
  heroTagline: "Grief, migration, and art.",
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
    // The press-kit button (and its never-created /press-kit.pdf, which 404'd
    // for as long as it shipped) was removed at Denise's request, Sep 2026.
    //
    // MUST be the youtube-nocookie EMBED url, not a watch?v= link: YouTube
    // serves watch pages with X-Frame-Options: SAMEORIGIN, so an iframe
    // pointed at one renders a silently blank box. Same trap as the Spotify
    // share-vs-embed URL noted above.
    voicesForVenezuelaUrl:
      "https://www.youtube-nocookie.com/embed/wimKS7SzHwE" as string | null
  },
  // SEO landing pages per speaking topic — each becomes /speak/<slug> with
  // its own Article/Service JSON-LD. Single source of truth in
  // src/data/speakingTopics.mjs so build scripts (generate-sitemap.mjs +
  // prerender.mjs) consume the same list without a TS toolchain.
  speakingTopics: SPEAKING_TOPICS,
};
