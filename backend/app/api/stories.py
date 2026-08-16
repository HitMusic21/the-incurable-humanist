"""
Stories CRUD API. Public reads for /stories and /stories/{slug}; author-only
mutation for POST/PATCH/DELETE (guarded by get_current_author).

Note: `from __future__ import annotations` is intentionally NOT used — see the
same note in app/api/leads.py for the FastAPI+Pydantic+slowapi rationale.
"""

import logging
import secrets
from datetime import datetime

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    StoryCreate,
    StoryDetail,
    StoryListResponse,
    StoryPublic,
    StoryUpdate,
)
from app.core.config import settings
from app.core.database import get_session
from app.models.story import Story, StoryStatus
from app.models.user import User
from app.services.auth import get_current_author
from app.services.slugify import ensure_unique_slug, slugify
from app.services.substack_sync import resolve_author, sync_from_feed

logger = logging.getLogger(__name__)

router = APIRouter()


class SyncResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str] = []


def _verify_scheduler_token(header_value: str | None) -> None:
    """Header-based auth for the sync endpoint. Rejects if SCHEDULER_TOKEN is
    unset (never accept unauth in prod) or if the header doesn't match."""
    expected = settings.SCHEDULER_TOKEN
    if not expected:
        logger.error("Sync request rejected: SCHEDULER_TOKEN is not configured.")
        raise HTTPException(status_code=503, detail="Sync scheduler not configured.")
    if not header_value or not secrets.compare_digest(header_value, expected):
        raise HTTPException(status_code=401, detail="Invalid scheduler token.")


def _coerce_status(raw: str | None) -> StoryStatus | None:
    if raw is None:
        return None
    try:
        return StoryStatus(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status {raw!r}. Must be one of: draft, published, archived.",
        ) from exc


@router.get("", response_model=StoryListResponse)
async def list_stories(
    status_filter: str | None = Query(default="published", alias="status"),
    # Cap high (500) so the sitemap/RSS generators can pull the full corpus in
    # one request; UI clients still pass smaller limits.
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> StoryListResponse:
    """
    Public list. Default filters to `published`; pass `status=all` to return every row
    (author-only clients can further filter client-side, but this endpoint stays public
    to keep the SEO/RSS generators simple).
    """
    where = []
    if status_filter and status_filter.lower() != "all":
        where.append(Story.status == _coerce_status(status_filter))

    stmt = select(Story)
    for clause in where:
        stmt = stmt.where(clause)
    stmt = stmt.order_by(Story.published_at.desc().nullslast(), Story.id.desc())

    total = (
        await session.execute(
            select(func.count()).select_from(Story).where(*where) if where
            else select(func.count()).select_from(Story)
        )
    ).scalar_one()

    rows = (
        await session.execute(stmt.limit(limit).offset(offset))
    ).scalars().all()

    return StoryListResponse(
        stories=[StoryPublic.model_validate(r) for r in rows],
        total_count=total,
    )


@router.get("/id/{story_id}", response_model=StoryDetail)
async def get_story_by_id(
    story_id: int,
    author: User = Depends(get_current_author),  # noqa: ARG001
    session: AsyncSession = Depends(get_session),
) -> StoryDetail:
    """Admin-only fetch by id — returns drafts + archived so the editor can hydrate."""
    row = (
        await session.execute(select(Story).where(Story.id == story_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return StoryDetail.model_validate(row)


@router.post("/sync", response_model=SyncResponse)
async def sync_substack(
    x_scheduler_token: str | None = Header(default=None, alias="X-Scheduler-Token"),
    session: AsyncSession = Depends(get_session),
) -> SyncResponse:
    """
    Pull the ~20 posts Substack exposes over RSS and upsert them as stories.

    Cloud Scheduler hits this hourly. Idempotent: posts whose text is unchanged
    are skipped, so a typical run writes nothing. Declared above GET /{slug}
    purely for readability — the methods differ, so there is no route conflict.
    """
    _verify_scheduler_token(x_scheduler_token)

    try:
        author = await resolve_author(session, settings.AUTHOR_EMAIL)
    except RuntimeError as exc:
        # Misconfiguration, not a client error — the author row must exist first.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        result = await sync_from_feed(session, author_id=author.id)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - upstream feed/network failure
        logger.exception("sync_substack failed")
        raise HTTPException(status_code=503, detail=f"Substack sync failed: {exc}") from exc

    return SyncResponse(
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        errors=result.errors,
    )


@router.get("/{slug}", response_model=StoryDetail)
async def get_story(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> StoryDetail:
    row = (
        await session.execute(select(Story).where(Story.slug == slug))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Story not found")
    if row.status != StoryStatus.PUBLISHED:
        # Hide drafts + archived from the public API. Author edits happen via id-scoped PATCH.
        raise HTTPException(status_code=404, detail="Story not found")

    row.view_count = (row.view_count or 0) + 1
    await session.commit()
    await session.refresh(row)
    return StoryDetail.model_validate(row)


@router.post("", response_model=StoryDetail, status_code=status.HTTP_201_CREATED)
async def create_story(
    payload: StoryCreate = Body(...),
    author: User = Depends(get_current_author),
    session: AsyncSession = Depends(get_session),
) -> StoryDetail:
    resolved_status = _coerce_status(payload.status) or StoryStatus.DRAFT
    base_slug = slugify(payload.slug) if payload.slug else slugify(payload.title)
    slug = await ensure_unique_slug(session, base_slug)

    story = Story(
        title=payload.title,
        slug=slug,
        content=payload.content,
        excerpt=payload.excerpt,
        meta_description=payload.meta_description,
        cover_image_url=payload.cover_image_url,
        canonical_url=payload.canonical_url,
        content_warning=payload.content_warning,
        status=resolved_status,
        author_id=author.id,
        published_at=datetime.utcnow() if resolved_status == StoryStatus.PUBLISHED else None,
    )
    session.add(story)
    await session.commit()
    await session.refresh(story)
    return StoryDetail.model_validate(story)


@router.patch("/{story_id}", response_model=StoryDetail)
async def update_story(
    story_id: int,
    payload: StoryUpdate = Body(...),
    author: User = Depends(get_current_author),  # noqa: ARG001
    session: AsyncSession = Depends(get_session),
) -> StoryDetail:
    story = (
        await session.execute(select(Story).where(Story.id == story_id))
    ).scalar_one_or_none()
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")

    data = payload.model_dump(exclude_unset=True)

    if "slug" in data and data["slug"]:
        base = slugify(data["slug"])
        data["slug"] = await ensure_unique_slug(session, base, own_id=story.id)

    if "status" in data:
        new_status = _coerce_status(data["status"])
        data["status"] = new_status
        if new_status == StoryStatus.PUBLISHED and story.published_at is None:
            data["published_at"] = datetime.utcnow()

    for key, value in data.items():
        setattr(story, key, value)
    story.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(story)
    return StoryDetail.model_validate(story)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: int,
    author: User = Depends(get_current_author),  # noqa: ARG001
    session: AsyncSession = Depends(get_session),
) -> None:
    story = (
        await session.execute(select(Story).where(Story.id == story_id))
    ).scalar_one_or_none()
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    await session.delete(story)
    await session.commit()
