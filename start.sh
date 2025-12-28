#!/bin/bash

cd "$(dirname "$0")"

lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

npx concurrently \
  -n "BACKEND,FRONTEND" \
  -c "blue,green" \
  --kill-others \
  "cd apps/server && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000" \
  "cd apps/front && pnpm dev"