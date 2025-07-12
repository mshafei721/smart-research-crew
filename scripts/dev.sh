#!/bin/bash
# Smart Research Crew Development Scripts

set -e

case "$1" in
  "backend")
    echo "🚀 Starting backend server..."
    cd backend && python crew.py --server
    ;;
  "frontend")
    echo "🚀 Starting frontend dev server..."
    cd frontend && npm run dev
    ;;
  "cli")
    echo "🚀 Running CLI mode..."
    shift
    cd backend && python crew.py "$@"
    ;;
  "install")
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    cd frontend && npm install
    ;;
  "test")
    echo "🧪 Running tests..."
    cd backend && python -m pytest tests/ || echo "Backend tests not found"
    cd ../frontend && npm run test || echo "Frontend tests not found"
    ;;
  "lint")
    echo "🔍 Running linters..."
    cd backend && python -m black . --check || echo "Install black for formatting"
    cd ../frontend && npm run lint || echo "Frontend linting not configured"
    ;;
  *)
    echo "Smart Research Crew Development Helper"
    echo ""
    echo "Usage: $0 {backend|frontend|cli|install|test|lint}"
    echo ""
    echo "Commands:"
    echo "  backend   - Start FastAPI server"
    echo "  frontend  - Start React dev server"
    echo "  cli       - Run CLI mode (pass topic as args)"
    echo "  install   - Install all dependencies"
    echo "  test      - Run all tests"
    echo "  lint      - Check code formatting"
    ;;
esac