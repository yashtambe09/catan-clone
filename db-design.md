# Database Design

Postgres 16, running in Docker on the same laptop as the backend (see
`decisions.md` §3/§4). This doc covers the schema itself and the migrations
convention; `decisions.md` covers the hosting/backup rationale.

---

## Tables

### `users`

| Column          | Type          | Constraints              |
|-----------------|---------------|---------------------------|
| `id`            | `SERIAL`      | Primary key               |
| `username`      | `TEXT`        | `UNIQUE`, `NOT NULL`      |
| `password_hash` | `TEXT`        | `NOT NULL` — argon2id, never plaintext |
| `created_at`    | `TIMESTAMPTZ` | `NOT NULL`, default `now()` |

### `games`

| Column         | Type          | Constraints |
|----------------|---------------|-------------|
| `id`           | `SERIAL`      | Primary key |
| `started_at`   | `TIMESTAMPTZ` | `NOT NULL`, default `now()` |
| `ended_at`     | `TIMESTAMPTZ` | Nullable — set when the game finishes |
| `winner_id`    | `INTEGER`     | `REFERENCES users(id)`, nullable until the game ends |
| `player_count` | `INTEGER`     | `NOT NULL`, `CHECK (2–6)` |
| `board_size`   | `TEXT`        | `NOT NULL`, `CHECK IN ('19-hex', '30-hex')` |

### `game_players`

Join table between `games` and `users` — one row per seat.

| Column        | Type      | Constraints |
|---------------|-----------|-------------|
| `game_id`     | `INTEGER` | `NOT NULL`, `REFERENCES games(id)`, part of PK |
| `user_id`     | `INTEGER` | `NOT NULL`, `REFERENCES users(id)`, part of PK |
| `final_score` | `INTEGER` | Nullable until the game ends |
| `placement`   | `INTEGER` | Nullable until the game ends (1st, 2nd, ...) |

Primary key: `(game_id, user_id)` — a user can only occupy one seat per game.

---

## Relationships

- `games.winner_id → users.id` — the game's winner (nullable while in progress).
- `game_players.game_id → games.id` and `game_players.user_id → users.id` —
  supports both aggregate stats (wins/losses/win-rate via `COUNT`/`AVG` over
  a user's `game_players` rows) and richer queries (past-opponent history:
  join `game_players` to itself on `game_id`, excluding the current user).
- `player_count`/`board_size` live on `games` (not derived) so stats can be
  segmented by board size later without joining back through game state that
  isn't otherwise persisted.

## What's *not* persisted

Per `decisions.md` §5, the server is authoritative over live game state
(board layout, hands, dev cards, turn order), but that state lives in the
running backend process during a game — not in Postgres. Only the
start/end-of-game summary above is written to the DB. If the laptop/backend
restarts mid-game, in-progress games are lost; this is an accepted tradeoff
for a friends-only hobby server (see `decisions.md` §3).

---

## Migrations

See [`backend/db/migrations/README.md`](backend/db/migrations/README.md) for
the day-to-day mechanics (naming, how a fresh setup applies them, how to
apply a new one to an already-running dev DB).

No ORM or migration framework (e.g. SQLAlchemy + Alembic) is used —
deliberate for a 3-table schema that isn't expected to churn much. Revisit
if that stops being true.

| Migration | Adds |
|-----------|------|
| `0001_initial_schema.sql` | `users`, `games`, `game_players` |
