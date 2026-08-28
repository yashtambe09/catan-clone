# Migrations

Plain numbered SQL files, applied in order. No ORM or migration framework
(e.g. Alembic) — deliberate choice for this project's small, stable schema.
See [`db-design.md`](../../../db-design.md) at the repo root for the schema
itself and the reasoning.

- **Naming:** `NNNN_description.sql`, zero-padded, strictly increasing.
- **Fresh setup:** `docker-compose.yml` mounts this directory as
  `/docker-entrypoint-initdb.d` on the `postgres` service. The official
  Postgres image runs every file here alphabetically, but **only** the very
  first time a container starts against an empty data volume.
- **Existing dev DB:** the mount above won't re-run for a database that's
  already initialized. Apply a new migration by hand:

  ```powershell
  Get-Content -Raw backend\db\migrations\0002_your_migration.sql | docker compose exec -T postgres psql -U catan -d catan
  ```

- Each file should be additive where possible (`CREATE TABLE`,
  `ALTER TABLE ... ADD COLUMN`, etc.) so applying them in order never loses
  data on a database that already has earlier migrations applied.
