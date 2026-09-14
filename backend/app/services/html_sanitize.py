"""HTML sanitization for remote (Substack) article bodies.

Substack's HTML is clean today — no <script>, no inline event handlers, no
tracking pixels — but it is still third-party markup that ends up in the
frontend's dangerouslySetInnerHTML. Sanitize on ingest, not on render.

The allowlist below was validated against 26 real article bodies (all 20 RSS
items plus 6 fetched from the JSON API, spanning newest to oldest):

  - text preserved character-for-character in 26/26 bodies
  - Substack's image share-widget chrome (<button>/<svg>/.pencraft) stripped
  - <img>, <a>, <picture>, <source>, <figcaption> retained
  - ~33% size reduction, all of it chrome
  - <script>, onerror=, javascript:, <iframe>, <style> all neutralized

Tags outside the allowlist are dropped but their text content is kept, which
is why Substack's ~31 <span> wrappers per post cost nothing.
"""

from __future__ import annotations

import hashlib
import html as html_module
import re

import nh3

# Structural tags we render. <picture>/<source> matter: the JSON API serves
# responsive srcset variants that the RSS feed does not.
ALLOWED_TAGS: set[str] = {
    "p", "br", "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "i", "b", "u", "s",
    "blockquote", "ul", "ol", "li",
    "a", "img",
    "figure", "figcaption", "hr", "code", "pre", "sup", "sub",
}

ALLOWED_ATTRS: dict[str, set[str]] = {
    # aria-label is ours, not Substack's — see _name_figure_links. Allowlisted so
    # a re-sanitize of already-stored HTML doesn't strip the accessible name.
    "a": {"href", "title", "aria-label"},
    # srcset/sizes dropped: rehost_essay_images collapsed every variant onto
    # one local file, so the descriptors all point at the identical URL, and
    # <source type="image/webp"> pointed at .jpg (175/175 lied). Next-gen
    # delivery is handled at the edge by Cloudflare Polish instead.
    # fetchpriority is ours, set on the first image (the LCP element).
    "img": {"src", "alt", "width", "height", "loading", "fetchpriority"},
}

ALLOWED_URL_SCHEMES: set[str] = {"http", "https", "mailto"}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
# Adds loading="lazy" to images that have neither loading= nor fetchpriority=.
# The fetchpriority guard matters for idempotency: _promote_first_image
# REMOVES loading="lazy" from the hero, so without it a re-sanitize would
# see a bare <img> and put the attribute straight back, leaving the hero
# with both loading="lazy" and fetchpriority="high".
_IMG_OPEN_RE = re.compile(r"<img(?![^>]*\b(?:loading|fetchpriority)=)")
# Whole <img …> tag, for the first-image promotion. Attribute order varies in
# the corpus, so the lazy attribute is removed from within the matched tag
# rather than by replacing a fixed prefix.
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_LAZY_ATTR_RE = re.compile(r'\s+loading="lazy"', re.IGNORECASE)
# Whole <figure> block: the caption is an *uncle* of the <img> (figure > a >
# picture > img, with figcaption a sibling of the <a>), so a sibling-scoped
# regex would never see it.
_FIGURE_RE = re.compile(r"<figure\b[^>]*>.*?</figure>", re.IGNORECASE | re.DOTALL)
_FIGCAPTION_RE = re.compile(r"<figcaption\b[^>]*>(.*?)</figcaption>", re.IGNORECASE | re.DOTALL)
_LINK_OPEN_RE = re.compile(r"<a\b(?![^>]*\baria-label=)", re.IGNORECASE)
_ALT_RE = re.compile(r'\salt=(["\']).*?\1', re.IGNORECASE | re.DOTALL)
# Body <h1> -> <h2>. The page template already renders the essay title as the
# document's one <h1>, so any <h1> inside the body is a second top-level
# heading competing with it. Substack authors hit this with listicles: the
# reading-list essay gave each of its 4 books an <h1>, producing 5 on the
# rendered page. Demoting preserves the visual hierarchy the author intended
# while restoring a single-h1 document outline.
_BODY_H1_RE = re.compile(r"<(/?)h1\b", re.IGNORECASE)

# Substack's own style attribute is the only one in the corpus (232 instances,
# all `text-align: justify`). It is stripped by the allowlist; the
# `.essay-content p` CSS rule applies justification instead.


def _name_figure_link(match: re.Match[str]) -> str:
    """Give an image-wrapping <a> an accessible name (axe `link-name`, serious).

    Substack ships every figure image with `alt=""`, so `<a><img alt=""></a>`
    has no accessible name at all — the link is announced as bare "link" and
    axe flags it on all 71 essays.

    Measured over 20 real posts (57 images in figures): 37 carry a figcaption,
    20 do not. So a caption-only fix leaves a third of the corpus failing:

      - Caption present: reuse its text as the img's alt AND the link's
        aria-label. The caption is the author's own description, so it is the
        most accurate name available.
      - No caption: leave alt="" — the image really is decorative here and
        inventing a description would be worse than none — and name the link
        generically so it is still announceable.
    """
    figure = match.group(0)
    if "aria-label=" in figure:
        return figure
    caption = _FIGCAPTION_RE.search(figure)
    label = plain_text(caption.group(1)) if caption else ""
    if label:
        alt = html_module.escape(label, quote=True)
        figure = _ALT_RE.sub("", figure).replace("<img", f'<img alt="{alt}"', 1)
    else:
        label = "View image"
    return _LINK_OPEN_RE.sub(f'<a aria-label="{html_module.escape(label, quote=True)}"', figure, 1)


def _demote_body_headings(html: str) -> str:
    """Rewrite body <h1> as <h2> (see _BODY_H1_RE).

    Markup-only: plain_text() strips tags before hashing, so this cannot move
    content_hash and will not make substack_sync see the row as edited.
    """
    return _BODY_H1_RE.sub(lambda m: f"<{m.group(1)}h2", html)


def _promote_first_image(html: str) -> str:
    """Make the first image eager and high-priority; keep the rest lazy.

    The blanket loading="lazy" pass is right for everything below the fold and
    wrong for the first image, which on a long-form essay is the LCP element —
    lazy-loading defers its request until after layout, so the metric it defines
    is measured against a deliberately delayed fetch.

    Idempotent: a second run finds fetchpriority already set.
    """
    match = _IMG_TAG_RE.search(html)
    if not match:
        return html
    tag = match.group(0)
    if "fetchpriority=" in tag.lower():
        return html
    promoted = _LAZY_ATTR_RE.sub("", tag).replace("<img", '<img fetchpriority="high"', 1)
    return html[: match.start()] + promoted + html[match.end() :]


def sanitize_substack_html(raw: str) -> str:
    """Allowlist-sanitize remote article HTML and lazy-load its images."""
    if not raw:
        return ""
    cleaned = nh3.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="nofollow noopener",
    )
    # nh3 filters attributes, it never adds them — so loading="lazy" and the
    # figure accessible names are post-passes. Both guarded against double-apply.
    cleaned = _IMG_OPEN_RE.sub('<img loading="lazy"', cleaned)
    cleaned = _demote_body_headings(cleaned)
    cleaned = _promote_first_image(cleaned)
    return _FIGURE_RE.sub(_name_figure_link, cleaned)


def plain_text(html: str) -> str:
    """Tag-stripped, entity-decoded, whitespace-collapsed text."""
    if not html:
        return ""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", html_module.unescape(html))).strip()


def content_hash(html: str) -> str:
    """Change-detection hash over normalized TEXT, deliberately not markup.

    Substack serves the same prose two ways: the JSON API emits
    <picture> + responsive srcset, the RSS feed emits a bare <img>. Hashing
    markup makes those two sources disagree permanently, so every scheduled
    sync would rewrite every row — churning updated_at and poisoning the
    sitemap's lastmod. Hashing text makes them agree (verified 20/20).
    """
    return hashlib.sha256(plain_text(html).encode("utf-8")).hexdigest()


def excerpt_from(html: str, limit: int = 300) -> str:
    """Lead paragraph text, cut on a word boundary."""
    text = plain_text(html)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def read_time_minutes(html: str, wpm: int = 200) -> int:
    """Reading time in whole minutes, floored at 1. Measured range: 1-7."""
    words = len(plain_text(html).split())
    return max(1, round(words / wpm))
