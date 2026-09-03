# DevPulse AI

All your tech updates. One place.

DevPulse AI is a production-ready MVP web platform that collects trusted developer updates, removes duplicate information, and shows the updates that matter to a developer's technology stack.

## Stack

- Frontend: React, Vite, TypeScript, Tailwind CSS, shadcn-style UI primitives, React Router, TanStack Query
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, APScheduler, Pytest
- Database: PostgreSQL
- External content provider: Tavily Search, Tavily Extract, Tavily Crawl only

## Quick Start

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

Frontend: http://localhost:5173
Backend: http://localhost:8000
API health: http://localhost:8000/api/health

Set `TAVILY_API_KEY` in `backend/.env` to ingest live developer updates. Without it, the app still starts but no external updates are fetched.
