# CLAUDE.md

Real-time multiplayer Catan clone. Full context lives in `decisions.md` (architecture, stack, scope decisions) and `flow.md` (day-by-day task/model plan) — read both before starting a new day's work. This file is a lean reference, not a substitute.

## 1. Stack & Structure

- **Backend:** Python 3.12, FastAPI + python-socketio (ASGI-mounted), `uvicorn --reload`. `backend/app/main.py` is the entrypoint.
- **Frontend:** React 18 + Redux Toolkit, Vite dev server, `socket.io-client`. Plain JS (no TypeScript). `frontend/src/` holds `App.jsx`, `socket.js`, and `store/` (Redux slices).
- **Database:** Postgres 16 (Docker, on-laptop, not yet wired into backend code — lands Day 2).
- **Orchestration:** `docker-compose.yml` at repo root — `backend`, `frontend`, `postgres` services, all hot-reloading via bind mounts. Resource limits set per-service under `deploy.resources.limits`.
- Server is authoritative; the client never trusts its own state for game logic (applies once game logic exists).

## 2. Coding Conventions

- Backend: standard FastAPI route/service structure as it grows; no ORM chosen yet (add when Day 2 DB work lands — don't pre-guess it).
- Frontend: one Redux slice per concern under `src/store/`; components stay presentational, side effects (socket events) live in `useEffect` or dedicated middleware as it grows.
- No custom crypto — auth (Day 2+) uses `argon2-cffi`/`passlib` and vetted JWT libraries only.
- Don't add abstractions, error handling, or config for cases that can't happen yet at this stage of the project — this is a greenfield build, not a hardening pass.
- Tests: pytest, in `backend/tests/`. Run with `docker compose exec backend pytest -q`. Pure game logic under `backend/app/game/` is expected to stay fully testable without a DB or socket connection — keep it that way.

## 3. Working Conventions (Token Discipline)

- Use **Plan Mode** before implementing any multi-file or architecturally uncertain feature — don't explore live via trial-and-error edits.
- Reference specific files with `@file` syntax rather than whole directories when scoping work.
- Periodically check `/context` and `/usage` to monitor what's consuming the context window.
- Treat this file and tool definitions as stable. Avoid mid-session edits to `CLAUDE.md` — they invalidate prompt caching.

## 4. Model Guidance

`flow.md` specifies a suggested model (Sonnet/Opus) and effort level per day. Default to what's specified there; override only if a given day's task proves clearly harder or easier than its listed effort suggests.

## 5. Tooling Status

**Graphify** is installed and active (see its own rules section below). **claude-mem was deliberately NOT installed** — every provider option it offered either bills a personal API key or draws on the Claude Code account authenticated in this terminal, which is BETSOL's, not a personal one; not worth spending company usage on a personal side project. **CLAUDE.md is the sole persistent-context mechanism for this project** — there is no dynamic/session memory layer alongside it, so keep this file honest and current rather than assuming something else is filling gaps.

## 6. Full Context

For anything not covered above — scope, schema, hosting plan, tooling rationale, open decisions — see [`decisions.md`](decisions.md) and [`flow.md`](flow.md).

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
