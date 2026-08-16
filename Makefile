# Backend
.PHONY: be-install be-run be-test be-lint be-format
be-install:
	pip install -r backend/requirements.txt

be-run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend

be-test:
	pytest -q

be-lint:
	ruff check backend && flake8 backend

be-format:
	black backend && isort backend

# Manually fire the welcome-sequence scheduler locally. Override BACKEND_URL
# for a non-default port (docker-compose maps to 8010).
BACKEND_URL ?= http://localhost:8010
SCHEDULER_TOKEN ?= dev-tick-token
.PHONY: tick
tick:
	@curl -sS -X POST $(BACKEND_URL)/leads/sequence/tick \
		-H "X-Scheduler-Token: $(SCHEDULER_TOKEN)" \
		-w '\nHTTP=%{http_code}\n'

# Frontend
.PHONY: fe-install fe-dev fe-build fe-test fe-lint fe-typecheck
fe-install:
	cd frontend && npm ci

fe-dev:
	cd frontend && npm run dev

fe-build:
	cd frontend && npm run build

fe-test:
	cd frontend && npm run test

fe-lint:
	cd frontend && npm run lint

fe-typecheck:
	cd frontend && npm run typecheck

# Aggregate gates — run these before committing.
.PHONY: lint test
lint: be-lint fe-lint

test: be-test fe-test
