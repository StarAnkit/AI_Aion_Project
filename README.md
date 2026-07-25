# AI_Aion_Project

A clean full-stack starting point with a React + TypeScript frontend and a FastAPI backend.

The project now includes a provider-neutral PostgreSQL catalog foundation and a fail-closed CC0 rights policy. It still contains no imported dataset, real database credentials, OpenAI SDK, or OpenAI credentials.

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
- PostgreSQL 17 (needed only when you are ready to apply database migrations)

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Vite normally opens at `http://localhost:5173`. To verify it, run `npm run check`.

The frontend gallery reads `VITE_API_BASE_URL` (default `/api/v1`). During local development, Vite proxies `/api` to `VITE_API_PROXY_TARGET` (default `http://localhost:8000`), so start the FastAPI backend before opening the gallery. Artwork detail links use `?artwork={provider-code}:{external-id}` and remain shareable without adding a client-side router.

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`; its interactive docs are at `http://localhost:8000/docs`. Verify it with `ruff check .` and `pytest`.

## Read-only catalog API

After applying the database migration and importing approved records, the backend exposes only assets that are published, explicitly CC0, and supported by non-conflicting rights evidence:

```text
GET /api/v1/catalog/artworks?limit=20&offset=0
GET /api/v1/catalog/artworks/{provider-code}:{external-id}
```

For the current Cleveland records, a detail identifier looks like `cleveland:12345`. Responses contain factual artwork metadata, the approved remote image URL, official source URL, provider attribution, and CC0 evidence. They never include database UUIDs, raw source payloads, authored descriptions, or unpublished/non-CC0 assets.

## Database migrations

Database features read `AI_AION_DATABASE_URL` from your uncommitted `backend/.env` file. The health endpoint does not require a database connection.

After creating a local PostgreSQL 17 database and setting that environment variable, apply the reviewed schema from `backend`:

```bash
alembic upgrade head
```

No database is created automatically. Read [docs/architecture.md](docs/architecture.md) for how the pieces fit together and [docs/future-integrations.md](docs/future-integrations.md) before adding OpenAI.
