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
    "a", "img", "picture", "source",
    "figure", "figcaption", "hr", "code", "pre", "sup", "sub",
}

ALLOWED_ATTRS: dict[str, set[str]] = {
    "a": {"href", "title"},
    "img": {"src", "alt", "width", "height", "loading", "srcset", "sizes"},
    "source": {"srcset", "type", "sizes"},
}

ALLOWED_URL_SCHEMES: set[str] = {"http", "https", "mailto"}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_IMG_OPEN_RE = re.compile(r"<img(?![^>]*\bloading=)")
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
    # See _scrub_srcset: nh3 does not scheme-check srcset, so we do it here.
    cleaned = _SRCSET_RE.sub(_scrub_srcset, cleaned)
    # nh3 filters attributes, it never adds them — so loading="lazy" is a
    # post-pass. Guarded so we never double-apply it.
    return _IMG_OPEN_RE.sub('<img loading="lazy"', cleaned)


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
