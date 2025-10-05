# Research & Technology Decisions

**Feature**: The Incurable Humanist - Personal Publication Platform
**Date**: 2025-10-04

## Executive Summary

This research document consolidates technology decisions and best practices for building a personal publication platform. All technical context items have been resolved through analysis of requirements, constitutional principles, and industry standards.

## Technology Stack Decisions

### Backend Framework: FastAPI
**Decision**: FastAPI with Python 3.11+
**Rationale**:
- Built-in OpenAPI documentation (Principle II: API-First Design)
- Pydantic integration for type safety and validation (Principle III)
- Async/await support for I/O operations (Constitution requirement)
- Excellent performance for personal blog scale (500 concurrent users)
**Alternatives Considered**:
- Django: Rejected - heavier framework, less API-focused
- Flask: Rejected - lacks built-in async and type validation

### Frontend Framework: React 19 + Vite
**Decision**: React 19 with TypeScript, Vite build tool
**Rationale**:
- Modern hooks-based architecture (Principle V: Clean Code)
- TypeScript strict mode for type safety (Principle III)
- Vite provides fast dev server and optimized production builds
- Component composition aligns with modular architecture (Principle I)
**Alternatives Considered**:
- Next.js: Considered but Vite simpler for personal blog scale
- Vue: Rejected - team familiarity with React

### Database: PostgreSQL with SQLModel
**Decision**: PostgreSQL 14+ with SQLModel ORM
**Rationale**:
- Relational model fits story/comment/user relationships well
- SQLModel provides Pydantic integration + SQLAlchemy power
- Async support via asyncpg
- Proven reliability for 100-500 user scale
**Alternatives Considered**:
- MongoDB: Rejected - relational data model preferred
- SQLite: Rejected - insufficient for production deployment

### Authentication Strategy
**Decision**: Email/password with JWT tokens
**Rationale**:
- Spec clarification: email/password only (no OAuth)
- Role-based access: Author (Denise) vs Readers
- JWT tokens for stateless API authentication
- Password reset via email (using SendGrid or similar)
**Implementation Notes**:
- bcrypt for password hashing
- FastAPI security utilities for JWT
- Author role hardcoded to Denise's email

### Rich Text Editor
**Decision**: Tiptap (frontend) + HTML storage (backend)
**Rationale**:
- Modern React-based editor with extensibility
- Supports required formats: headings, bold, italic, quotes, lists
- Stores as HTML in database (searchable content)
- Optional: Could add Markdown support later
**Alternatives Considered**:
- Draft.js: Older, less active maintenance
- Quill: Good but Tiptap better React integration

### Search Implementation
**Decision**: PostgreSQL full-text search
**Rationale**:
- Clarified scope: title, content, themes, author notes
- Personal blog scale doesn't need Elasticsearch
- PostgreSQL FTS handles English text well
- ts_vector for indexing, ts_rank for relevance
**Implementation Notes**:
- Create GIN index on story content + metadata
- Use websearch_to_tsquery for user-friendly search
- Rank by relevance + recency

### Email & Newsletter
**Decision**: SendGrid for transactional and marketing emails
**Rationale**:
- Reliable delivery for password resets and newsletters
- Template support for different frequencies (daily/weekly/monthly)
- Analytics tracking (opens, clicks) with privacy consent
- Free tier sufficient for 100-500 readers
**Alternatives Considered**:
- Amazon SES: More complex setup
- Mailgun: Similar but SendGrid better UI

### Image Upload & Storage
**Decision**: Local filesystem or S3-compatible storage
**Rationale**:
- Clarified: cover images are optional
- For personal blog, local storage acceptable initially
- Can migrate to S3/Cloudinary if needed
- Image optimization via Pillow (Python) or Sharp (Node)
**Implementation Notes**:
- Store path in database
- Serve via FastAPI static files or CDN

### Session & State Management
**Decision**: JWT tokens (backend), React Context (frontend)
**Rationale**:
- Stateless API with JWT in httpOnly cookies
- Frontend: React Context for auth state
- No complex state management needed (no Redux/Zustand required)
- Simple bookmark/reading progress stored in DB

### Testing Frameworks
**Decision**: pytest (backend), Vitest (frontend)
**Rationale**:
- pytest: Python standard, async support, fixture system
- Vitest: Fast, Vite-native, Jest-compatible API
- Contract tests using FastAPI TestClient
- Integration tests for 8 acceptance scenarios
**Test Categories**:
- Contract: API endpoint request/response validation
- Integration: Complete user workflows
- Unit: Business logic (moderation, archiving, search)

### Deployment Platform
**Decision**: Railway (backend), Vercel (frontend)
**Rationale**:
- Railway: Easy PostgreSQL + FastAPI deployment
- Vercel: Optimized for React/Vite static sites
- Both support environment variables and secrets
- Auto-deploy from Git branches
**Alternatives Considered**:
- Heroku: More expensive, less modern
- AWS: Over-engineered for personal blog

### Performance Optimization
**Decision**: Standard caching + CDN
**Rationale**:
- Target: <3 second page load, 500 concurrent users
- Redis for session/cache (if needed)
- Cloudflare or Vercel CDN for static assets
- Database query optimization via indexes
**Key Metrics**:
- API response: <200ms p95
- Story search: <500ms
- Newsletter send: background jobs

## Remaining Implementation Details

These items will be finalized during Phase 1 (contracts) or deferred to implementation:

1. **Reader Profile Data** (FR-013): Basic fields - name, email, theme preferences
2. **Reading Progress** (FR-019): Store scroll percentage in database
3. **Author-Reader Dialogue**: Denise can reply to comments (threaded structure)
4. **Social Sharing**: Facebook, Twitter, email share buttons
5. **Privacy Consent**: Cookie banner for analytics tracking
6. **Content Warnings**: Modal/acknowledgment before viewing sensitive stories
7. **View Counting**: Track both anonymous and authenticated readers

## Security Considerations

- HTTPS only in production
- CORS configured for frontend origin
- Rate limiting on auth endpoints (prevent brute force)
- SQL injection prevented by SQLModel/SQLAlchemy
- XSS prevented by React's escaping + CSP headers
- File upload validation (if images implemented)

## Development Workflow

Per constitution:
1. Contract tests first (API specs)
2. Integration tests for user workflows
3. Implementation to pass tests
4. Black/isort/flake8 for Python
5. ESLint for TypeScript/React
6. Pre-commit hooks for code quality

## Next Steps (Phase 1)

1. Create data-model.md with SQLModel schemas
2. Generate OpenAPI contracts for all endpoints
3. Write failing contract tests
4. Create quickstart.md for validation scenarios
5. Update CLAUDE.md with tech stack details
