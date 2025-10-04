#!/bin/bash

# TIH2 Project Setup Script
# FastAPI + React + PostgreSQL Full Stack Application
# Author: Setup script for macOS with zsh

set -e  # Exit on any error

echo "🚀 Setting up TIH2 FastAPI + React project..."

# =============================================================================
# 1. PROJECT STRUCTURE SETUP
# =============================================================================

echo "📁 Creating project structure..."

# Create main project directories
mkdir -p backend frontend

echo "✅ Project directories created"

# =============================================================================
# 2. BACKEND SETUP (FastAPI)
# =============================================================================

echo "🐍 Setting up Python backend..."

# Create Python virtual environment
python3 -m venv backend/venv

# Activate virtual environment
source backend/venv/bin/activate

echo "✅ Python virtual environment created and activated"

# Install backend dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn[standard] sqlmodel asyncpg pydantic python-dotenv python-multipart

# Create requirements.txt
pip freeze > backend/requirements.txt

echo "✅ Backend dependencies installed"

# =============================================================================
# 3. FRONTEND SETUP (React + Vite + TypeScript)
# =============================================================================

echo "⚛️ Setting up React frontend..."

# Create React app with Vite and TypeScript
npm create vite@latest frontend -- --template react-ts

# Navigate to frontend directory and install dependencies
cd frontend

# Install base dependencies
npm install

# Install additional frontend dependencies
echo "📦 Installing frontend dependencies..."
npm install axios zustand

# Install and setup Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install shadcn/ui dependencies
npm install class-variance-authority clsx tailwind-merge lucide-react
npm install -D @types/node

echo "✅ Frontend dependencies installed"

# Go back to project root
cd ..

# =============================================================================
# 4. GIT REPOSITORY INITIALIZATION
# =============================================================================

echo "📝 Initializing Git repository..."

# Initialize git repository
git init

# Create comprehensive .gitignore
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
backend/venv/
backend/env/
backend/ENV/
backend/env.bak/
backend/venv.bak/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# NYC test coverage
.nyc_output

# Dependency directories
frontend/node_modules/
frontend/.pnp
frontend/.pnp.js

# Production builds
frontend/build/
frontend/dist/

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# Next.js build output
.next

# Nuxt.js build / generate output
.nuxt
dist

# Storybook build outputs
.out
.storybook-out

# Temporary folders
tmp/
temp/

# Database
*.db
*.sqlite3

# Docker
.dockerignore
EOF

echo "✅ Git repository initialized with .gitignore"

# =============================================================================
# 5. ENVIRONMENT CONFIGURATION
# =============================================================================

echo "🔧 Creating environment configuration..."

# Create .env file with placeholders
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/tih2_db
POSTGRES_USER=tih2_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=tih2_db

# FastAPI Configuration
SECRET_KEY=your_jwt_secret_key_here_min_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_HOST=localhost
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend Configuration (for build process)
VITE_API_URL=http://localhost:8000

# Development Settings
DEBUG=True
ENVIRONMENT=development
EOF

echo "✅ Environment file created with placeholders"

# =============================================================================
# 6. DOCKER SETUP FOR POSTGRESQL
# =============================================================================

echo "🐳 Creating Docker configuration for PostgreSQL..."

# Create docker-compose.yml for PostgreSQL
cat > docker-compose.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: tih2_postgres
    environment:
      POSTGRES_USER: tih2_user
      POSTGRES_PASSWORD: your_secure_password_here
      POSTGRES_DB: tih2_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  adminer:
    image: adminer
    container_name: tih2_adminer
    restart: unless-stopped
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  postgres_data:
EOF

# Create init.sql for database initialization
cat > init.sql << EOF
-- TIH2 Database initialization
-- This file runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Add any initial database setup here
-- Tables will be created by SQLModel/Alembic in the FastAPI app
EOF

echo "✅ Docker configuration created"

# =============================================================================
# 7. DEVELOPMENT SCRIPTS
# =============================================================================

echo "📜 Creating development scripts..."

# Create start-backend script
cat > start-backend.sh << EOF
#!/bin/bash

# Start FastAPI backend server
echo "🚀 Starting FastAPI backend server..."

# Activate virtual environment
source backend/venv/bin/activate

# Start uvicorn server with auto-reload
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Note: Make sure you have created backend/main.py with your FastAPI app
EOF

# Create start-frontend script
cat > start-frontend.sh << EOF
#!/bin/bash

# Start React frontend development server
echo "⚛️ Starting React frontend development server..."

# Navigate to frontend directory
cd frontend

# Start Vite development server
npm run dev

# The development server will be available at http://localhost:3000
EOF

# Create start-database script
cat > start-database.sh << EOF
#!/bin/bash

# Start PostgreSQL database using Docker
echo "🐘 Starting PostgreSQL database..."

# Start PostgreSQL container
docker-compose up -d postgres

echo "✅ PostgreSQL is running at localhost:5432"
echo "📊 Adminer (DB admin) available at http://localhost:8080"
echo "   Server: postgres"
echo "   Username: tih2_user"
echo "   Password: your_secure_password_here"
echo "   Database: tih2_db"
EOF

# Create stop-services script
cat > stop-services.sh << EOF
#!/bin/bash

# Stop all TIH2 services
echo "🛑 Stopping TIH2 services..."

# Stop Docker containers
docker-compose down

echo "✅ All services stopped"
EOF

# Create full-setup script
cat > dev-setup.sh << EOF
#!/bin/bash

# Complete development environment setup
echo "🔧 Setting up complete development environment..."

# Start database
echo "Starting database..."
./start-database.sh

# Wait for database to be ready
echo "Waiting for database to initialize..."
sleep 10

# Install backend dependencies if not already done
if [ ! -d "backend/venv" ]; then
    echo "Setting up backend..."
    python3 -m venv backend/venv
    source backend/venv/bin/activate
    pip install --upgrade pip
    pip install fastapi uvicorn[standard] sqlmodel asyncpg pydantic python-dotenv python-multipart
    pip freeze > backend/requirements.txt
fi

# Install frontend dependencies if not already done
if [ ! -d "frontend/node_modules" ]; then
    echo "Setting up frontend..."
    cd frontend
    npm install
    cd ..
fi

echo "✅ Development environment ready!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your actual database credentials"
echo "2. Create backend/main.py with your FastAPI application"
echo "3. Configure frontend/src/main.tsx and components"
echo "4. Run './start-database.sh' to start PostgreSQL"
echo "5. Run './start-backend.sh' to start FastAPI server"
echo "6. Run './start-frontend.sh' to start React dev server"
EOF

# Make all scripts executable
chmod +x start-backend.sh start-frontend.sh start-database.sh stop-services.sh dev-setup.sh

echo "✅ Development scripts created and made executable"

# =============================================================================
# 8. FINAL SETUP COMPLETION
# =============================================================================

echo "🎉 TIH2 project setup completed successfully!"
echo ""
echo "📋 SUMMARY:"
echo "✅ Project structure created (backend/, frontend/)"
echo "✅ Python virtual environment set up"
echo "✅ FastAPI dependencies installed"
echo "✅ React + TypeScript + Vite app created"
echo "✅ Frontend dependencies installed (axios, zustand, tailwindcss)"
echo "✅ Git repository initialized"
echo "✅ Environment configuration created"
echo "✅ Docker setup for PostgreSQL ready"
echo "✅ Development scripts created"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Update the .env file with your actual database credentials"
echo "2. Create your FastAPI application in backend/main.py"
echo "3. Configure Tailwind CSS in frontend/tailwind.config.js"
echo "4. Start development:"
echo "   • Database: ./start-database.sh"
echo "   • Backend:  ./start-backend.sh"
echo "   • Frontend: ./start-frontend.sh"
echo ""
echo "🌐 Development URLs:"
echo "• Frontend: http://localhost:3000 (React)"
echo "• Backend:  http://localhost:8000 (FastAPI)"
echo "• Database: localhost:5432 (PostgreSQL)"
echo "• DB Admin: http://localhost:8080 (Adminer)"
echo ""
echo "📁 Project structure:"
echo "TIH2/"
echo "├── backend/          # FastAPI application"
echo "│   ├── venv/         # Python virtual environment"
echo "│   └── requirements.txt"
echo "├── frontend/         # React application"
echo "├── .env             # Environment variables"
echo "├── docker-compose.yml"
echo "├── start-*.sh       # Development scripts"
echo "└── .gitignore       # Git ignore file"

# Deactivate virtual environment
deactivate 2>/dev/null || true

echo ""
echo "Happy coding! 🎯"