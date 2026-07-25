# Future integrations

## PostgreSQL 17

No schema, ORM, driver, migration tool, dataset, or connection string is selected. First define the user workflow and information that must persist. Then model it, choose the access and migration approach, and put PostgreSQL implementations behind backend repository interfaces. Keep database models separate from public API models.

## OpenAI APIs

No model, SDK, prompt, key, or credential placeholder is included. First define the AI-assisted outcome plus input, output, latency, privacy, and evaluation requirements. Then add a backend-owned provider interface. Keep credentials only in runtime environment configuration and use deterministic fakes in routine tests.
