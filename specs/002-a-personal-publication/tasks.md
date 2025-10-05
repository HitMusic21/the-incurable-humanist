# Tasks: The Incurable Humanist - Personal Publication Platform

**Input**: Design documents from `/specs/002-a-personal-publication/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: tech stack (FastAPI, React 19, PostgreSQL, SQLModel), project structure
2. Load design documents:
   → data-model.md: 9 entities (User, Story, Theme, StoryTheme, Comment, Bookmark, NewsletterSubscription, ReadingProgress)
   → contracts/: 4 API specs (auth, stories, admin, reader)
   → research.md: Technology decisions and best practices
   → quickstart.md: 8 acceptance scenarios + 6 edge cases
3. Generate tasks by category:
   → Setup: project init, dependencies, linting (T001-T005)
   → Contract Tests: 4 API specs → 4 test tasks [P] (T006-T009)
   → Database Models: 9 entities → 9 model tasks [P] (T010-T018)
   → Services: Business logic (auth, story, comment, newsletter) (T019-T026)
   → API Endpoints: FastAPI routers (T027-T034)
   → Frontend Components: React components [P] (T035-T046)
   → Integration Tests: 8 acceptance scenarios [P] (T047-T054)
   → Polish: Unit tests, performance, docs [P] (T055-T060)
4. Apply task rules:
   → Different files = [P] (parallel)
   → Same file = sequential
   → Tests before implementation (TDD)
5. Number sequentially (T001-T060)
6. Generate dependency graph
7. Create parallel execution examples
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/app/` (models, services, api, core)
- **Frontend**: `frontend/src/` (components, pages, lib)
- **Tests**: `backend/tests/`, `frontend/tests/`

---

## Phase 3.1: Setup

- [ ] **T001** Create backend project structure per plan: backend/app/{models,services,api,core}, backend/tests/{contract,integration,unit}
- [ ] **T002** Initialize Python backend: create venv, install FastAPI, SQLModel, pytest, alembic, uvicorn in backend/requirements.txt
- [ ] **T003** Initialize React frontend: create Vite + React 19 + TypeScript project in frontend/, configure Vitest
- [ ] **T004** [P] Configure Python linting: setup Black (100-char), isort (STDLIB→THIRDPARTY→FIRSTPARTY), flake8 (ignore E203, W503) in backend/
- [ ] **T005** [P] Configure TypeScript linting: setup ESLint with React hooks plugin, TypeScript strict mode in frontend/tsconfig.json

---

## Phase 3.2: Contract Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [ ] **T006** [P] Write contract test for auth API in backend/tests/contract/test_auth_api.py (POST /auth/register, /auth/login, /auth/me, /auth/reset-password)
- [ ] **T007** [P] Write contract test for stories API in backend/tests/contract/test_stories_api.py (GET /stories, GET /stories/{id} with theme filtering and search)
- [ ] **T008** [P] Write contract test for admin API in backend/tests/contract/test_admin_api.py (GET/POST /admin/stories, PUT/DELETE /admin/stories/{id}, POST /admin/stories/{id}/publish, GET /admin/comments, POST /admin/comments/{id}/moderate)
- [ ] **T009** [P] Write contract test for reader API in backend/tests/contract/test_reader_api.py (GET/POST /stories/{id}/comments, GET/POST/DELETE /bookmarks, POST/GET /reading-progress, POST /newsletter/subscribe)

---

## Phase 3.3: Database Models (ONLY after contract tests are failing)

- [ ] **T010** [P] Create User model in backend/app/models/user.py (id, email, hashed_password, full_name, is_author, is_active, created_at)
- [ ] **T011** [P] Create Story model in backend/app/models/story.py (id, title, content, excerpt, cover_image_url, status enum, author_notes, content_warning, view_count, read_time_minutes, author_id, timestamps, search_vector for full-text)
- [ ] **T012** [P] Create Theme model in backend/app/models/theme.py (id, name, slug, description)
- [ ] **T013** [P] Create StoryTheme junction table in backend/app/models/story.py (story_id, theme_id for many-to-many)
- [ ] **T014** [P] Create Comment model in backend/app/models/comment.py (id, content, status enum, user_id, story_id, parent_id for threading, created_at, moderated_at)
- [ ] **T015** [P] Create Bookmark model in backend/app/models/bookmark.py (id, user_id, story_id, created_at, unique constraint on user+story)
- [ ] **T016** [P] Create NewsletterSubscription model in backend/app/models/newsletter.py (id, user_id, frequency enum, is_active, preferred_themes JSON, subscribed_at, unsubscribed_at)
- [ ] **T017** [P] Create ReadingProgress model in backend/app/models/reading_progress.py (id, user_id, story_id, progress_percent 0-100, last_read_at, unique constraint on user+story)
- [ ] **T018** Create database config and session in backend/app/core/database.py (async engine, SessionLocal, Base, get_db dependency)

---

## Phase 3.4: Core Services

- [ ] **T019** Create auth service in backend/app/services/auth.py (hash_password with bcrypt, verify_password, create_access_token JWT, get_current_user dependency)
- [ ] **T020** Create story service in backend/app/services/story.py (create_story, update_story, publish_story, archive_story, get_stories with filters/pagination, search_stories with PostgreSQL full-text)
- [ ] **T021** Create comment service in backend/app/services/comment.py (create_comment pending status, moderate_comment approve/reject, get_comments_for_story approved only, support threading with parent_id)
- [ ] **T022** Create bookmark service in backend/app/services/bookmark.py (create_bookmark unique check, delete_bookmark, get_user_bookmarks with story details)
- [ ] **T023** Create reading progress service in backend/app/services/reading_progress.py (upsert_progress 0-100%, get_user_progress, get_continue_reading stories >0% <100%)
- [ ] **T024** Create newsletter service in backend/app/services/newsletter.py (subscribe with frequency enum, unsubscribe, get_subscribers_by_frequency, curate_newsletter select stories)
- [ ] **T025** Create user service in backend/app/services/user.py (create_user email validation, get_user_by_email, update_user, delete_user_data GDPR)
- [ ] **T026** Create theme service in backend/app/services/theme.py (get_all_themes, create_theme seed data: grief/migration/art)

---

## Phase 3.5: API Endpoints

- [ ] **T027** Create auth endpoints in backend/app/api/auth.py (POST /register, POST /login return JWT, GET /me protected, POST /reset-password, POST /reset-password/{token})
- [ ] **T028** Create stories endpoints in backend/app/api/stories.py (GET /stories with theme/search/pagination, GET /stories/{id} increment view_count, public access no auth)
- [ ] **T029** Create admin stories endpoints in backend/app/api/admin.py (GET /admin/stories all statuses, POST /admin/stories create draft, PUT /admin/stories/{id}, DELETE /admin/stories/{id} archive only, POST /admin/stories/{id}/publish, requires is_author=True)
- [ ] **T030** Create admin comment moderation in backend/app/api/admin.py (GET /admin/comments filter by status, POST /admin/comments/{id}/moderate approve/reject, requires is_author)
- [ ] **T031** Create comment endpoints in backend/app/api/comments.py (GET /stories/{story_id}/comments approved only, POST /stories/{story_id}/comments pending status, requires auth)
- [ ] **T032** Create bookmark endpoints in backend/app/api/bookmarks.py (GET /bookmarks user's list, POST /bookmarks add, DELETE /bookmarks/{story_id} remove, requires auth)
- [ ] **T033** Create reading progress endpoints in backend/app/api/progress.py (POST /reading-progress upsert, GET /reading-progress all user progress, requires auth)
- [ ] **T034** Create newsletter endpoints in backend/app/api/newsletter.py (POST /newsletter/subscribe with frequency, POST /newsletter/unsubscribe, requires auth)

---

## Phase 3.6: Frontend Components

- [ ] **T035** [P] Create Auth components in frontend/src/components/auth/ (Login.tsx, Register.tsx, ResetPassword.tsx forms with validation)
- [ ] **T036** [P] Create StoryList component in frontend/src/components/stories/StoryList.tsx (display stories grid, theme filters, pagination, search bar)
- [ ] **T037** [P] Create StoryCard component in frontend/src/components/stories/StoryCard.tsx (title, excerpt, cover image, themes, read time, published date)
- [ ] **T038** [P] Create StoryReader component in frontend/src/components/stories/StoryReader.tsx (full story content HTML, content warning modal if present, bookmark button, share buttons)
- [ ] **T039** [P] Create CommentForm component in frontend/src/components/comments/CommentForm.tsx (submit comment textarea, requires auth, shows "awaiting moderation" on submit)
- [ ] **T040** [P] Create CommentList component in frontend/src/components/comments/CommentList.tsx (display approved comments, threaded replies, user names, timestamps)
- [ ] **T041** [P] Create AuthorDashboard in frontend/src/components/admin/AuthorDashboard.tsx (story list with statuses, draft/published/archived tabs, create/edit/delete actions)
- [ ] **T042** [P] Create StoryEditor in frontend/src/components/admin/StoryEditor.tsx (Tiptap rich text editor, title/excerpt/themes/cover image fields, save draft/publish buttons)
- [ ] **T043** [P] Create ModerationQueue in frontend/src/components/admin/ModerationQueue.tsx (pending comments list, approve/reject buttons, story context)
- [ ] **T044** [P] Create NewsletterCurator in frontend/src/components/admin/NewsletterCurator.tsx (select stories for newsletter, preview, schedule send by frequency)
- [ ] **T045** [P] Create BookmarkList component in frontend/src/components/reader/BookmarkList.tsx (user's bookmarked stories, remove button, continue reading indicator)
- [ ] **T046** [P] Create NewsletterSubscribe component in frontend/src/components/newsletter/NewsletterSubscribe.tsx (frequency radio buttons: daily/weekly/monthly, theme checkboxes, subscribe button)

---

## Phase 3.7: Frontend Pages

- [ ] **T047** Create homepage in frontend/src/pages/index.tsx (render StoryList with all published stories, no auth required)
- [ ] **T048** Create story detail page in frontend/src/pages/story/[id].tsx (render StoryReader, CommentList, CommentForm, track reading progress on scroll)
- [ ] **T049** Create admin dashboard page in frontend/src/pages/admin/index.tsx (protected route, render AuthorDashboard, requires is_author)
- [ ] **T050** Create story editor page in frontend/src/pages/admin/stories/[id].tsx (protected route, render StoryEditor for create/edit)
- [ ] **T051** Create moderation page in frontend/src/pages/admin/moderation.tsx (protected route, render ModerationQueue)
- [ ] **T052** Create auth pages in frontend/src/pages/auth/ (login.tsx, register.tsx, reset-password.tsx)

---

## Phase 3.8: Integration Tests

- [ ] **T053** [P] Integration test: Author create and publish story in backend/tests/integration/test_author_workflows.py (Scenario 1 from quickstart: login, create draft, publish, verify public)
- [ ] **T054** [P] Integration test: Author comment moderation in backend/tests/integration/test_author_workflows.py (Scenario 2: reader submits comment, author approves, verify visible)
- [ ] **T055** [P] Integration test: Newsletter curation in backend/tests/integration/test_newsletter.py (Scenario 3: author selects stories, schedules by frequency, verify subscribers)
- [ ] **T056** [P] Integration test: Edit published story in backend/tests/integration/test_author_workflows.py (Scenario 4: edit story, verify bookmarks/comments preserved)
- [ ] **T057** [P] Integration test: Reader browse stories in backend/tests/integration/test_reader_workflows.py (Scenario 5: public access, theme filters, search, no auth)
- [ ] **T058** [P] Integration test: Reader engagement in backend/tests/integration/test_reader_workflows.py (Scenario 6: register, bookmark, comment pending, verify)
- [ ] **T059** [P] Integration test: Newsletter subscription in backend/tests/integration/test_newsletter.py (Scenario 7: subscribe with frequency/themes, receive newsletter)
- [ ] **T060** [P] Integration test: Reading progress tracking in backend/tests/integration/test_reader_workflows.py (Scenario 8: track scroll %, restore position, continue reading list)

---

## Phase 3.9: Database & Migrations

- [ ] **T061** Create initial Alembic migration in backend/alembic/versions/ (all 9 tables with relationships, indexes, constraints)
- [ ] **T062** Create full-text search migration in backend/alembic/versions/ (GIN index on story search_vector, trigger to update on insert/update)
- [ ] **T063** Seed initial data in backend/app/core/seed.py (3 themes: grief/migration/art, Denise author account with is_author=True)

---

## Phase 3.10: Integration & Middleware

- [ ] **T064** Create CORS middleware in backend/app/main.py (allow frontend origin http://localhost:5173, credentials support)
- [ ] **T065** Create JWT auth middleware in backend/app/core/security.py (verify token, extract user, check is_author for admin routes)
- [ ] **T066** Create error handling middleware in backend/app/main.py (catch validation errors, return consistent JSON responses)
- [ ] **T067** Create API client in frontend/src/lib/api/client.ts (axios with JWT interceptor, base URL, error handling)
- [ ] **T068** Create auth context in frontend/src/lib/auth/AuthContext.tsx (React Context for current user, login/logout functions)
- [ ] **T069** Create protected route wrapper in frontend/src/lib/auth/ProtectedRoute.tsx (check auth, redirect to login if needed, check is_author for admin)

---

## Phase 3.11: Polish & Testing

- [ ] **T070** [P] Unit test: Password hashing service in backend/tests/unit/test_auth_service.py (bcrypt verify, JWT creation)
- [ ] **T071** [P] Unit test: Story search service in backend/tests/unit/test_story_service.py (full-text search, ranking by relevance + recency)
- [ ] **T072** [P] Unit test: Comment moderation logic in backend/tests/unit/test_comment_service.py (approve/reject, threading)
- [ ] **T073** [P] Unit test: Newsletter frequency logic in backend/tests/unit/test_newsletter_service.py (daily/weekly/monthly subscribers)
- [ ] **T074** [P] Performance test: Story list pagination in backend/tests/performance/test_story_performance.py (verify <200ms for 20 stories)
- [ ] **T075** [P] Performance test: Search query speed in backend/tests/performance/test_search_performance.py (verify <500ms for full-text search)
- [ ] **T076** Create environment config in backend/app/core/config.py (Pydantic settings: DATABASE_URL, JWT_SECRET, SENDGRID_API_KEY from .env)
- [ ] **T077** Create Docker Compose for local dev in docker-compose.yml (PostgreSQL 14, backend, frontend services)
- [ ] **T078** Update CLAUDE.md with deployment instructions (Railway backend, Vercel frontend, env variables)
- [ ] **T079** Create manual testing checklist from quickstart.md in specs/002-a-personal-publication/manual-test-checklist.md (8 scenarios + 6 edge cases)
- [ ] **T080** Run full quickstart validation: execute all 8 scenarios manually, verify edge cases, document results

---

## Dependencies

**Critical Path**:
1. Setup (T001-T005) → Everything else
2. Contract Tests (T006-T009) → Models (T010-T018) → Services (T019-T026) → Endpoints (T027-T034)
3. Contract Tests (T006-T009) → Frontend Components (T035-T046) parallel with backend
4. Endpoints (T027-T034) + Components (T035-T046) → Pages (T047-T052)
5. Pages (T047-T052) → Integration Tests (T053-T060)
6. Services (T019-T026) → Unit Tests (T070-T073)
7. Everything → Polish (T074-T080)

**Blocking Relationships**:
- T018 (database config) blocks T019-T026 (services need DB session)
- T019 (auth service) blocks T027 (auth endpoints need service)
- T027-T034 (all endpoints) block T053-T060 (integration tests need working API)
- T067 (API client) blocks T035-T046 (components need API calls)
- T068 (auth context) blocks T069 (protected routes need context)

---

## Parallel Execution Examples

### Example 1: Contract Tests (After T001-T005)
```bash
# All contract tests can run in parallel - different API specs
Task: "Write contract test for auth API in backend/tests/contract/test_auth_api.py"
Task: "Write contract test for stories API in backend/tests/contract/test_stories_api.py"
Task: "Write contract test for admin API in backend/tests/contract/test_admin_api.py"
Task: "Write contract test for reader API in backend/tests/contract/test_reader_api.py"
```

### Example 2: Database Models (After T006-T009)
```bash
# All models independent - can create in parallel
Task: "Create User model in backend/app/models/user.py"
Task: "Create Story model in backend/app/models/story.py"
Task: "Create Theme model in backend/app/models/theme.py"
Task: "Create Comment model in backend/app/models/comment.py"
Task: "Create Bookmark model in backend/app/models/bookmark.py"
# ... etc
```

### Example 3: Frontend Components (After T027-T034)
```bash
# Components in different domains - parallel
Task: "Create Auth components in frontend/src/components/auth/"
Task: "Create StoryList component in frontend/src/components/stories/StoryList.tsx"
Task: "Create CommentForm component in frontend/src/components/comments/CommentForm.tsx"
Task: "Create AuthorDashboard in frontend/src/components/admin/AuthorDashboard.tsx"
# ... etc
```

### Example 4: Integration Tests (After T047-T052)
```bash
# Each scenario tests different workflow - parallel
Task: "Integration test: Author create and publish story"
Task: "Integration test: Author comment moderation"
Task: "Integration test: Reader browse stories"
Task: "Integration test: Newsletter subscription"
# ... etc
```

---

## Notes

- **[P] tasks** = Different files, no dependencies, safe to parallelize
- **Verify tests fail** before implementing (T006-T009 must fail, then T010+ makes them pass)
- **Commit after each task** for clear history
- **Avoid**: Vague tasks, same-file conflicts, skipping tests
- **TDD Order**: Tests (T006-T009) → Models (T010-T018) → Services (T019-T026) → Endpoints (T027-T034) → Integration (T053-T060)

---

## Task Validation Checklist

- [ ] All contract tests exist (T006-T009)
- [ ] All models created (T010-T017)
- [ ] All services implemented (T019-T026)
- [ ] All API endpoints working (T027-T034)
- [ ] All frontend components built (T035-T046)
- [ ] All integration tests pass (T053-T060)
- [ ] Manual quickstart validation complete (T080)
- [ ] Performance targets met (<3s load, 500 concurrent)

---

**Total Tasks**: 80
**Estimated Time**: 6-8 days (assuming parallel execution where marked)
**Ready for**: `/implement` or manual execution
