# Future integrations

## PostgreSQL 17

The provider-neutral catalog foundation uses SQLAlchemy 2, Alembic, and the Psycopg driver. Its initial schema separates providers, source records, normalized artwork facts, media assets, and rights evidence. Database access is configured only through `AI_AION_DATABASE_URL`; no real credentials are committed and no database is created automatically.

Cleveland Museum of Art is the approved first provider, but its future mapping belongs behind the provider adapter boundary. No Cleveland records have been fetched or imported. Future schema changes must use reviewed Alembic migrations, and database models must remain separate from public API models.

## OpenAI APIs

No model, SDK, prompt, key, or credential placeholder is included. First define the AI-assisted outcome plus input, output, latency, privacy, and evaluation requirements. Then add a backend-owned provider interface. Keep credentials only in runtime environment configuration and use deterministic fakes in routine tests.
