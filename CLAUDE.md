# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TIH2 is a full-stack application built with **FastAPI (Python)** backend and **React + TypeScript + Vite** frontend, designed to use PostgreSQL as the database.

## Tech Stack

**Backend:**
- FastAPI with uvicorn server
- SQLModel for database ORM (built on SQLAlchemy + Pydantic)
- asyncpg for PostgreSQL async operations
- Python virtual environment in `backend/venv/`

**Frontend:**
- React 19 with TypeScript
- Vite as build tool and dev server
- ESLint for linting

**Database:**
- PostgreSQL (Docker-based setup via setup script)

## Common Commands

### Backend Development

```bash
# Activate Python virtual environment
source backend/venv/bin/activate

# Install/update backend dependencies
pip install -r backend/requirements.txt

# Start backend server (when main.py exists)
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Update requirements after installing new packages
pip freeze > backend/requirements.txt
```

### Frontend Development

```bash
# Install frontend dependencies
cd frontend && npm install

# Start dev server
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Lint frontend code
cd frontend && npm run lint

# Preview production build
cd frontend && npm run preview
```

### Database Setup

The project includes a `setup.sh` script that automates the entire project setup including:
- Creating Python virtual environment
- Installing backend dependencies (FastAPI, SQLModel, asyncpg, etc.)
- Setting up React frontend with Vite and TypeScript
- Creating Docker configuration for PostgreSQL
- Generating development scripts

Run `./setup.sh` for initial project setup (if not already done).

## Project Structure

```
TIH2/
├── backend/              # FastAPI backend
│   ├── venv/            # Python virtual environment
│   └── requirements.txt # Python dependencies
├── frontend/            # React + TypeScript frontend
│   ├── src/            # Source code
│   └── package.json    # Node dependencies
├── .flake8             # Python linting config
├── pyproject.toml      # Python tooling config (black, isort)
└── setup.sh            # Project setup automation script
```

## Code Style & Linting

**Python:**
- Line length: 100 characters (black, flake8, isort)
- Black formatter with isort for import sorting
- Flake8 ignores: E203, W503
- Import ordering: STDLIB → THIRDPARTY → FIRSTPARTY

**TypeScript/React:**
- ESLint with React hooks and React refresh plugins
- TypeScript strict mode (tsconfig)

## Development Workflow

1. **Backend**: The backend code will reside in `backend/` directory. When creating FastAPI app, the main entry point is typically `backend/main.py`
2. **Frontend**: React components and application code in `frontend/src/`
3. **Database**: PostgreSQL connection configured via environment variables (DATABASE_URL)
4. **Environment**: Configuration via `.env` file (see setup.sh for template structure)

## Testing

- Backend: Use pytest for Python tests (not installed by default)
- Frontend: No test framework installed by default in the Vite template

## Key Integration Points

- Backend API typically runs on `http://localhost:8000`
- Frontend dev server runs on `http://localhost:5173` (Vite default) or configured port
- Database on `localhost:5432`
- CORS configuration needed in FastAPI to allow frontend origin
