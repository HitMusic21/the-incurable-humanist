"""Unit tests for the Substack HTML sanitizer.

No DB or network — pure functions over fixed markup samples. The samples mirror
the real shapes observed in the live feed: Substack wraps images in
`figure > a > picture > source + img` and decorates them with share-widget
`<button>`/`<svg>` chrome that must not reach the page.
"""

from __future__ import annotations

import re

import pytest
from app.services.html_sanitize import (
    content_hash,
    excerpt_from,
    plain_text,
    read_time_minutes,
    sanitize_substack_html,
)

# Trimmed from a real post: the widget chrome Substack injects next to images.
SUBSTACK_IMAGE_HTML = (
    '<figure><a class="image-link image2" href="https://substackcdn.com/image/fetch/x.png" '
    'data-component-name="Image2ToDOM"><div class="image2-inset"><picture>'
    '<source type="image/webp" srcset="https://substackcdn.com/w_424/x.png 424w">'
    '<img src="https://substackcdn.com/w_1456/x.png" width="1456" height="788" alt="A photo">'
    '</picture><div class="pencraft pc-display-flex">'
    '<button tabindex="0" type="button" class="pencraft icon-container restack-image">'
    '<svg xmlns="http://www.w3.org/2000/svg"><path d="M1 2"></path></svg></button>'
    "</div></div></a><figcaption><strong>Henri-Lucien Doucet</strong></figcaption></figure>"
)

XSS_HTML = (
    "<p>safe</p><script>alert(1)</script><img src=x onerror=alert(2)>"
    '<a href="javascript:alert(3)">bad link</a><iframe src="//evil"></iframe>'
    "<style>body{display:none}</style>"
)


class TestSanitize:
    def test_strips_widget_chrome_but_keeps_the_image(self):
        out = sanitize_substack_html(SUBSTACK_IMAGE_HTML)
        assert "<button" not in out
        assert "<svg" not in out
        assert "pencraft" not in out
        assert "tabindex" not in out
        # The actual content survives. <picture>/<source> are deliberately
        # dropped now (see TestSrcsetIsRemoved) — the <img> they wrapped is
        # what carries the image, and it is kept.
        assert "<img" in out
        assert "<picture" not in out
        assert "<source" not in out
        assert "<figcaption>" in out
        assert "Henri-Lucien Doucet" in out

    def test_drops_srcset_but_keeps_the_image_and_its_dimensions(self):
        """srcset is no longer allowlisted (see TestSrcsetIsRemoved), but the
        intrinsic dimensions must survive — they are what prevents CLS."""
        out = sanitize_substack_html(SUBSTACK_IMAGE_HTML)
        assert "srcset" not in out
        assert 'width="1456"' in out and 'height="788"' in out

    def test_neutralizes_xss_vectors(self):
        out = sanitize_substack_html(XSS_HTML)
        for vector in ("<script", "onerror", "javascript:", "<iframe", "<style"):
            assert vector not in out
        assert "<p>safe</p>" in out

    def test_keeps_text_of_dropped_tags(self):
        """Substack wraps prose in <span>; the tag goes, the words stay."""
        out = sanitize_substack_html("<p><span>kept text</span></p>")
        assert "kept text" in out
        assert "<span" not in out

    def test_external_links_get_rel(self):
        out = sanitize_substack_html('<a href="https://example.com">x</a>')
        assert "nofollow" in out and "noopener" in out

    def test_empty_input(self):
        assert sanitize_substack_html("") == ""


class TestSrcsetIsRemoved:
    """srcset and <picture>/<source> are no longer allowlisted.

    They only earned their place while images were hotlinked from Substack's
    CDN. rehost_essay_images collapsed every responsive variant onto ONE local
    file, so the surviving descriptors all pointed at the identical URL — four
    identical candidates plus sizes="100vw", telling the browser to reserve a
    full-viewport slot for an image with one resolution. Worse, every
    <source type="image/webp"> pointed at a .jpg (175/175 on the live corpus).

    Dropping them from the allowlist also subsumes the old _scrub_srcset pass:
    the sanitizer's url_schemes check ignores srcset, so that function existed
    to scheme-check it by hand. With the attribute gone, hostile payloads go
    with it. Cloudflare Polish handles next-gen formats at the edge instead.
    """

    @pytest.mark.parametrize(
        "hostile",
        [
            '<img srcset="javascript:alert(1)">',
            "<img srcset='javascript:alert(1)'>",
            '<IMG SRCSET="JavaScript:alert(1)">',
            '<source srcset="javascript:alert(1)" type="image/webp">',
            '<img srcset="vbscript:msgbox(1) 1x">',
            '<img srcset="data:text/html;base64,PHN2Zz4= 1x">',
            '<img srcset="https://ok/a.png 424w, javascript:alert(1) 848w">',
        ],
    )
    def test_hostile_srcset_is_dropped(self, hostile):
        out = sanitize_substack_html(hostile)
        lowered = out.lower()
        assert "srcset" not in lowered
        assert "javascript:" not in lowered
        assert "vbscript:" not in lowered
        assert "data:text/html" not in lowered

    def test_srcset_and_sizes_are_always_stripped(self):
        out = sanitize_substack_html(
            '<img src="/a.jpg" srcset="/a.jpg 424w, /a.jpg 848w" sizes="100vw">'
        )
        assert "srcset" not in out
        assert "sizes" not in out
        assert 'src="/a.jpg"' in out, "the real src must survive"

    def test_picture_and_source_are_dropped_but_the_img_survives(self):
        out = sanitize_substack_html(
            '<picture><source type="image/webp" srcset="/a.jpg 424w">'
            '<img src="/a.jpg" alt="A photo"></picture>'
        )
        assert "<picture" not in out
        assert "<source" not in out
        assert "image/webp" not in out
        assert 'src="/a.jpg"' in out
        assert 'alt="A photo"' in out

    def test_dimensions_survive_for_cls(self):
        out = sanitize_substack_html('<img src="/a.jpg" width="1456" height="788">')
        assert 'width="1456"' in out and 'height="788"' in out

    def test_first_image_is_eager_and_high_priority(self):
        """The first image is the LCP element; lazy-loading it defers the very
        fetch the metric measures."""
        out = sanitize_substack_html('<p>x</p><img src="/1.jpg"><p>y</p><img src="/2.jpg">')
        tags = re.findall(r"<img\b[^>]*>", out)
        assert 'fetchpriority="high"' in tags[0]
        assert 'loading="lazy"' not in tags[0]
        assert 'loading="lazy"' in tags[1]
        assert "fetchpriority" not in tags[1]

    def test_lazy_loading_is_applied_once_and_is_idempotent(self):
        out = sanitize_substack_html(SUBSTACK_IMAGE_HTML)
        again = sanitize_substack_html(out)
        assert again == out, "re-sanitizing stored HTML must be a no-op"
        # The hero is promoted rather than lazy, so no lazy attribute stacks on it.
        assert again.count('fetchpriority="high"') == 1


class TestFigureLinkNames:
    """axe `link-name` (serious) x2 on every one of the 71 essays.

    Substack ships `alt=""`, so `<figure><a><img alt=""></a></figure>` has no
    accessible name. Measured over 20 real posts (57 images in figures): 37
    have a figcaption to borrow, 20 have none — hence two branches.
    """

    def test_caption_becomes_alt_and_link_name(self):
        out = sanitize_substack_html(SUBSTACK_IMAGE_HTML)
        assert 'alt="Henri-Lucien Doucet"' in out
        assert 'aria-label="Henri-Lucien Doucet"' in out

    def test_caption_markup_is_stripped_from_the_attribute(self):
        """The caption's own <strong>/<em> must not leak into an attribute."""
        html = (
            "<figure><a href='https://x/'><img src='https://x/a.png' alt=''></a>"
            "<figcaption>Edward Hopper, <em>Nighthawks, </em>1942</figcaption></figure>"
        )
        out = sanitize_substack_html(html)
        assert 'aria-label="Edward Hopper, Nighthawks, 1942"' in out
        assert "<em>" in out, "the caption itself keeps its markup"

    def test_quotes_in_caption_are_escaped(self):
        html = (
            "<figure><a href='https://x/'><img src='https://x/a.png' alt=''></a>"
            '<figcaption>She said "hello"</figcaption></figure>'
        )
        out = sanitize_substack_html(html)
        assert 'aria-label="She said &quot;hello&quot;"' in out
        assert 'alt="She said &quot;hello&quot;"' in out
        assert 'She said "hello"</figcaption>' in out, "visible caption text is untouched"

    def test_captionless_figure_keeps_empty_alt_and_gets_generic_name(self):
        """Nothing to borrow — the image is decorative, so don't invent a description."""
        html = "<figure><a href='https://x/'><img src='https://x/a.png' alt=''></a></figure>"
        out = sanitize_substack_html(html)
        assert 'aria-label="View image"' in out
        assert 'alt=""' in out

    @pytest.mark.parametrize(
        "html",
        [
            SUBSTACK_IMAGE_HTML,
            "<figure><a href='https://x/'><img src='https://x/a.png' alt=''></a></figure>",
        ],
    )
    def test_does_not_double_apply(self, html):
        """Re-sanitizing stored HTML must be a no-op, not a second aria-label."""
        once = sanitize_substack_html(html)
        assert sanitize_substack_html(once) == once
        assert once.count("aria-label") == 1

    def test_leaves_prose_links_alone(self):
        """Only figure links are renamed — inline links already have text."""
        out = sanitize_substack_html('<p><a href="https://example.com">read this</a></p>')
        assert "aria-label" not in out


class TestContentHash:
    def test_ignores_image_markup_differences(self):
        """The load-bearing property.

        Substack serves the same prose two ways: the JSON API emits
        <picture> + srcset, RSS emits a bare <img>. Hashing markup would mark
        every row changed on every scheduled sync.
        """
        api = '<p>Same words.</p><picture><source srcset="a.png 424w"><img src="b.png"></picture>'
        rss = '<p>Same words.</p><img src="b.png">'
        assert content_hash(api) == content_hash(rss)

    def test_detects_real_text_change(self):
        assert content_hash("<p>original</p>") != content_hash("<p>edited</p>")

    def test_ignores_entity_encoding(self):
        """RSS escapes curly quotes; the API does not."""
        assert content_hash("<p>Denise&#8217;s</p>") == content_hash("<p>Denise’s</p>")

    def test_ignores_whitespace_noise(self):
        assert content_hash("<p>a  b</p>") == content_hash("<p>a\n\nb</p>")


class TestDerivedFields:
    def test_plain_text_strips_and_collapses(self):
        assert plain_text("<p>one</p>  <p>two</p>") == "one two"

    def test_excerpt_cuts_on_word_boundary(self):
        html = "<p>" + ("word " * 200) + "</p>"
        out = excerpt_from(html, limit=50)
        assert len(out) <= 51  # +1 for the ellipsis
        assert out.endswith("…")
        assert not out[:-1].endswith(" wor")  # no mid-word cut

    def test_excerpt_short_text_unchanged(self):
        assert excerpt_from("<p>short</p>", limit=50) == "short"

    def test_read_time_floors_at_one(self):
        assert read_time_minutes("<p>tiny</p>") == 1

    def test_read_time_scales(self):
        # 600 words at 200wpm -> 3 min
        assert read_time_minutes("<p>" + ("w " * 600) + "</p>") == 3
