# Substack API Research Report

**Date:** 2025-10-04
**Context:** Newsletter page with Substack integration - retrieving published articles/posts
**Goal:** Display articles that have already been posted on Substack

---

## Executive Summary

**CRITICAL FINDING:** Substack does NOT provide an official public API. However, there are three viable approaches to retrieve published posts:

1. **RSS Feed (RECOMMENDED)** - Official, stable, public, no authentication required
2. **Unofficial JSON API** - Undocumented internal endpoints, may change without notice
3. **Third-party Python libraries** - Wrappers around unofficial APIs

**Recommended Approach:** Use RSS feed parsed to JSON for maximum stability and no authentication requirements.

---

## 1. RSS Feed Approach (RECOMMENDED)

### Endpoint
```
https://{newsletter-name}.substack.com/feed
```

### Method
GET

### Authentication
**None required** - Public endpoint

### Request Parameters
None required for basic feed access

### Response Structure
Standard RSS 2.0 XML format. Example structure:

```xml
<rss version="2.0">
  <channel>
    <title>Publication Title</title>
    <link>https://example.substack.com</link>
    <description>Publication description</description>
    <item>
      <title>Post Title</title>
      <link>https://example.substack.com/p/post-url</link>
      <description>Post excerpt or summary</description>
      <pubDate>Wed, 02 Oct 2024 14:30:00 GMT</pubDate>
      <guid>https://example.substack.com/p/post-url</guid>
      <author>author@email.com (Author Name)</author>
    </item>
    <!-- More items... -->
  </channel>
</rss>
```

### Key RSS Fields
- **title** - Post title
- **link** - Full URL to the post
- **description** - Post excerpt/summary
- **pubDate** - Publication date (RFC 822 format)
- **guid** - Unique identifier for the post
- **author** - Author information

### Limitations
- RSS feeds typically return only the most recent ~20 posts
- Does not include full article content (only excerpts)
- No control over sorting or filtering

---

## 2. Unofficial JSON API Approach (USE WITH CAUTION)

### Archive Endpoint
```
https://{newsletter-name}.substack.com/api/v1/archive
```

### Method
GET

### Authentication
**None required** for public posts (cookies required for paywalled content)

### Request Parameters
- `sort` - Sorting parameter (e.g., "new")
- `search` - Search query string (can be empty)
- `offset` - Number of posts to skip (pagination)
- `limit` - Number of posts to return (typically 12)

### Example URL
```
https://example.substack.com/api/v1/archive?sort=new&search=&offset=0&limit=12
```

### Alternative Posts Endpoint
```
https://{newsletter-name}.substack.com/api/v1/posts?limit=50&offset=0
```

### Response Structure
JSON array of post objects with metadata:

```json
[
  {
    "id": 123456,
    "publication_id": 789,
    "title": "Post Title",
    "post_date": "2024-10-02T14:30:00.000Z",
    "audience": "everyone",
    "comment_count": 15,
    "canonical_url": "https://example.substack.com/p/post-url",
    "slug": "post-url",
    "description": "Post excerpt",
    "cover_image": "https://...",
    "reactions": {...}
  }
]
```

### Key JSON Fields
- **id** - Post ID
- **publication_id** - Publication ID
- **title** - Post title
- **post_date** - Publication date (ISO 8601)
- **canonical_url** - Full URL to post
- **slug** - URL slug
- **description** - Post excerpt
- **cover_image** - Featured image URL
- **comment_count** - Number of comments
- **audience** - Visibility (e.g., "everyone", "paid")

### Limitations
- **UNOFFICIAL** - May change without notice
- Not documented or supported by Substack
- May violate Substack's terms of service
- No guaranteed stability

---

## 3. Implementation Recommendations for FastAPI + React

### Recommended Architecture

**Backend (FastAPI):**
1. Create an endpoint to fetch and parse Substack RSS feed
2. Convert RSS to JSON format
3. Cache results to reduce requests to Substack
4. Return standardized JSON to frontend

**Frontend (React):**
1. Fetch posts from backend API endpoint
2. Display posts with title, date, excerpt, link
3. Handle loading and error states

### Python Implementation (FastAPI Backend)

#### Install Dependencies
```bash
pip install feedparser
pip install python-dateutil
```

Add to `backend/requirements.txt`:
```
feedparser==6.0.11
python-dateutil==2.8.2
```

#### Backend Code Example

**File: `backend/app/routers/newsletter.py`**

```python
from fastapi import APIRouter, HTTPException
from typing import List
import feedparser
from datetime import datetime
from dateutil import parser as date_parser
from pydantic import BaseModel

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])


class SubstackPost(BaseModel):
    title: str
    link: str
    description: str
    published: str
    published_date: datetime
    author: str
    guid: str


@router.get("/posts", response_model=List[SubstackPost])
async def get_substack_posts(limit: int = 10):
    """
    Fetch published posts from Substack RSS feed

    Args:
        limit: Maximum number of posts to return (default: 10)

    Returns:
        List of SubstackPost objects
    """
    # Replace with your Substack newsletter URL
    SUBSTACK_FEED_URL = "https://your-newsletter.substack.com/feed"

    try:
        # Parse RSS feed
        feed = feedparser.parse(SUBSTACK_FEED_URL)

        # Check if feed was parsed successfully
        if feed.bozo:
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing RSS feed: {feed.bozo_exception}"
            )

        # Extract posts from entries
        posts = []
        for entry in feed.entries[:limit]:
            try:
                # Parse published date
                published_date = date_parser.parse(entry.published)

                post = SubstackPost(
                    title=entry.title,
                    link=entry.link,
                    description=entry.get('description', entry.get('summary', '')),
                    published=entry.published,
                    published_date=published_date,
                    author=entry.get('author', 'Unknown'),
                    guid=entry.get('id', entry.link)
                )
                posts.append(post)
            except Exception as e:
                # Log error but continue processing other posts
                print(f"Error processing entry: {e}")
                continue

        return posts

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Substack posts: {str(e)}"
        )


@router.get("/feed-info")
async def get_feed_info():
    """Get Substack feed metadata"""
    SUBSTACK_FEED_URL = "https://your-newsletter.substack.com/feed"

    try:
        feed = feedparser.parse(SUBSTACK_FEED_URL)

        if feed.bozo:
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing RSS feed: {feed.bozo_exception}"
            )

        return {
            "title": feed.feed.get('title', ''),
            "link": feed.feed.get('link', ''),
            "description": feed.feed.get('description', ''),
            "language": feed.feed.get('language', 'en'),
            "total_posts": len(feed.entries)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching feed info: {str(e)}"
        )
```

#### Environment Configuration

**File: `backend/.env`**
```env
SUBSTACK_FEED_URL=https://your-newsletter.substack.com/feed
```

#### With Caching (Optional but Recommended)

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache
_cache = {}
_cache_expiry = {}
CACHE_DURATION = timedelta(minutes=15)


@router.get("/posts", response_model=List[SubstackPost])
async def get_substack_posts(limit: int = 10, use_cache: bool = True):
    """Fetch published posts from Substack RSS feed with caching"""

    SUBSTACK_FEED_URL = "https://your-newsletter.substack.com/feed"
    cache_key = f"posts_{limit}"

    # Check cache
    if use_cache and cache_key in _cache:
        if datetime.now() < _cache_expiry.get(cache_key, datetime.min):
            return _cache[cache_key]

    # Fetch fresh data (same logic as before)
    feed = feedparser.parse(SUBSTACK_FEED_URL)
    # ... (rest of parsing logic)

    # Update cache
    _cache[cache_key] = posts
    _cache_expiry[cache_key] = datetime.now() + CACHE_DURATION

    return posts
```

### Frontend Implementation (React + TypeScript)

#### TypeScript Interface

**File: `frontend/src/types/newsletter.ts`**
```typescript
export interface SubstackPost {
  title: string;
  link: string;
  description: string;
  published: string;
  published_date: string;
  author: string;
  guid: string;
}

export interface FeedInfo {
  title: string;
  link: string;
  description: string;
  language: string;
  total_posts: number;
}
```

#### React Component Example

**File: `frontend/src/components/NewsletterPosts.tsx`**
```typescript
import React, { useEffect, useState } from 'react';
import { SubstackPost } from '../types/newsletter';

const NewsletterPosts: React.FC = () => {
  const [posts, setPosts] = useState<SubstackPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/newsletter/posts?limit=10');

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: SubstackPost[] = await response.json();
        setPosts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch posts');
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return <div className="loading">Loading posts...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="newsletter-posts">
      <h2>Latest Newsletter Posts</h2>
      <div className="posts-grid">
        {posts.map((post) => (
          <article key={post.guid} className="post-card">
            <h3>
              <a href={post.link} target="_blank" rel="noopener noreferrer">
                {post.title}
              </a>
            </h3>
            <p className="post-meta">
              By {post.author} • {formatDate(post.published_date)}
            </p>
            <div
              className="post-description"
              dangerouslySetInnerHTML={{ __html: post.description }}
            />
            <a
              href={post.link}
              className="read-more"
              target="_blank"
              rel="noopener noreferrer"
            >
              Read More →
            </a>
          </article>
        ))}
      </div>
    </div>
  );
};

export default NewsletterPosts;
```

#### API Service Layer (Optional)

**File: `frontend/src/services/newsletterService.ts`**
```typescript
import { SubstackPost, FeedInfo } from '../types/newsletter';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const newsletterService = {
  async getPosts(limit: number = 10): Promise<SubstackPost[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/newsletter/posts?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch posts: ${response.statusText}`);
    }

    return response.json();
  },

  async getFeedInfo(): Promise<FeedInfo> {
    const response = await fetch(`${API_BASE_URL}/api/newsletter/feed-info`);

    if (!response.ok) {
      throw new Error(`Failed to fetch feed info: ${response.statusText}`);
    }

    return response.json();
  }
};
```

---

## 4. Alternative: Using Unofficial API (Not Recommended)

If you absolutely need more than 20 posts or require additional metadata not available in RSS:

### Backend Implementation with Unofficial API

```python
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])


@router.get("/posts-advanced")
async def get_substack_posts_advanced(limit: int = 12, offset: int = 0):
    """
    Fetch posts using unofficial Substack archive API
    WARNING: This is an undocumented API that may change without notice
    """
    SUBSTACK_SUBDOMAIN = "your-newsletter"
    API_URL = f"https://{SUBSTACK_SUBDOMAIN}.substack.com/api/v1/archive"

    params = {
        "sort": "new",
        "search": "",
        "offset": offset,
        "limit": limit
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL, params=params)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching from Substack API: {str(e)}"
        )
```

**IMPORTANT:** This approach:
- May break at any time
- Is not officially supported
- May violate Substack's terms of service
- Should only be used as a last resort

---

## 5. Security & Performance Considerations

### CORS Configuration (FastAPI)

**File: `backend/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting

Consider implementing rate limiting to avoid overwhelming Substack's servers:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/posts")
@limiter.limit("10/minute")
async def get_substack_posts(request: Request, limit: int = 10):
    # ... implementation
```

### Caching Strategy

1. **In-memory cache** - Simple, fast, resets on server restart
2. **Redis cache** - Persistent, scalable, shared across instances
3. **CDN caching** - For static JSON responses

Recommended cache duration: 10-15 minutes for newsletter posts

---

## 6. Error Handling & Edge Cases

### Common Errors to Handle

1. **Network failures** - Substack server unavailable
2. **Invalid feed format** - Malformed RSS/XML
3. **Empty feeds** - New newsletters with no posts
4. **Rate limiting** - Too many requests
5. **Timeout errors** - Slow response from Substack

### Example Error Handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "path": request.url.path
        }
    )
```

---

## 7. Testing Recommendations

### Backend Tests

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_posts_success():
    response = client.get("/api/newsletter/posts?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


def test_get_posts_with_invalid_limit():
    response = client.get("/api/newsletter/posts?limit=-1")
    assert response.status_code == 422  # Validation error
```

### Frontend Tests (Jest/React Testing Library)

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import NewsletterPosts from './NewsletterPosts';

test('displays loading state initially', () => {
  render(<NewsletterPosts />);
  expect(screen.getByText(/loading/i)).toBeInTheDocument();
});

test('displays posts after successful fetch', async () => {
  // Mock fetch
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve([
        {
          title: 'Test Post',
          link: 'https://example.com',
          description: 'Test description',
          published: 'Wed, 02 Oct 2024 14:30:00 GMT',
          published_date: '2024-10-02T14:30:00Z',
          author: 'Test Author',
          guid: '123'
        }
      ])
    })
  ) as jest.Mock;

  render(<NewsletterPosts />);

  await waitFor(() => {
    expect(screen.getByText('Test Post')).toBeInTheDocument();
  });
});
```

---

## 8. Deployment Considerations

### Environment Variables

**Backend (.env):**
```env
SUBSTACK_FEED_URL=https://your-newsletter.substack.com/feed
CACHE_DURATION_MINUTES=15
CORS_ORIGINS=https://yourdomain.com,http://localhost:5173
```

**Frontend (.env):**
```env
VITE_API_URL=https://api.yourdomain.com
```

### Production Optimizations

1. **Enable HTTP/2** for faster parallel requests
2. **Use CDN** for static frontend assets
3. **Implement Redis caching** for scalability
4. **Set up monitoring** for API failures
5. **Configure logging** for debugging

---

## 9. Summary & Recommendations

### Final Recommendation: RSS Feed Approach

**Pros:**
- Official, supported by Substack
- No authentication required
- Stable and reliable
- Simple to implement
- No terms of service concerns

**Cons:**
- Limited to ~20 most recent posts
- Only provides excerpts, not full content
- No advanced filtering or sorting

### Implementation Checklist

- [ ] Install feedparser in backend
- [ ] Create FastAPI endpoint for RSS parsing
- [ ] Implement caching (15-minute duration)
- [ ] Configure CORS for frontend origin
- [ ] Create TypeScript interfaces for posts
- [ ] Build React component to display posts
- [ ] Add error handling and loading states
- [ ] Test with your actual Substack feed
- [ ] Add rate limiting (optional)
- [ ] Set up monitoring and logging

### Alternative Path (If RSS is Insufficient)

If you need more than 20 posts or additional metadata:
1. Use unofficial archive API with extreme caution
2. Document the risks to stakeholders
3. Implement robust error handling
4. Monitor for API changes
5. Have fallback to RSS feed

---

## 10. Additional Resources

### Official Substack Documentation
- RSS Feed Support: https://support.substack.com/hc/en-us/articles/360038239391

### Python Libraries
- feedparser: https://pypi.org/project/feedparser/
- Unofficial substack-api: https://pypi.org/project/substack-api/
- GitHub wrapper: https://github.com/NHagar/substack_api

### Related Tools
- RSS to JSON converters: https://rss2json.com/
- Feed validators: https://validator.w3.org/feed/

---

## File Locations for Implementation

**Backend Files:**
- `/Users/carlosmescalona/Documents/Projects/TIH2/backend/app/routers/newsletter.py` - API endpoints
- `/Users/carlosmescalona/Documents/Projects/TIH2/backend/.env` - Configuration
- `/Users/carlosmescalona/Documents/Projects/TIH2/backend/requirements.txt` - Dependencies

**Frontend Files:**
- `/Users/carlosmescalona/Documents/Projects/TIH2/frontend/src/types/newsletter.ts` - Type definitions
- `/Users/carlosmescalona/Documents/Projects/TIH2/frontend/src/services/newsletterService.ts` - API service
- `/Users/carlosmescalona/Documents/Projects/TIH2/frontend/src/components/NewsletterPosts.tsx` - React component

---

**Report Generated:** 2025-10-04
**Next Steps:** Proceed with RSS feed implementation using FastAPI + feedparser + React
