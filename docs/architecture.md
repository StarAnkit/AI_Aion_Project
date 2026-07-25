# Architecture

## Application boundaries

- `frontend` owns browser rendering and user interaction.
- `backend` owns HTTP endpoints and application behavior.
- PostgreSQL and future OpenAI code live behind backend-owned interfaces.

The database foundation keeps provider-specific mapping outside the catalog model. Provider adapters emit a common import candidate, the central CC0 policy makes the publication decision, and only then may normalized records become publicly visible. The initial artwork allowlist contains factual fields only; authored descriptions are excluded.

Provider discovery and persistence are deliberately separate. An adapter may inspect a provider's metadata response, including a temporary image URL, only to build an ephemeral candidate for the central policy. Rejected, unclear, non-CC0, conflicting-rights, and no-image candidates produce no persistence command: their records, image URLs, and image bytes must not be stored, copied, downloaded, or cached. Only an approved candidate may cross the persistence boundary. The Cleveland adapter currently uses synthetic local fixtures only; a separately approved future live import must remain capped at 50-100 records.

The Cleveland transport is metadata-only and caps each request at 100 records. It requests only the official artwork JSON endpoint and has no image-download method. A live metadata dry run may aggregate policy decisions in memory, but it must not write provider records or raw responses. A later persistent import remains a separate approval even when the dry run succeeds.

The first persistent import uses a generic catalog-import service. It accepts only already-approved candidates, reevaluates the central CC0 policy at the write boundary, stores a factual source snapshot plus official source and policy URLs, and relies on `(provider_id, external_id)` to avoid duplicates. A future provider supplies a different adapter and registration, not a different persistence path.

The public catalog read boundary is `GET /api/v1/catalog/artworks` and `GET /api/v1/catalog/artworks/{provider-code}:{external-id}`. It returns a deliberately small factual representation. Its query requires an enabled provider, published image, approved CC0 media state, an explicit non-conflicting CC0 evidence row, and no conflicting evidence. The service then rebuilds the policy candidate and re-evaluates the shared CC0 policy before serializing a response. This defense in depth prevents accidental exposure if a database row becomes inconsistent.

The catalog response includes an approved remote image URL only after those checks. It does not download or proxy image bytes. It excludes internal UUIDs, raw provider payloads, authored descriptions, and every non-public candidate.

## Design principles

- **High cohesion:** code that changes for the same reason lives together.
- **Loose coupling:** UI components depend on a small API interface, not raw networking details.
- **Explicit contracts:** TypeScript types and Pydantic models describe exchanged data.
- **Testability:** dependencies can be replaced by fakes; frontend and backend test independently.
- **Simple growth:** new backend features can follow `route -> service -> interface -> infrastructure` when real behavior exists. Empty layers are avoided for now.
