// Single source of truth for press coverage.
//
// Consumed by four places:
//   - src/config/site.ts             (re-exported as SITE.press)
//   - src/pages/Press.tsx            (full cards, via SITE.press)
//   - src/pages/Speak.tsx, Links.tsx ("Featured in" outlet-name strip)
//   - scripts/generate-sitemap.mjs   (emits dist/press.json, which the Python
//                                     Worker reads through its ASSETS binding
//                                     to server-render /press)
//
// Written as .mjs for the same reason as speakingTopics.mjs: the Node build
// scripts must import it without a TS-compile step, and the Worker cannot
// import TypeScript at all. Adding an outlet here fans out to every consumer;
// a hand-maintained Python copy would drift on the first addition.
//
// TODO(copy): the `title` and `dek` for Observer and Singulart are drafted in
// the style of the existing entries and need Denise's review — she supplied the
// URLs, not the descriptions.

/** @type {ReadonlyArray<import('./press').PressItem>} */
export const PRESS = [
  {
    outlet: "Observer",
    title: "Venezuela's Art Scene Endures Under Dictatorship",
    dek: "On the cultural market, museums, and what it takes to keep an art scene alive under an authoritarian state.",
    href: "https://observer.com/2026/01/venezuela-art-scene-cultural-market-museums-dictatorship/",
  },
  {
    outlet: "The Art Gorgeous",
    title: "Denise Dao Is The Powerhouse Promoting Latin American Art",
    dek: "Feature article highlighting Denise's role in promoting Latin American artists and cultural advocacy work.",
    href: "https://theartgorgeous.com/denise-dao-is-the-powerhouse-promoting-latin-american-art/",
  },
  {
    outlet: "Singulart Magazine",
    title: "Women in the Art World to Follow on Instagram",
    dek: "Named among the women shaping how contemporary art is discovered, collected, and talked about online.",
    href: "https://www.singulart.com/blog/en/2021/02/26/double-tap-women-in-the-art-world-to-follow-on-instagram/",
  },
  {
    outlet: "La Guía de Caracas",
    title: "Denise Rodriguez Dao Promoviendo Arte",
    dek: "Coverage of Denise's art promotion work and cultural contributions in Latin American communities.",
    // http:// is deliberate — the host does not answer on 443 (verified), so
    // "upgrading" this to https breaks the link.
    href: "http://laguiadecaracas.net/41802/denise-rodriguez-dao-promoviendo-arte/",
  },
];
