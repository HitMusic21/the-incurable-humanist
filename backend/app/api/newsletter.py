"""
Newsletter API endpoints for fetching articles from Substack RSS feed.
"""

from datetime import datetime

import feedparser
from dateutil import parser as date_parser
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.api.schemas import NewsletterArticle, NewsletterResponse

router = APIRouter()

# Substack RSS feed URL
SUBSTACK_RSS_URL = "https://theincurablehumanist.substack.com/feed"


@router.get("/articles", response_model=NewsletterResponse)
async def get_newsletter_articles():
    """
    Fetch articles from The Incurable Humanist Substack newsletter RSS feed.

    Returns:
        NewsletterResponse: List of articles with metadata

    Raises:
        HTTPException: 503 if unable to fetch or parse RSS feed
    """
    try:
        # Parse the RSS feed
        feed = feedparser.parse(SUBSTACK_RSS_URL)

        # Check if feed was successfully parsed
        if feed.bozo:
            # Feed has parsing errors
            error_msg = getattr(feed, "bozo_exception", "Unknown parsing error")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to parse RSS feed: {str(error_msg)}",
            )

        # Check if feed has entries
        if not hasattr(feed, "entries") or not feed.entries:
            raise HTTPException(
                status_code=503,
                detail="RSS feed contains no articles",
            )

        # Extract articles from feed entries
        articles = []
        for entry in feed.entries:
            try:
                # Parse published date and convert to ISO format
                published_date = entry.get("published", "")
                if published_date:
                    try:
                        parsed_date = date_parser.parse(published_date)
                        published_iso = parsed_date.isoformat()
                    except (ValueError, TypeError):
                        # If date parsing fails, use the original string
                        published_iso = published_date
                else:
                    published_iso = datetime.utcnow().isoformat()

                # Extract author information
                author = None
                if hasattr(entry, "author"):
                    author = entry.author
                elif hasattr(entry, "authors") and entry.authors:
                    author = entry.authors[0].get("name", None)

                # Create article object
                article = NewsletterArticle(
                    title=entry.get("title", "Untitled"),
                    link=entry.get("link", ""),
                    description=entry.get("summary", ""),
                    published=published_iso,
                    author=author,
                )
                articles.append(article)

            except Exception as entry_error:
                # Log error but continue processing other entries
                print(f"Error processing entry: {str(entry_error)}")
                continue

        if not articles:
            raise HTTPException(
                status_code=503,
                detail="No valid articles found in RSS feed",
            )

        return NewsletterResponse(articles=articles, total_count=len(articles))

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=503,
            detail=f"Unable to fetch newsletter articles: {str(e)}",
        )


@router.get("/health")
async def newsletter_health_check():
    """
    Health check endpoint to verify RSS feed connectivity.

    Returns:
        dict: Status information about the RSS feed
    """
    try:
        feed = feedparser.parse(SUBSTACK_RSS_URL)

        if feed.bozo:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "RSS feed has parsing errors",
                    "feed_url": SUBSTACK_RSS_URL,
                },
            )

        article_count = len(feed.entries) if hasattr(feed, "entries") else 0

        return {
            "status": "healthy",
            "feed_url": SUBSTACK_RSS_URL,
            "article_count": article_count,
            "feed_title": feed.feed.get("title", "Unknown") if hasattr(feed, "feed") else "Unknown",
        }

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": str(e),
                "feed_url": SUBSTACK_RSS_URL,
            },
        )
