# AI_Aion_Project

A clean full-stack starting point with a React + TypeScript frontend and a FastAPI backend.

This scaffold intentionally contains no dataset, database schema, PostgreSQL connection, OpenAI SDK, or OpenAI credentials. Those decisions come later, once concrete product requirements exist.

## Structure

```text
AI_Aion_Project/
├── frontend/   # Browser UI: React, TypeScript, Vite
├── backend/    # HTTP API: FastAPI, Python
└── docs/       # Architecture and future-integration notes
```

The two applications are independent so each can be developed, tested, and deployed without tightly coupling it to the other.

## Prerequisites

- Node.js 22+
- Python 3.12+
- PostgreSQL 17 later (not needed yet)

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Vite normally opens at `http://localhost:5173`. To verify it, run `npm run check`.

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`; its interactive docs are at `http://localhost:8000/docs`. Verify it with `ruff check .` and `pytest`.

Read [docs/architecture.md](docs/architecture.md) for how the pieces fit together and [docs/future-integrations.md](docs/future-integrations.md) before adding PostgreSQL or OpenAI.
