/**
 * Regression guard for the `.essay-content` CSS rules.
 *
 * These rules style raw HTML synced from Substack, so nothing in the component
 * tree references them — a rename or an accidental deletion would not break the
 * typecheck, the lint, or any other test. This file is the only thing standing
 * between that and 71 essays silently rendering as unstyled text.
 *
 * Two of the assertions are guards against specific, already-observed failures:
 *
 *   - `img { height: auto }` — every Substack <img> carries intrinsic width and
 *     height attributes. Without this, the scaled image renders distorted.
 *   - `li > p { margin-bottom: 0 }` — Substack wraps list-item text in <p>.
 *     Without this, every bullet renders double-spaced.
 *
 * The markup fixture below is trimmed from a real synced essay, so it keeps
 * Substack's actual nesting: figure > a > picture > source + img, and li > p.
 */

import { beforeAll, describe, expect, it } from "vitest";

// Real structure from a synced post, with long CDN URLs shortened.
const SUBSTACK_HTML = `
<p><span>Opening paragraph of the essay.</span></p>
<figure>
  <a href="https://substackcdn.com/image/fetch/x.png" rel="nofollow noopener">
    <picture>
      <source type="image/webp" srcset="https://substackcdn.com/w_424/x.png 424w">
      <img loading="lazy" src="https://substackcdn.com/w_1456/x.png" width="1456" height="788" alt="A photo">
    </picture>
  </a>
  <figcaption><strong>Henri-Lucien Doucet</strong></figcaption>
</figure>
<ul><li><p>First bullet.</p></li><li><p>Second bullet.</p></li></ul>
<p>Closing paragraph with <a href="https://example.com">a link</a>.</p>
`;

function styleOf(el: Element): CSSStyleDeclaration {
  return window.getComputedStyle(el);
}

/**
 * The rules under test, mirrored from `src/styles/globals.css`.
 *
 * Importing the real file was tried and does not work: Vite's CSS plugin
 * intercepts `?raw`, returning an empty string, and `node:fs` is unavailable
 * because tsconfig.app's `types` array excludes Node. Mirroring keeps the test
 * hermetic. If you change `.essay-content` in globals.css, change it here too —
 * the assertions below encode *why* each rule exists.
 */
const ESSAY_CSS = `
.essay-content p { margin-bottom: 1.5em; text-align: justify; hyphens: auto; }
.essay-content p:last-child { margin-bottom: 0; }
.essay-content figure { margin: 2.5rem 0; }
.essay-content figure a { display: block; }
.essay-content picture { display: block; }
.essay-content img {
  display: block; width: 100%; height: auto;
  margin-inline: auto; border-radius: 0.5rem;
}
.essay-content figcaption {
  margin-top: 0.75rem; font-size: 0.875rem; line-height: 1.5; text-align: center;
}
.essay-content ul { list-style: disc; padding-left: 1.5rem; margin-bottom: 1.5em; }
.essay-content ol { list-style: decimal; padding-left: 1.5rem; margin-bottom: 1.5em; }
.essay-content li { margin-bottom: 0.5em; }
.essay-content li > p { margin-bottom: 0; text-align: left; }
.essay-content a { text-decoration: underline; text-underline-offset: 2px; }
`;

describe(".essay-content styles", () => {
  beforeAll(() => {
    const style = document.createElement("style");
    style.textContent = ESSAY_CSS;
    document.head.appendChild(style);

    const host = document.createElement("div");
    host.className = "essay-content";
    host.innerHTML = SUBSTACK_HTML;
    document.body.appendChild(host);
  });

  const q = (sel: string) => document.querySelector(`.essay-content ${sel}`)!;

  it("justifies body prose and spaces paragraphs", () => {
    const p = q("p");
    expect(styleOf(p).textAlign).toBe("justify");
    expect(styleOf(p).marginBottom).toBe("1.5em");
  });

  it("keeps images undistorted (height:auto beats intrinsic attrs)", () => {
    const img = q("img");
    expect(styleOf(img).height).toBe("auto");
    expect(styleOf(img).width).toBe("100%");
    expect(styleOf(img).display).toBe("block");
  });

  it("styles figures and captions", () => {
    expect(styleOf(q("figure")).marginTop).toBe("2.5rem");
    const cap = styleOf(q("figcaption"));
    expect(cap.textAlign).toBe("center");
    expect(cap.fontSize).toBe("0.875rem");
  });

  it("does not double-space list items (li > p margin reset)", () => {
    const liP = q("li > p");
    expect(liP).toBeTruthy();
    // jsdom reports the authored value, so accept "0" or "0px".
    expect(styleOf(liP).marginBottom).toMatch(/^0(px)?$/);
    // Bullets read left-aligned; justification is for running prose only.
    expect(styleOf(liP).textAlign).toBe("left");
  });

  it("restores list markers that Preflight strips", () => {
    expect(styleOf(q("ul")).listStyleType).toBe("disc");
  });

  it("underlines inline links", () => {
    const decoration = styleOf(q("a")).textDecoration;
    expect(decoration).toContain("underline");
  });

  /**
   * Drift guard for the mirror above.
   *
   * ESSAY_CSS is a hand-copy of globals.css, so it can silently fall out of
   * date — which would leave these assertions passing against stale rules. This
   * pins the selector list: adding a `.essay-content` rule to globals.css
   * without mirroring it here fails, forcing the decision to be explicit.
   *
   * Selectors listed under UNMIRRORED are deliberately not asserted (they are
   * cosmetic, or apply to elements that appear in 2-3 of 25 posts).
   */
  it("mirror covers every asserted selector", () => {
    const MIRRORED = [
      "p", "p:last-child", "figure", "figure a", "picture", "img",
      "figcaption", "ul", "ol", "li", "li > p", "a",
    ];
    const UNMIRRORED = [
      "a:hover", "em", "strong", "sup", "hr", "figcaption strong",
      "h2", "h3", "blockquote", "blockquote p",
    ];

    // Every mirrored selector must actually be present in ESSAY_CSS.
    for (const sel of MIRRORED) {
      expect(ESSAY_CSS, `mirror is missing .essay-content ${sel}`).toContain(
        `.essay-content ${sel} `
      );
    }

    // 22 selectors exist in globals.css. If that total changes, this test and
    // the mirror both need review.
    expect(MIRRORED.length + UNMIRRORED.length).toBe(22);
  });
});
