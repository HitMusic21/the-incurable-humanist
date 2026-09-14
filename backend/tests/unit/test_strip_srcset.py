"""Proof that the srcset migration is markup-only.

The D1 migration in backend/scripts/strip_degenerate_srcset.py rewrites stored
essay HTML in place. It is only safe because `content_hash()` hashes
`plain_text(html)` — "normalized TEXT, deliberately not markup" — so the
hourly substack_sync keeps short-circuiting and does not rewrite all 73 rows,
churning updated_at and poisoning the sitemap's lastmod.

These tests assert that invariant directly, against the real exported corpus
when it is available and against representative fixtures otherwise.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from app.services.html_sanitize import content_hash, plain_text

_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _ROOT / "backend" / "scripts" / "strip_degenerate_srcset.py"
_EXPORT = Path("/tmp/d1_export.json")

_spec = importlib.util.spec_from_file_location("strip_srcset", _SCRIPT)
strip = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(strip)


# Shape taken verbatim from the live corpus.
REAL_MARKUP = (
    "<p>Lead paragraph.</p>"
    '<figure><picture>'
    '<source type="image/webp" srcset="/essay-images/abc.jpg 424w, '
    "/essay-images/abc.jpg 848w, /essay-images/abc.jpg 1272w, "
    '/essay-images/abc.jpg 1456w" sizes="100vw">'
    '<img alt="Edward Hopper, Nighthawks, 1942" loading="lazy" '
    'src="/essay-images/abc.jpg" width="1456" height="788" '
    'srcset="/essay-images/abc.jpg 424w, /essay-images/abc.jpg 848w" '
    'sizes="100vw"></picture>'
    "<figcaption>A caption.</figcaption></figure>"
    "<p>Second paragraph.</p>"
    '<img loading="lazy" src="/essay-images/def.jpg" alt="Second image">'
)


class TestHashStability:
    def test_visible_text_is_untouched(self):
        assert plain_text(strip.fix(REAL_MARKUP)) == plain_text(REAL_MARKUP)

    def test_content_hash_is_unchanged(self):
        """The whole migration rests on this."""
        assert content_hash(strip.fix(REAL_MARKUP)) == content_hash(REAL_MARKUP)

    def test_caption_and_alt_text_survive(self):
        out = strip.fix(REAL_MARKUP)
        assert "A caption." in out
        assert 'alt="Edward Hopper, Nighthawks, 1942"' in out

    @pytest.mark.skipif(not _EXPORT.exists(), reason="no D1 export at /tmp/d1_export.json")
    def test_every_real_essay_keeps_its_hash(self):
        """The same guarantee across all 73 published essays."""
        raw = _EXPORT.read_text(encoding="utf-8")
        rows = json.loads(
            re.search(r'"results":\s*(\[.*?\])\s*,\s*"success"', raw, re.S).group(1)
        )
        assert len(rows) >= 70, f"expected the full corpus, got {len(rows)}"
        for row in rows:
            before = row.get("content") or ""
            if not before:
                continue
            after = strip.fix(before)
            assert content_hash(after) == content_hash(before), f"hash moved: {row['slug']}"


class TestMarkupChanges:
    def test_degenerate_srcset_is_removed(self):
        assert "srcset=" not in strip.fix(REAL_MARKUP)

    def test_sizes_is_removed_with_it(self):
        # sizes="100vw" only made sense alongside real width candidates.
        assert "sizes=" not in strip.fix(REAL_MARKUP)

    def test_picture_is_unwrapped_and_the_webp_lie_is_gone(self):
        out = strip.fix(REAL_MARKUP)
        assert "<picture" not in out
        assert "<source" not in out
        # 175/175 <source type="image/webp"> pointed at a .jpg.
        assert "image/webp" not in out

    def test_img_and_its_dimensions_survive(self):
        out = strip.fix(REAL_MARKUP)
        assert "<img" in out
        assert 'width="1456"' in out and 'height="788"' in out  # CLS protection

    def test_first_image_is_promoted(self):
        out = strip.fix(REAL_MARKUP)
        first = re.search(r"<img\b[^>]*>", out).group(0)
        assert 'fetchpriority="high"' in first
        assert 'loading="lazy"' not in first

    def test_later_images_stay_lazy(self):
        out = strip.fix(REAL_MARKUP)
        later = re.findall(r"<img\b[^>]*>", out)[1:]
        assert later, "fixture should contain a second image"
        for tag in later:
            assert 'loading="lazy"' in tag
            assert "fetchpriority" not in tag

    def test_is_idempotent(self):
        once = strip.fix(REAL_MARKUP)
        assert strip.fix(once) == once


class TestGuards:
    def test_a_real_srcset_is_left_alone(self):
        """Only degenerate srcsets are stripped."""
        real = (
            '<img src="/a-400.jpg" '
            'srcset="/a-400.jpg 400w, /a-800.jpg 800w" sizes="100vw">'
        )
        assert "srcset=" in strip.fix(real)

    def test_a_picture_with_real_variants_is_left_alone(self):
        real = (
            "<picture>"
            '<source type="image/webp" srcset="/a-400.webp 400w, /a-800.webp 800w">'
            '<img src="/a.jpg"></picture>'
        )
        assert "<picture" in strip.fix(real)

    def test_is_degenerate_splits_on_comma_space(self):
        # Substack CDN URLs embed bare commas in transform params; a plain
        # "," split would shred one URL into scheme-less fragments.
        same = "/essay-images/a.jpg 424w, /essay-images/a.jpg 848w"
        assert strip.is_degenerate(same) is True
        assert strip.is_degenerate("/a.jpg 400w, /b.jpg 800w") is False

    def test_verify_aborts_when_text_would_change(self):
        with pytest.raises(SystemExit):
            strip.verify("<p>hello</p>", "<p>goodbye</p>")

    def test_content_without_images_is_untouched(self):
        prose = "<p>No images here at all.</p><h2>A heading</h2>"
        assert strip.fix(prose) == prose
