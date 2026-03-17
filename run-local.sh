#!/usr/bin/env bash
# Run Resume Builder on http://127.0.0.1:8000
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Creating virtual environment (.venv)..."
  python3 -m venv .venv
fi
echo "Installing dependencies (first time may take a minute)..."
.venv/bin/pip install -q -r requirements.txt
echo "Starting server at http://127.0.0.1:8000"
echo "Open that URL in your browser. Ctrl+C to stop."
exec .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
