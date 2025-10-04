<!--
Sync Impact Report:
- Version change: [unversioned template] → 1.0.0
- Principles defined:
  1. Modular Architecture (NEW)
  2. API-First Design (NEW)
  3. Type Safety & Validation (NEW)
  4. Test-Driven Development (NEW)
  5. Clean Code Standards (NEW)
- Added sections:
  1. Code Quality Standards (NEW)
  2. Development Workflow (NEW)
- Templates requiring updates:
  ✅ plan-template.md - Constitution Check gates aligned with principles
  ✅ spec-template.md - Requirements aligned with API-first approach
  ✅ tasks-template.md - Task categories support modular architecture
  ✅ agent-file-template.md - No changes needed (auto-generated)
- Follow-up TODOs: None
-->

# TIH2 Constitution

## Core Principles

### I. Modular Architecture
Every feature MUST be implemented as a self-contained module with clear boundaries and responsibilities. Modules MUST be independently testable and reusable. Backend services MUST follow domain-driven design with separation of concerns (models, services, API endpoints). Frontend components MUST be composable and follow single responsibility principle.

**Rationale**: Modular architecture enables parallel development, easier testing, and long-term maintainability. Clear boundaries prevent tight coupling and facilitate code reuse.

### II. API-First Design
All backend functionality MUST be exposed through well-defined REST APIs following OpenAPI specifications. API contracts MUST be defined before implementation. FastAPI automatic documentation and validation MUST be leveraged for all endpoints. CORS, authentication, and error handling MUST be consistently applied across all endpoints.

**Rationale**: API-first ensures frontend-backend decoupling, enables contract testing, and provides clear interface documentation. FastAPI's built-in tools enforce consistency and reduce boilerplate.

### III. Type Safety & Validation
Python backend MUST use Pydantic models for all data validation and serialization. Type hints MUST be used throughout the codebase. TypeScript MUST be used with strict mode enabled for all frontend code. SQLModel MUST be used for database ORM to leverage shared type definitions.

**Rationale**: Type safety catches errors at development time, improves IDE support, and serves as living documentation. Pydantic and TypeScript strict mode enforce contracts at runtime and compile time respectively.

### IV. Test-Driven Development (NON-NEGOTIABLE)
Tests MUST be written before implementation. Contract tests MUST verify API specifications. Integration tests MUST validate user workflows. Unit tests MUST cover business logic. Tests MUST fail before implementation begins (Red-Green-Refactor cycle strictly enforced).

**Rationale**: TDD ensures code meets requirements, facilitates refactoring, and prevents regressions. Writing tests first clarifies requirements and drives better design decisions.

### V. Clean Code Standards
Code MUST follow language-specific best practices: Python (Black formatting, isort imports, 100-char line length, flake8 compliance), React (functional components, hooks, component composition), FastAPI (async/await, dependency injection, middleware patterns). Code MUST be self-documenting with clear naming and minimal comments except for complex business logic.

**Rationale**: Consistent code style reduces cognitive load, improves collaboration, and makes code reviews more effective. Best practices leverage framework strengths and prevent common pitfalls.

## Code Quality Standards

**Python Backend Requirements**:
- Black formatter with line length 100
- isort for import ordering (STDLIB → THIRDPARTY → FIRSTPARTY)
- flake8 linting (ignore E203, W503)
- Async/await for I/O operations
- FastAPI dependency injection for services
- Pydantic models for request/response schemas
- SQLModel for database models
- Structured logging throughout

**React Frontend Requirements**:
- Functional components with hooks only
- TypeScript strict mode enabled
- Component composition over inheritance
- Custom hooks for shared logic
- ESLint with React hooks plugin
- Clear component directory structure
- Props interfaces defined for all components

**Database Requirements**:
- PostgreSQL as primary database
- SQLModel for ORM with async support
- Migrations for all schema changes
- Indexes on frequently queried fields
- Transactions for multi-step operations

## Development Workflow

**Setup Process**:
1. Python virtual environment in backend/venv/
2. Dependencies managed via requirements.txt
3. Frontend dependencies via npm/package.json
4. Docker for PostgreSQL (local development)
5. Environment variables via .env file

**Development Cycle**:
1. Feature spec defines WHAT (no implementation details)
2. Implementation plan defines HOW (tech decisions, structure)
3. Contract tests written first (API specifications)
4. Integration tests for user workflows
5. Implementation to make tests pass
6. Code review for principle compliance
7. Manual testing and documentation

**Quality Gates**:
- All tests MUST pass before merge
- Code MUST pass linting (flake8, ESLint)
- API contracts MUST be documented
- Type coverage MUST be maintained
- No console.log or print statements in production code

## Governance

**Amendment Process**:
Constitution changes require documentation of rationale, impact analysis on existing code, and update of dependent templates (plan, spec, tasks templates). All amendments MUST increment version following semantic versioning.

**Compliance Review**:
All feature plans MUST verify compliance in Constitution Check section. Non-compliance requires explicit justification in Complexity Tracking. Code reviews MUST verify adherence to core principles. Violations without justification result in rejection.

**Versioning Policy**:
- MAJOR: Breaking changes to principles or governance
- MINOR: New principles added or significant expansions
- PATCH: Clarifications, wording improvements, or minor updates

**Runtime Guidance**:
Project-specific development commands and conventions are maintained in `CLAUDE.md` at repository root. Agent-specific guidance files may exist for different AI assistants (e.g., `.github/copilot-instructions.md` for GitHub Copilot).

**Version**: 1.0.0 | **Ratified**: 2025-10-04 | **Last Amended**: 2025-10-04
