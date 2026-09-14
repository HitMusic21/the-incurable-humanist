"""Strip meaningless responsive-image markup from stored essay HTML.

WHY
---
Substack emitted ~8.6 srcset variants per image, all wrapping the SAME upstream
original. `rehost_essay_images.py` deliberately collapsed every variant onto one
local file (its docstring calls this out), which left behind a srcset whose
width descriptors all point at the identical URL:

    srcset="/essay-images/abc.jpg 424w, /essay-images/abc.jpg 848w,
            /essay-images/abc.jpg 1272w, /essay-images/abc.jpg 1456w"
    sizes="100vw"

That is not a responsive image. It is four identical candidates plus a `sizes`
hint telling the browser to reserve a full-viewport slot for a file that has
exactly one resolution, so a phone downloads the same bytes as a desktop.

The `<picture>` wrapper is worse: every `<source>` advertises
`type="image/webp"` while pointing at a `.jpg`. Measured over the live corpus:
175/175 of them lie about the format. A conforming browser acts on that hint.
Next-gen delivery belongs at the edge (Cloudflare Polish), per-client and per
Accept header — not in a content-type claim the bytes do not honour.

Finally, `loading="lazy"` is applied to EVERY image by html_sanitize, including
the first one on the page. On an essay that is the LCP element, and lazy-loading
defers its request until after layout. The first image is switched to
`fetchpriority="high"`.

MEASURED SCOPE (live D1, 73 published essays)
    181 <img>, 175 <picture>, 350 srcset attributes, 181 loading="lazy"
    350/350 srcset attributes are degenerate — zero have real variants
    175/175 <source type="image/webp"> point at a .jpg

SAFETY
------
`content_hash()` in html_sanitize.py hashes `plain_text(html)` — "normalized
TEXT, deliberately not markup". None of these edits change a single character of
hashed text, so substack_sync's short-circuit still fires and the hourly cron
will NOT see these rows as edited and rewrite all 73 (which would churn
updated_at and poison the sitemap's lastmod). `verify()` below asserts this per
row before any SQL is emitted.

NOTE: rehost_essay_images.py's local_name() and docstring both say ".webp".
That is STALE — every file in worker/public/essay-images/ is .jpg and every D1
reference is .jpg.

USAGE
-----
    # 1. Export (this is also the rollback backup — keep it)
    cd worker && uv run pywrangler d1 execute tih-db --remote \\
        --command "SELECT id, slug, content FROM story WHERE status='published'" \\
        --json > /tmp/d1_export.json

    # 2. Inspect, then generate
    python3 backend/scripts/strip_degenerate_srcset.py --dry-run
    python3 backend/scripts/strip_degenerate_srcset.py > /tmp/strip.sql

    # 3. Apply
    cd worker && uv run pywrangler d1 execute tih-db --remote --file=/tmp/strip.sql

Rollback: replay the content column from /tmp/d1_export.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

EXPORT_PATH = "/tmp/d1_export.json"

# Whole srcset/sizes attributes, on <img> or <source>.
_SRCSET_ATTR = re.compile(r'\s+srcset="[^"]*"', re.I)
_SIZES_ATTR = re.compile(r'\s+sizes="[^"]*"', re.I)
# <picture>…</picture>, non-greedy so adjacent figures don't merge.
_PICTURE = re.compile(r"<picture\b[^>]*>(.*?)</picture>", re.I | re.S)
_SOURCE = re.compile(r"<source\b[^>]*/?>", re.I)
_IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
_LAZY_ATTR = re.compile(r'\s+loading="lazy"', re.I)

# Mirrors html_sanitize.plain_text closely enough to prove the hash is stable.
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def plain_text(html: str) -> str:
    """Tag-stripped, whitespace-normalized text — what content_hash hashes."""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", html)).strip()


def is_degenerate(srcset: str) -> bool:
    """True when every candidate in a srcset points at the same URL.

    Candidates are split on ", " (comma + whitespace), not a bare comma:
    Substack CDN URLs embed commas inside transform params, and a plain split
    would shred one legitimate URL into fragments. Same reasoning as
    html_sanitize._SRCSET_SPLIT_RE.
    """
    urls = {p.strip().split(" ")[0] for p in re.split(r",\s+", srcset) if p.strip()}
    return len(urls) <= 1


def unwrap_picture(match: re.Match[str]) -> str:
    """Reduce <picture><source…><img…></picture> to the bare <img>.

    Only unwraps when every <source> inside is degenerate; a genuine art-direction
    or real-variant <picture> is left alone. Measured on the live corpus, all 175
    qualify, but the guard keeps this script correct if that ever changes.
    """
    body = match.group(1)
    for src in _SOURCE.findall(body):
        found = re.search(r'srcset="([^"]*)"', src, re.I)
        if found and not is_degenerate(found.group(1)):
            return match.group(0)  # real variants — leave the whole element
    return _SOURCE.sub("", body)


def promote_first_image(html: str) -> str:
    """Drop loading="lazy" from the first <img> and mark it high priority.

    Attribute order varies in the corpus (`<img alt=… loading="lazy" …>` and
    `<img src=… loading="lazy">` both occur), so this edits inside the matched
    tag rather than string-replacing a fixed prefix.
    """
    match = _IMG_TAG.search(html)
    if not match:
        return html
    tag = match.group(0)
    promoted = _LAZY_ATTR.sub("", tag)
    if "fetchpriority=" not in promoted.lower():
        promoted = promoted.replace("<img", '<img fetchpriority="high"', 1)
    return html[: match.start()] + promoted + html[match.end() :]


def fix(html: str) -> str:
    """Apply every markup correction to one essay body."""
    out = _PICTURE.sub(unwrap_picture, html)

    # Strip only degenerate srcsets, then the now-pointless sizes hint that
    # accompanied them.
    def _strip_if_degenerate(m: re.Match[str]) -> str:
        inner = re.search(r'srcset="([^"]*)"', m.group(0), re.I)
        return "" if inner and is_degenerate(inner.group(1)) else m.group(0)

    out = _SRCSET_ATTR.sub(_strip_if_degenerate, out)
    if "srcset=" not in out:
        out = _SIZES_ATTR.sub("", out)
    return promote_first_image(out)


def verify(before: str, after: str) -> None:
    """Abort unless the change is markup-only.

    If hashed text moved, the next substack_sync would treat the row as edited
    and rewrite all 73, churning updated_at and the sitemap's lastmod.
    """
    if plain_text(before) != plain_text(after):
        raise SystemExit("ABORT: visible text changed — content_hash would move")


def sql_escape(text: str) -> str:
    return text.replace("'", "''")


def load_rows() -> list[dict]:
    raw = open(EXPORT_PATH, encoding="utf-8").read()
    match = re.search(r'"results":\s*(\[.*?\])\s*,\s*"success"', raw, re.S)
    if not match:
        sys.exit(f"could not parse {EXPORT_PATH} — is it a --json d1 export?")
    return json.loads(match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report, emit no SQL")
    args = parser.parse_args()

    rows = load_rows()
    changed = 0
    stats = {"srcset": 0, "sizes": 0, "picture": 0, "lazy": 0}
    statements: list[str] = []

    for row in rows:
        before = row.get("content") or ""
        if not before:
            continue
        after = fix(before)
        if after == before:
            continue

        verify(before, after)
        changed += 1
        stats["srcset"] += before.count("srcset=") - after.count("srcset=")
        stats["sizes"] += before.count("sizes=") - after.count("sizes=")
        stats["picture"] += before.count("<picture") - after.count("<picture")
        stats["lazy"] += before.count('loading="lazy"') - after.count('loading="lazy"')
        statements.append(
            f"UPDATE story SET content = '{sql_escape(after)}' WHERE id = {int(row['id'])};"
        )

    if args.dry_run:
        print(f"rows that would change : {changed}/{len(rows)}")
        print(f"srcset attrs removed   : {stats['srcset']}")
        print(f"sizes attrs removed    : {stats['sizes']}")
        print(f"<picture> unwrapped    : {stats['picture']}")
        print(f'loading="lazy" removed : {stats["lazy"]} (first image per essay)')
        print("\nvisible text unchanged on every row — content_hash is stable")
        return

    print("-- Generated by backend/scripts/strip_degenerate_srcset.py")
    print(f"-- {changed} rows; srcset-{stats['srcset']} picture-{stats['picture']}")
    print("-- Markup only: content_hash hashes text, so substack_sync stays a no-op.")
    for statement in statements:
        print(statement)


if __name__ == "__main__":
    main()
