# Smart Research Crew - Development Automation
# Makefile for formatting, linting, testing, and development workflows

.PHONY: help install test lint fmt check clean dev-server dev-frontend dev build validate docs

# Default target
help:
	@echo "Smart Research Crew - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install all dependencies (backend + frontend)"
	@echo "  install-backend  Install Python dependencies"
	@echo "  install-frontend Install Node.js dependencies"
	@echo ""
	@echo "Development:"
	@echo "  dev              Start both backend and frontend in development mode"
	@echo "  dev-server       Start backend FastAPI server only"
	@echo "  dev-frontend     Start frontend Vite dev server only"
	@echo ""
	@echo "Code Quality:"
	@echo "  fmt              Format all code (Python + TypeScript)"
	@echo "  lint             Run all linters"
	@echo "  test             Run all tests"
	@echo "  check            Run format + lint + test (full check)"
	@echo ""
	@echo "Validation:"
	@echo "  validate         Validate environment and configuration"
	@echo "  docs             Generate and serve API documentation"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean            Clean build artifacts and cache"
	@echo "  build            Build production assets"

# Installation targets
install: install-backend install-frontend
	@echo "✅ All dependencies installed"

install-backend:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✅ Backend dependencies installed"

install-frontend:
	@echo "📦 Installing Node.js dependencies..."
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed"

# Development targets
dev:
	@echo "🚀 Starting development servers..."
	@echo "Backend will be available at: http://localhost:8000"
	@echo "Frontend will be available at: http://localhost:5173"
	@echo "API docs will be available at: http://localhost:8000/docs"
	@echo ""
	@echo "Press Ctrl+C to stop all servers"
	@echo ""
	@$(MAKE) -j2 dev-server dev-frontend

dev-server:
	@echo "🔧 Starting FastAPI server..."
	cd backend && python crew.py --server

dev-frontend:
	@echo "🎨 Starting Vite dev server..."
	cd frontend && npm run dev

# Code quality targets
fmt:
	@echo "🎨 Formatting Python code with Black..."
	black backend/ --line-length 100 --target-version py311
	@echo "🎨 Formatting TypeScript code with Prettier..."
	cd frontend && npm run format
	@echo "✅ Code formatting completed"

lint:
	@echo "🔍 Linting Python code with flake8..."
	flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503
	@echo "🔍 Linting TypeScript code with ESLint..."
	cd frontend && npm run lint
	@echo "✅ Code linting completed"

test:
	@echo "🧪 Running Python tests with pytest..."
	cd backend && python -m pytest tests/ -v --tb=short
	@echo "🧪 Running TypeScript tests with Vitest..."
	cd frontend && npm run test
	@echo "✅ All tests completed"

check: fmt lint test
	@echo ""
	@echo "🎉 All checks passed! Code is ready for commit."

# Validation targets
validate:
	@echo "🔍 Validating environment configuration..."
	cd backend && python crew.py --validate
	@echo "✅ Environment validation completed"

docs:
	@echo "📚 Starting API documentation server..."
	@echo "API docs will be available at: http://localhost:8000/docs"
	@echo "ReDoc will be available at: http://localhost:8000/redoc"
	cd backend && python crew.py --server &
	@echo "Press Ctrl+C to stop the server"

# Build targets
build:
	@echo "🏗️  Building frontend for production..."
	cd frontend && npm run build
	@echo "✅ Production build completed"

# Maintenance targets
clean:
	@echo "🧹 Cleaning build artifacts and cache..."
	rm -rf backend/__pycache__
	rm -rf backend/src/__pycache__
	rm -rf backend/src/*/__pycache__
	rm -rf backend/src/*/*/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf backend/tests/__pycache__
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.cache
	@echo "✅ Cleanup completed"

# Environment setup helpers
.env:
	@echo "📝 Creating .env file from .env.example..."
	cp .env.example .env
	@echo "⚠️  Please edit .env file and add your OPENAI_API_KEY"
	@echo "📖 See README.md for setup instructions"

# Git hooks
install-hooks:
	@echo "🪝 Installing git pre-commit hooks..."
	echo '#!/bin/bash\nmake check' > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "✅ Git hooks installed"

# Quick commands for common workflows
quick-start: install .env validate
	@echo ""
	@echo "🎉 Quick setup completed!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env file and add your OPENAI_API_KEY"
	@echo "2. Run 'make dev' to start development servers"
	@echo "3. Open http://localhost:5173 for the app"
	@echo "4. Open http://localhost:8000/docs for API docs"

# Production deployment helpers
prod-check: install check build validate
	@echo "✅ Production readiness check completed"

# Testing with coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	cd backend && python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in backend/htmlcov/"

# Performance testing
test-performance:
	@echo "🚀 Running performance tests..."
	cd backend && python -m pytest tests/ -v -k "performance"
	@echo "✅ Performance tests completed"

# Security testing
test-security:
	@echo "🔒 Running security tests..."
	cd backend && python -m pytest tests/ -v -k "security"
	@echo "✅ Security tests completed"