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
