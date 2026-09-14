"""SSR dispatch coverage for the Worker.

Mirrors the routing predicates in `_render_markup` (worker/src/worker.py). As
with test_routing.py, worker.py cannot be imported outside the Pyodide runtime,
so the dispatch shape is re-declared and `test_dispatch_mirrors_source` fails
when the two drift.

What this protects: before Phase 3, every marketing route shipped a 29-byte
body. Googlebot renders JS so it eventually saw them, but GPTBot, ClaudeBot and
PerplexityBot do not — /about and all four /speak/<topic> pages were literally
blank to every AI answer engine, which is precisely where the site's authority
and speaker-booking content lives.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_WORKER_PY = _ROOT / "worker" / "src" / "worker.py"
_TOPICS_MJS = _ROOT / "frontend" / "src" / "data" / "speakingTopics.mjs"

_STATIC_SSR_KEYS = {"", "about", "listen", "privacy"}


def _route_kind(clean: str) -> str:
    """Mirrors _render_markup's dispatch order."""
    if clean.startswith("essays/") and clean.count("/") == 1:
        return "essay"
    if clean == "archive":
        return "archive"
    if clean == "speak":
        return "speak"
    if clean.startswith("speak/") and clean.count("/") == 1:
        return "topic"
    if clean in _STATIC_SSR_KEYS:
        return "static"
    return "none"


@pytest.mark.parametrize(
    ("path", "kind"),
    [
        ("", "static"),
        ("about", "static"),
        ("listen", "static"),
        ("privacy", "static"),
        ("archive", "archive"),
        ("speak", "speak"),
        ("speak/grief-and-inheritance", "topic"),
        ("speak/migration-as-grief", "topic"),
        ("essays/ambiguous-loss", "essay"),
        # Routes with no SSR fall through to the plain shell.
        ("subscribed", "none"),
        ("links", "none"),
        ("admin/stories", "none"),
        ("speak/a/b", "none"),
        ("essays/a/b", "none"),
    ],
)
def test_dispatch(path, kind):
    assert _route_kind(path) == kind


def test_every_marketing_route_has_ssr():
    """The routes that shipped an empty body must all resolve to SSR now."""
    for path in ("", "about", "speak", "listen", "privacy"):
        assert _route_kind(path) != "none", f"/{path} lost its SSR"


def test_topic_dispatch_covers_every_published_topic():
    """Each slug in speakingTopics.mjs must route to the topic renderer.

    speakingTopics.mjs is the single source of truth; the Worker reads it via
    the build-time speaking-topics.json rather than keeping a Python copy.
    """
    slugs = [
        line.split('"')[1]
        for line in _TOPICS_MJS.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("slug:")
    ]
    assert len(slugs) >= 4, f"expected the 4 speaking topics, found {slugs}"
    for slug in slugs:
        assert _route_kind(f"speak/{slug}") == "topic"


def test_topics_json_is_emitted_by_the_sitemap_script():
    """The Worker depends on this file existing in public/ at deploy time."""
    src = (_ROOT / "frontend" / "scripts" / "generate-sitemap.mjs").read_text("utf-8")
    assert "speaking-topics.json" in src
    for field in ("slug", "title", "subtitle", "audience", "blurb"):
        assert f"{field}: t.{field}" in src, f"{field} missing from the emitted JSON"


def test_emitted_topics_json_shape_if_present():
    """When a build has run, the artifact must carry what _ssr_topic reads."""
    built = _ROOT / "frontend" / "dist" / "speaking-topics.json"
    if not built.exists():
        pytest.skip("no build output present")
    topics = json.loads(built.read_text(encoding="utf-8"))
    assert len(topics) >= 4
    for t in topics:
        assert {"slug", "title", "subtitle", "audience", "blurb"} <= set(t)


def test_dispatch_mirrors_source():
    """Fail when _render_markup's dispatch drifts from the mirror above."""
    src = _WORKER_PY.read_text(encoding="utf-8")

    assert 'if clean.startswith("essays/") and clean.count("/") == 1:' in src
    assert 'if clean == "archive":' in src
    assert 'if clean == "speak":' in src
    assert 'if clean.startswith("speak/") and clean.count("/") == 1:' in src
    assert "return _STATIC_SSR.get(clean)" in src

    for key in _STATIC_SSR_KEYS:
        assert f'"{key}":' in src, f"_STATIC_SSR missing {key!r}"

    # The topic list must come from the build artifact, not a Python copy —
    # speakingTopics.mjs promises that adding a topic fans out to consumers.
    assert "speaking-topics.json" in src
    assert "SPEAKING_TOPICS" not in src, "topic list must not be duplicated in Python"

    # SSR must stay an enhancement: a D1 failure serves the shell, never a 500.
    assert "SSR failed for" in src
