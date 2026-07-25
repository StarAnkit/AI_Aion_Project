# Architecture

## Application boundaries

- `frontend` owns browser rendering and user interaction.
- `backend` owns HTTP endpoints and application behavior.
- Future PostgreSQL and OpenAI code will live behind backend-owned interfaces.

The only current cross-application contract is `GET /api/v1/health`. It proves the applications can communicate without inventing domain data too early.

## Design principles

- **High cohesion:** code that changes for the same reason lives together.
- **Loose coupling:** UI components depend on a small API interface, not raw networking details.
- **Explicit contracts:** TypeScript types and Pydantic models describe exchanged data.
- **Testability:** dependencies can be replaced by fakes; frontend and backend test independently.
- **Simple growth:** new backend features can follow `route -> service -> interface -> infrastructure` when real behavior exists. Empty layers are avoided for now.
