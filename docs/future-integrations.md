# Future integrations

## PostgreSQL 17

The provider-neutral catalog foundation uses SQLAlchemy 2, Alembic, and the Psycopg driver. Its initial schema separates providers, source records, normalized artwork facts, media assets, and rights evidence. Database access is configured only through `AI_AION_DATABASE_URL`; no real credentials are committed and no database is created automatically.

Cleveland Museum of Art is the approved first provider, but its future mapping belongs behind the provider adapter boundary. No Cleveland records have been fetched or imported. Future schema changes must use reviewed Alembic migrations, and database models must remain separate from public API models.

## OpenAI APIs

The first grounded AI slice is limited to explaining an already-public eligible Cleveland artwork. Its backend-owned provider receives a server-derived, provider-host-allowlisted image URL and normalized factual metadata only. It has no arbitrary prompt, URL, web search, scrape, fetch, upload, or image-proxy surface. The key remains backend-only, calls use `store=False`, outputs are bounded and typed, and routine tests use deterministic fakes.

Web research is a later, separately approved phase. It requires a reviewed allowlist of institutional, public-domain, or otherwise permitted sources; citations attached to each factual claim; original paraphrase only; and fail-closed source and rights eligibility. No arbitrary-site fallback or scraping may be added.

Before a real provider is enabled publicly, deployment must add authentication or equivalent abuse attribution, per-user or tenant quotas, distributed rate limits, maximum spend controls and alerts, safe proxy/IP handling, request metrics without prompts or secrets, and incident-response controls. The local in-process throttle is not a substitute for those controls.
