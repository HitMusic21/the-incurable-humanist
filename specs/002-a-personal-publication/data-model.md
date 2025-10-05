# Data Model

**Feature**: The Incurable Humanist - Personal Publication Platform
**Database**: PostgreSQL with SQLModel ORM
**Date**: 2025-10-04

## Entity Relationship Diagram

```
User (Reader/Author)
  ├── has many → Story (if is_author=True, only Denise)
  ├── has many → Comment
  ├── has many → Bookmark
  ├── has one → NewsletterSubscription
  └── has many → ReadingProgress

Story
  ├── belongs to → User (author, must be Denise)
  ├── has many → StoryTheme (junction table)
  ├── has many → Comment
  ├── has many → Bookmark
  └── has many → ReadingProgress

Theme
  └── has many → StoryTheme (junction table)

Comment
  ├── belongs to → User (reader)
  ├── belongs to → Story
  └── has one → Comment (parent, for threading)

Bookmark
  ├── belongs to → User
  └── belongs to → Story

NewsletterSubscription
  └── belongs to → User

ReadingProgress
  ├── belongs to → User
  └── belongs to → Story
```

## Core Entities

### User
Represents both readers and the author (Denise).

```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    full_name: str | None = Field(default=None, max_length=255)
    is_author: bool = Field(default=False)  # True only for Denise
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    stories: list["Story"] = Relationship(back_populates="author")
    comments: list["Comment"] = Relationship(back_populates="user")
    bookmarks: list["Bookmark"] = Relationship(back_populates="user")
    subscription: "NewsletterSubscription | None" = Relationship(back_populates="user")
    reading_progress: list["ReadingProgress"] = Relationship(back_populates="user")
```

**Validation Rules**:
- Email must be valid format and unique
- Password min 8 characters (validated before hashing)
- Only one user with is_author=True (Denise)
- Email is case-insensitive for lookups

**Indexes**:
- email (unique index)
- is_author (for author queries)

---

### Story
Content authored by Denise.

```python
class StoryStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Story(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    content: str  # HTML from Tiptap editor
    excerpt: str | None = Field(default=None, max_length=500)  # For newsletters
    cover_image_url: str | None = Field(default=None, max_length=500)
    status: StoryStatus = Field(default=StoryStatus.DRAFT)
    author_notes: str | None = Field(default=None)  # Internal notes, searchable
    content_warning: str | None = Field(default=None, max_length=500)
    view_count: int = Field(default=0)
    read_time_minutes: int | None = Field(default=None)  # Calculated from content

    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: datetime | None = Field(default=None)

    # Full-text search
    search_vector: str | None = Field(default=None, sa_column=Column(TSVector()))

    # Relationships
    author: User = Relationship(back_populates="stories")
    themes: list["Theme"] = Relationship(back_populates="stories", link_model="StoryTheme")
    comments: list["Comment"] = Relationship(back_populates="story")
    bookmarks: list["Bookmark"] = Relationship(back_populates="story")
    reading_progress: list["ReadingProgress"] = Relationship(back_populates="story")
```

**Validation Rules**:
- Title required, max 500 chars
- Content required for published stories
- Author must have is_author=True (only Denise)
- Status transitions: draft → published → archived
- Cannot delete published stories (only archive)
- published_at set on first publish

**Indexes**:
- author_id + status (for dashboard queries)
- published_at DESC (for homepage sorting)
- search_vector (GIN index for full-text search)

**State Transitions**:
```
DRAFT → PUBLISHED: Set published_at, status=PUBLISHED
PUBLISHED → PUBLISHED: Edit allowed, update updated_at
PUBLISHED → ARCHIVED: Hide from public, preserve data
ARCHIVED → PUBLISHED: Re-publish allowed
```

---

### Theme
Categories: grief, migration, art (multi-select).

```python
class Theme(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50)  # "grief", "migration", "art"
    slug: str = Field(unique=True, max_length=50)  # URL-friendly
    description: str | None = Field(default=None, max_length=500)

    # Relationships
    stories: list["Story"] = Relationship(back_populates="themes", link_model="StoryTheme")
```

**Validation Rules**:
- Name unique, lowercase
- Slug auto-generated from name
- Initial data: grief, migration, art

**Indexes**:
- slug (unique index for URL lookup)

---

### StoryTheme (Junction Table)
Many-to-many relationship between Story and Theme.

```python
class StoryTheme(SQLModel, table=True):
    story_id: int = Field(foreign_key="story.id", primary_key=True)
    theme_id: int = Field(foreign_key="theme.id", primary_key=True)
```

---

### Comment
Reader comments on stories (moderated).

```python
class CommentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Comment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(max_length=2000)
    status: CommentStatus = Field(default=CommentStatus.PENDING)

    user_id: int = Field(foreign_key="user.id")
    story_id: int = Field(foreign_key="story.id")
    parent_id: int | None = Field(default=None, foreign_key="comment.id")  # For threading/replies

    created_at: datetime = Field(default_factory=datetime.utcnow)
    moderated_at: datetime | None = Field(default=None)

    # Relationships
    user: User = Relationship(back_populates="comments")
    story: Story = Relationship(back_populates="comments")
    parent: "Comment | None" = Relationship(
        sa_relationship_kwargs={"remote_side": "Comment.id"}
    )
    replies: list["Comment"] = Relationship(back_populates="parent")
```

**Validation Rules**:
- Content required, max 2000 chars
- Must be associated with published story
- Pending by default, requires moderation
- Parent comment must be on same story

**Indexes**:
- story_id + status (for displaying approved comments)
- user_id + status (for user's comment history)
- status + created_at (for moderation queue)

**State Transitions**:
```
PENDING → APPROVED: Set moderated_at, visible on story
PENDING → REJECTED: Set moderated_at, hidden
```

---

### Bookmark
Reader's saved stories.

```python
class Bookmark(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    story_id: int = Field(foreign_key="story.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="bookmarks")
    story: Story = Relationship(back_populates="bookmarks")

    class Config:
        # Unique constraint: one bookmark per user per story
        table_args = (UniqueConstraint("user_id", "story_id"),)
```

**Validation Rules**:
- User can only bookmark each story once
- Can only bookmark published stories

**Indexes**:
- user_id + created_at DESC (for user's bookmark list)
- Unique index on (user_id, story_id)

---

### NewsletterSubscription
Reader's newsletter preferences.

```python
class NewsletterFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class NewsletterSubscription(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    frequency: NewsletterFrequency = Field(default=NewsletterFrequency.WEEKLY)
    is_active: bool = Field(default=True)

    # Theme preferences (JSON array of theme IDs)
    preferred_themes: list[int] | None = Field(default=None, sa_column=Column(JSON))

    subscribed_at: datetime = Field(default_factory=datetime.utcnow)
    unsubscribed_at: datetime | None = Field(default=None)

    # Relationships
    user: User = Relationship(back_populates="subscription")
```

**Validation Rules**:
- One subscription per user
- Frequency from enum
- preferred_themes must be valid theme IDs

**Indexes**:
- user_id (unique index)
- is_active + frequency (for newsletter jobs)

---

### ReadingProgress
Track reader's position in stories.

```python
class ReadingProgress(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    story_id: int = Field(foreign_key="story.id")
    progress_percent: int = Field(default=0, ge=0, le=100)  # 0-100%
    last_read_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="reading_progress")
    story: Story = Relationship(back_populates="reading_progress")

    class Config:
        # Unique constraint: one progress per user per story
        table_args = (UniqueConstraint("user_id", "story_id"),)
```

**Validation Rules**:
- Progress between 0-100
- Updated on scroll/exit
- One record per user per story

**Indexes**:
- user_id + last_read_at DESC (for recent reading list)
- Unique index on (user_id, story_id)

---

## Database Migrations

Using Alembic for schema migrations:

```bash
# Initial migration
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# Add full-text search index
alembic revision -m "Add search index"
# In migration file:
op.execute("""
    CREATE INDEX story_search_idx ON story
    USING GIN (to_tsvector('english', title || ' ' || content || ' ' || COALESCE(author_notes, '')))
""")
```

## Data Volume Estimates

- Stories: ~50 total (1-2 per week over 6 months)
- Users: 100-500 readers
- Comments: ~500 total (10 per story average)
- Bookmarks: ~1000 total (2 per user average)
- Newsletter subscriptions: 50-200 (40-50% of readers)
- Reading progress: ~2500 records (5 stories per user average)

**Total DB size estimate**: <100 MB (well within PostgreSQL free tier)

## Performance Considerations

1. **Story List Query** (Homepage):
   - Index on (status, published_at DESC)
   - Eager load themes via JOIN
   - Paginate 20 stories per page

2. **Story Search**:
   - GIN index on search_vector
   - Rank by ts_rank + recency
   - Limit to top 50 results

3. **Comment Moderation Queue**:
   - Index on (status='pending', created_at)
   - Load with user relationship
   - Paginate 50 comments per page

4. **User's Bookmarks**:
   - Index on (user_id, created_at DESC)
   - JOIN with story for details
   - Paginate 20 per page
