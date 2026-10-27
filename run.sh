#!/usr/bin/env bash
# TRINETRA — KSP Datathon 2026 one-command launcher.
# Starts the FastAPI engine (:8077) and the Vite dev server (:5173).
# Run from anywhere: ./trinetra/run.sh
set -euo pipefail

# Resolve the directory this script lives in (the trinetra/ root).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$SCRIPT_DIR/backend"
FRONTEND="$SCRIPT_DIR/frontend"

PY="${PYTHON:-python3}"

echo "==> TRINETRA launcher"
echo "    backend:  $BACKEND"
echo "    frontend: $FRONTEND"

# --- Backend -------------------------------------------------------------
echo "==> Installing backend dependencies"
"$PY" -m pip install -r "$BACKEND/requirements.txt"

if [ ! -f "$BACKEND/trinetra.db" ]; then
  echo "==> Generating synthetic FIR database (4000 cases)"
  ( cd "$BACKEND" && "$PY" generate_data.py )
else
  echo "==> trinetra.db already present (delete it to regenerate)"
fi

echo "==> Starting FastAPI engine on :8077"
( cd "$BACKEND" && "$PY" -m uvicorn app.main:app --port 8077 ) &
BACKEND_PID=$!

# --- Frontend ------------------------------------------------------------
echo "==> Installing frontend dependencies"
( cd "$FRONTEND" && npm install )

echo "==> Starting Vite dev server on :5173"
( cd "$FRONTEND" && npm run dev -- --port 5173 --host 127.0.0.1 ) &
FRONTEND_PID=$!

echo ""
echo "==> TRINETRA is up:"
echo "      Engine : http://127.0.0.1:8077/health"
echo "      App    : http://127.0.0.1:5173/"
echo "    Press Ctrl+C to stop both."

# Stop both children on exit.
trap 'echo; echo "==> Stopping..."; kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' INT TERM EXIT

wait
