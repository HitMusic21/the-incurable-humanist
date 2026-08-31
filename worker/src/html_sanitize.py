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

import bleach

# Structural tags we render. <picture>/<source> matter: the JSON API serves
# responsive srcset variants that the RSS feed does not.
ALLOWED_TAGS: set[str] = {
    "p", "br", "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "i", "b", "u", "s",
    "blockquote", "ul", "ol", "li",
    "a", "img", "picture", "source",
    "figure", "figcaption", "hr", "code", "pre", "sup", "sub",
}

ALLOWED_ATTRS: dict[str, set[str]] = {
    # aria-label and rel are ours, not Substack's — see _name_figure_links and
    # the _LINK_NO_REL_RE pass. Allowlisted so a re-sanitize of already-stored
    # HTML doesn't strip the accessible name or the rel hardening.
    "a": {"href", "title", "aria-label", "rel"},
    "img": {"src", "alt", "width", "height", "loading", "srcset", "sizes"},
    "source": {"srcset", "type", "sizes"},
}

ALLOWED_URL_SCHEMES: set[str] = {"http", "https", "mailto"}

# HTML "raw text" / escapable-raw-text elements. Their contents are character
# data, so a tag-only strip would leak the code as prose — see
# _strip_raw_text_elements.
_RAW_TEXT_RE = re.compile(
    r"<(script|style|template|noscript|title|textarea)\b[^>]*>.*?</\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_RAW_TEXT_OPEN_RE = re.compile(
    r"<(script|style|template|noscript|title|textarea)\b[^>]*>.*",
    re.IGNORECASE | re.DOTALL,
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_IMG_OPEN_RE = re.compile(r"<img(?![^>]*\bloading=)")
# Whole <figure> block: the caption is an *uncle* of the <img> (figure > a >
# picture > img, with figcaption a sibling of the <a>), so a sibling-scoped
# regex would never see it.
_FIGURE_RE = re.compile(r"<figure\b[^>]*>.*?</figure>", re.IGNORECASE | re.DOTALL)
_FIGCAPTION_RE = re.compile(r"<figcaption\b[^>]*>(.*?)</figcaption>", re.IGNORECASE | re.DOTALL)
_LINK_OPEN_RE = re.compile(r"<a\b(?![^>]*\baria-label=)", re.IGNORECASE)
# Guarded against double-apply so re-sanitizing stored HTML is idempotent.
_LINK_NO_REL_RE = re.compile(r"<a\b(?![^>]*\brel=)", re.IGNORECASE)
_ALT_RE = re.compile(r'\salt=(["\']).*?\1', re.IGNORECASE | re.DOTALL)
# Captures a whole srcset="..." / srcset='...' attribute so it can be dropped
# wholesale when any candidate URL carries a disallowed scheme.
_SRCSET_RE = re.compile(r"\ssrcset=([\"'])(.*?)\1", re.IGNORECASE | re.DOTALL)
# Candidate separator: a comma followed by whitespace. Substack's CDN embeds
# bare commas inside a single URL's transform params, so a plain "," split
# would shred one legitimate URL into scheme-less fragments.
_SRCSET_SPLIT_RE = re.compile(r",\s+")

# Substack's own style attribute is the only one in the corpus (232 instances,
# all `text-align: justify`). It is stripped by the allowlist; the
# `.essay-content p` CSS rule applies justification instead.


def _scrub_srcset(match: re.Match[str]) -> str:
    """Drop a srcset unless every candidate URL uses an allowed scheme.

    nh3's `url_schemes` only guards `href` and `src` — it passes `srcset`
    through untouched, so `srcset="javascript:alert(1)"` survives an otherwise
    correct clean(). We allowlist `srcset` on <img>/<source> to keep Substack's
    responsive images, which means we own this check.

    A srcset is a comma-separated list of "<url> <descriptor>" pairs. Rejecting
    the whole attribute (rather than filtering candidates) is deliberate: a
    partly-hostile srcset is not something to salvage, and dropping it degrades
    to the plain `src`, which nh3 has already validated.

    Splitting on a bare comma is WRONG here. Substack's CDN puts literal commas
    inside a single URL's transform params:

        https://substackcdn.com/image/fetch/$s_!YX72!,w_424,c_limit,f_webp/...

    A bare split turns that one URL into fragments like "w_424", which have no
    scheme and would fail the check — silently stripping every legitimate
    responsive image. Split on the real delimiter instead: a comma that follows
    a descriptor and precedes the next URL, i.e. comma + whitespace.
    """
    value = match.group(2)
    for candidate in _SRCSET_SPLIT_RE.split(value):
        stripped = candidate.strip()
        if not stripped:
            continue
        url = stripped.split()[0]
        scheme = url.split(":", 1)[0].lower().strip() if ":" in url else ""
        # A scheme-relative or path-relative URL has no scheme, which is safe.
        # Guard against "javascript" appearing before a path-only colon by
        # requiring the scheme to look like a scheme (no slash before the colon).
        if scheme and "/" not in scheme and scheme not in ALLOWED_URL_SCHEMES:
            return ""
    return match.group(0)


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


def _strip_raw_text_elements(raw: str) -> str:
    """Drop <script>/<style>/… *with their text content*.

    This exists because bleach and nh3 differ here, and the difference is a
    content bug rather than a security one. `bleach.clean(strip=True)` removes
    the disallowed TAG but keeps its character data, so

        <p>hi</p><script>alert(1)</script>   ->  <p>hi</p>alert(1)
        <style>body{}</style><p>keep</p>     ->  body{}<p>keep</p>

    i.e. code leaks into the rendered prose (and into excerpt/content_hash).
    nh3 drops the subtree outright. Pre-stripping the HTML "raw text" elements
    restores nh3's behaviour before bleach ever sees them.

    The second pass catches an *unclosed* raw-text tag, where everything to the
    end of the document is character data and would otherwise survive.

    Verified against 25 real essay bodies: content_hash matches nh3 25/25, so
    swapping sanitizers does not rewrite existing rows on the next sync.
    """
    raw = _RAW_TEXT_RE.sub("", raw)
    return _RAW_TEXT_OPEN_RE.sub("", raw)


def sanitize_substack_html(raw: str) -> str:
    """Allowlist-sanitize remote article HTML and lazy-load its images."""
    if not raw:
        return ""
    cleaned = bleach.clean(
        _strip_raw_text_elements(raw),
        tags=ALLOWED_TAGS,
        attributes={tag: list(attrs) for tag, attrs in ALLOWED_ATTRS.items()},
        protocols=ALLOWED_URL_SCHEMES,
        strip=True,
        strip_comments=True,
    )
    # bleach has no `link_rel=` equivalent to nh3's, so add rel ourselves.
    # Every <a> here is an outbound Substack link opened from our origin;
    # without rel="noopener" the target gets a live window.opener handle.
    cleaned = _LINK_NO_REL_RE.sub('<a rel="nofollow noopener"', cleaned)
    # See _scrub_srcset: the allowlist does not scheme-check srcset, so we do.
    cleaned = _SRCSET_RE.sub(_scrub_srcset, cleaned)
    # nh3 filters attributes, it never adds them — so loading="lazy" and the
    # figure accessible names are post-passes. Both guarded against double-apply.
    cleaned = _IMG_OPEN_RE.sub('<img loading="lazy"', cleaned)
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
