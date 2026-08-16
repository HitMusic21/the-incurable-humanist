"""Unit tests for the Substack HTML sanitizer.

No DB or network — pure functions over fixed markup samples. The samples mirror
the real shapes observed in the live feed: Substack wraps images in
`figure > a > picture > source + img` and decorates them with share-widget
`<button>`/`<svg>` chrome that must not reach the page.
"""

from __future__ import annotations

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
        # The actual content survives.
        assert "<img" in out
        assert "<picture" in out
        assert "<source" in out
        assert "<figcaption>" in out
        assert "Henri-Lucien Doucet" in out

    def test_preserves_responsive_srcset(self):
        """The JSON API's srcset is the reason <picture>/<source> are allowlisted."""
        out = sanitize_substack_html(SUBSTACK_IMAGE_HTML)
        assert "srcset" in out
        assert 'width="1456"' in out and 'height="788"' in out

    def test_neutralizes_xss_vectors(self):
        out = sanitize_substack_html(XSS_HTML)
        for vector in ("<script", "onerror", "javascript:", "<iframe", "<style"):
            assert vector not in out
        assert "<p>safe</p>" in out


class TestSrcsetScrubbing:
    """nh3's url_schemes guards href and src but IGNORES srcset.

    Since srcset is allowlisted on <img>/<source> to keep Substack's responsive
    images, the scheme check for it is ours to own. Found by fuzzing: a clean()
    that correctly stripped `src="javascript:..."` passed
    `srcset="javascript:..."` through untouched.
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
            # One good candidate does not launder a hostile sibling.
            '<img srcset="https://ok/a.png 424w, javascript:alert(1) 848w">',
        ],
    )
    def test_hostile_srcset_is_dropped(self, hostile):
        out = sanitize_substack_html(hostile)
        lowered = out.lower()
        assert "javascript:" not in lowered
        assert "vbscript:" not in lowered
        assert "data:text/html" not in lowered

    def test_substack_cdn_srcset_survives_its_embedded_commas(self):
        """Regression: the scrubber must not shred legitimate CDN URLs.

        Substack's CDN puts literal commas inside one URL's transform params
        (`$s_!YX72!,w_424,c_limit,f_webp`). Splitting candidates on a bare comma
        turned that single URL into scheme-less fragments like `w_424` and
        stripped every responsive image on the site — real markup verified
        against the live feed, where a naive split dropped 36 of 36 srcsets.
        """
        cdn = (
            "https://substackcdn.com/image/fetch/$s_!YX72!,w_424,c_limit,f_webp,"
            "q_auto:good,fl_progressive:steep/https%3A%2F%2Fexample.png"
        )
        html = f'<img src="https://cdn/x.png" srcset="{cdn} 424w, {cdn} 848w">'
        out = sanitize_substack_html(html)
        assert "srcset=" in out, "legitimate CDN srcset was stripped"
        assert "424w" in out and "848w" in out

    def test_relative_urls_are_allowed(self):
        """No scheme means relative, which is safe."""
        out = sanitize_substack_html('<img srcset="/images/a.png 1x, ./b.png 2x">')
        assert "srcset=" in out

    def test_adds_lazy_loading_once(self):
        out = sanitize_substack_html(SUBSTACK_IMAGE_HTML)
        assert out.count('loading="lazy"') == 1
        # Re-sanitizing must not stack a second attribute.
        assert sanitize_substack_html(out).count('loading="lazy"') == 1

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
