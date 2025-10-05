
# Implementation Plan: The Incurable Humanist - Personal Publication Platform

**Branch**: `002-a-personal-publication` | **Date**: 2025-10-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-a-personal-publication/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
A personal publication platform for Denise Rodriguez Dao to write and share stories about grief, migration, and art. Single-author model where Denise creates content and readers engage through comments, bookmarks, and newsletter subscriptions. Platform supports rich text formatting, theme-based organization, comment moderation, and customizable newsletter delivery.

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript/React 19 (frontend)
**Primary Dependencies**: FastAPI, React 19, Vite, SQLModel, PostgreSQL
**Storage**: PostgreSQL (relational database for stories, users, comments, bookmarks)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web application (Railway/Vercel hosting)
**Project Type**: web (frontend + backend)
**Performance Goals**: <3 seconds page load, support 500 concurrent readers
**Constraints**: Personal blog scale (100-500 readers), English-only interface
**Scale/Scope**: Single author, ~50 stories, 500 max concurrent users, basic analytics

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Modular Architecture
- [x] Feature designed as self-contained module with clear boundaries? YES - Author/Reader/Content modules
- [x] Backend follows domain separation (models/services/API)? YES - Stories, Users, Comments domains
- [x] Frontend components are composable and single-responsibility? YES - StoryList, CommentForm, etc.
- [x] Dependencies between modules minimized and explicit? YES - Clear entity relationships

### Principle II: API-First Design
- [x] API contracts defined before implementation? YES - Will create OpenAPI specs in Phase 1
- [x] OpenAPI/contract specifications created? Planned for Phase 1
- [x] CORS, auth, error handling patterns identified? YES - Email/password auth, reader/author roles
- [x] FastAPI automatic docs will be leveraged? YES - Built-in Swagger/ReDoc

### Principle III: Type Safety & Validation
- [x] Pydantic models planned for all data validation? YES - Story, User, Comment schemas
- [x] TypeScript strict mode will be used? YES - React 19 with TS strict
- [x] SQLModel selected for database ORM? YES - PostgreSQL with SQLModel
- [x] Type hints planned throughout codebase? YES - All Python and TypeScript

### Principle IV: Test-Driven Development
- [x] Contract tests planned before implementation? YES - API endpoint tests first
- [x] Integration tests mapped to user workflows? YES - 8 acceptance scenarios from spec
- [x] Unit tests identified for business logic? YES - Moderation, archiving, search
- [x] TDD cycle (Red-Green-Refactor) will be followed? YES - Tests before implementation

### Principle V: Clean Code Standards
- [x] Python: Black/isort/flake8 configured (100-char)? YES - Per constitution
- [x] React: Functional components + hooks approach? YES - React 19 patterns
- [x] FastAPI: async/await + dependency injection? YES - Async DB operations
- [x] Code will be self-documenting with clear naming? YES - Clear domain language

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── app/
│   ├── models/          # SQLModel database models
│   │   ├── user.py      # User, Author entities
│   │   ├── story.py     # Story, Theme entities
│   │   ├── comment.py   # Comment entity
│   │   └── newsletter.py # Newsletter, Subscription entities
│   ├── services/        # Business logic layer
│   │   ├── auth.py      # Authentication service
│   │   ├── story.py     # Story CRUD and search
│   │   ├── comment.py   # Comment moderation
│   │   └── newsletter.py # Newsletter curation and delivery
│   ├── api/             # FastAPI routers
│   │   ├── auth.py      # /auth endpoints
│   │   ├── stories.py   # /stories endpoints
│   │   ├── comments.py  # /comments endpoints
│   │   ├── admin.py     # /admin (author dashboard)
│   │   └── newsletter.py # /newsletter endpoints
│   ├── core/            # Config, database, dependencies
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   └── main.py          # FastAPI app entry
├── tests/
│   ├── contract/        # API contract tests
│   ├── integration/     # User workflow tests
│   └── unit/            # Business logic tests
└── requirements.txt

frontend/
├── src/
│   ├── components/
│   │   ├── auth/        # Login, Register, ResetPassword
│   │   ├── stories/     # StoryList, StoryReader, StoryCard
│   │   ├── comments/    # CommentForm, CommentList
│   │   ├── admin/       # AuthorDashboard, StoryEditor, ModerationQueue
│   │   └── layout/      # Header, Footer, Navigation
│   ├── pages/
│   │   ├── index.tsx    # Homepage (story list)
│   │   ├── story/[id].tsx # Individual story view
│   │   ├── admin/       # Author dashboard pages
│   │   └── auth/        # Auth pages
│   ├── lib/
│   │   ├── api/         # API client functions
│   │   └── hooks/       # Custom React hooks
│   └── types/           # TypeScript interfaces
├── tests/
│   └── components/      # Component tests
└── package.json
```

**Structure Decision**: Web application architecture selected. Backend uses FastAPI with domain-driven design (models/services/API separation). Frontend uses React 19 with component-based architecture. This structure supports the single-author publication model with clear separation between author admin features and public reader features.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract file → contract test task [P] (4 API specs = 4 test tasks)
- Each entity from data-model.md → model creation task [P] (9 entities)
- Each acceptance scenario → integration test task (8 scenarios)
- Implementation tasks to make tests pass

**Ordering Strategy**:
1. **Setup** (T001-T003): Project structure, dependencies, linting
2. **Contract Tests** (T004-T007): API specs → failing tests [P]
3. **Database Models** (T008-T016): SQLModel entities [P]
4. **Services Layer** (T017-T024): Business logic (auth, story, comment, newsletter)
5. **API Endpoints** (T025-T032): FastAPI routers to pass contract tests
6. **Frontend Components** (T033-T044): React components [P]
7. **Integration Tests** (T045-T052): User workflows from quickstart
8. **Polish** (T053-T058): Performance, error handling, documentation

**Task Breakdown by Domain**:
- **Auth**: Register, login, password reset, JWT middleware
- **Stories**: CRUD, search, archiving, theme management
- **Comments**: Submit, moderate (approve/reject), threading
- **Reader Features**: Bookmarks, reading progress, profile
- **Newsletter**: Subscribe, curate, send (with frequency options)
- **Admin Dashboard**: Story editor, moderation queue, analytics

**Parallel Execution Opportunities** (marked [P]):
- All contract tests can run in parallel (different API specs)
- All database models can be created in parallel (independent entities)
- Frontend components can be built in parallel (different domains)
- Different services can be developed in parallel (auth vs story vs comment)

**Estimated Output**: ~55-60 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md created
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md, CLAUDE.md updated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) - Strategy documented above
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS - All principles aligned
- [x] Post-Design Constitution Check: PASS - Modular, API-first, type-safe design
- [x] All NEEDS CLARIFICATION resolved - Via /clarify session
- [x] Complexity deviations documented - None, all principles followed

**Artifacts Generated**:
- [x] /specs/002-a-personal-publication/research.md
- [x] /specs/002-a-personal-publication/data-model.md
- [x] /specs/002-a-personal-publication/contracts/auth-api.yaml
- [x] /specs/002-a-personal-publication/contracts/stories-api.yaml
- [x] /specs/002-a-personal-publication/contracts/admin-api.yaml
- [x] /specs/002-a-personal-publication/contracts/reader-api.yaml
- [x] /specs/002-a-personal-publication/quickstart.md
- [x] /CLAUDE.md (updated with tech stack)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
