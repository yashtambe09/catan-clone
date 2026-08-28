# CATAN Project — Day-by-Day Flow
**Domain:** catan.mightyeaption.in
**Repo:** https://github.com/yashtambe09/catan-clone — single repo, one commit per day minimum
**Stack:** Python backend (FastAPI + python-socketio) · React + Redux frontend · Postgres (Docker, on-laptop) · Docker Compose local hosting → Cloudflare Pages (UI) + Cloudflare Tunnel (backend)
**Players:** 2–6 · Boards: 19-hex (2–4p) / 30-hex (5–6p) · Win condition: 10 VP standard, all player counts

> **How to use this file:** each day has a Focus, Model, Effort, Task list, and a Suggested Prompt to kick off the Claude Code session. Model/Effort are recommendations — override if a task turns out harder or easier than expected. Commit at end of day, referencing the day number and CTN-### code (e.g. `Day 4: hex board generator (CTN001)`).

---

## Phase 1: Logic + Basic UI + Local Docker (Days 1–16)

### Day 1 — Project Scaffold
- **Focus:** Repo + Docker skeleton
- **Model:** Sonnet
- **Effort:** Low
- **Tasks:**
  - Docker Compose skeleton: backend (Python/FastAPI), frontend (React), Postgres services
  - Write initial `CLAUDE.md` (stack, conventions, test commands, directories to avoid)
  - Confirm `decisions.md` is in repo root and referenced
- **Suggested prompt:**
  > Scaffold a monorepo for a real-time multiplayer Catan clone. Backend: Python 3.12, FastAPI, python-socketio. Frontend: React + Redux (Vite). Add a docker-compose.yml with backend, frontend, and postgres services, each with hot-reload for local dev. Don't implement game logic yet — just a working "hello world" health-check endpoint and a blank React shell that connects via socket.io.

### Day 2 — DB Schema + Auth Scaffold
- **Focus:** Postgres schema, hand-rolled auth
- **Model:** Sonnet
- **Effort:** Low–Medium
- **Tasks:**
  - `users`, `games`, `game_players` tables (see schema in decisions.md)
  - Password hashing via `passlib`/`argon2-cffi` (no custom crypto)
  - Session/JWT handling
  - `pg_dump` backup script (cron wiring deferred to Day 27)
- **Suggested prompt:**
  > Add a Postgres schema with users, games, and game_players tables (see decisions.md for the exact columns). Implement signup/login endpoints in FastAPI using argon2 for password hashing and JWT for sessions. Write a pg_dump backup shell script that dumps to a separate /backups directory, keeps the last 14 days, and prints a restore command in a comment — don't wire up cron yet.

### Day 3–4 — Hex-Grid Board Generation
- **Focus:** Core board data model, parameterized for both board sizes
- **Model:** Opus
- **Effort:** High
- **Tasks:**
  - Axial/cube coordinate hex grid
  - Board generator parameterized by player count (19-hex for 2–4p, 30-hex for 5–6p)
  - Tile/number-token randomization with fairness constraints (no adjacent 6/8, resource distribution balance)
- **Suggested prompt:**
  > Implement a hex-grid board generator using axial coordinates. It must support two board sizes selected by player count: a 19-hex board (rows 3-4-5-4-3) for 2–4 players, and a 30-hex board (rows 3-4-5-6-5-4-3) for 5–6 players. Randomize terrain tiles and number tokens with fairness constraints: no two adjacent hexes both bearing 6 or 8, and roughly even resource-type distribution. Write this as pure, testable logic separate from any rendering code — include unit tests for the fairness constraint.

### Day 5 — Minimal Board Rendering
- **Focus:** Bare-functional SVG board render
- **Model:** Sonnet
- **Effort:** Low
- **Tasks:**
  - Plain SVG hex rendering, no styling — just functional hexes + number labels
  - Confirm both board sizes render correctly
- **Suggested prompt:**
  > Render the hex board data model from Day 3-4 as plain SVG in React — no styling, just correctly positioned hexes with terrain-type text labels and number tokens. Verify it works for both the 19-hex and 30-hex layouts.

### Day 6–7 — Lobby, WebSocket, Player Join Flow
- **Focus:** Room system, connection handling
- **Model:** Sonnet
- **Effort:** Medium
- **Tasks:**
  - Lobby/room creation with player-count selector (2–6)
  - WebSocket connection via python-socketio, room-scoped events
  - Player join/leave flow, board generated on room start based on selected count
- **Suggested prompt:**
  > Implement a lobby system: a room can be created, players join via a room code, and the host selects player count (2-6) before starting. On start, generate the correct board size and broadcast initial game state to all connected players via socket.io rooms. Handle basic join/leave events.

### Day 8–9 — Turn State Machine
- **Focus:** Core turn loop
- **Model:** Opus
- **Effort:** Medium–High
- **Tasks:**
  - Turn phases: roll → resource distribution → robber-on-7 → build/trade → end turn
  - Server-authoritative state (never trust client)
- **Suggested prompt:**
  > Implement the core turn state machine server-side: dice roll → resource distribution to all players → robber activation on a roll of 7 (discard-half rule for players with 8+ cards, then robber placement + steal) → build/trade phase → end turn. State must be authoritative on the server; the client only renders what it's sent. Write it as an explicit state machine, not implicit if/else chains.

### Day 10–11 — Placement Rules
- **Focus:** Settlement/road/city rules, both board sizes
- **Model:** Opus
- **Effort:** High
- **Tasks:**
  - Distance rule (no adjacent settlements)
  - Road connectivity requirements
  - Initial placement phase (special turn order)
  - Test against **both** board adjacency graphs, not just the 4-player one
- **Suggested prompt:**
  > Implement settlement, road, and city placement validation: the distance rule (settlements must be 2+ edges apart), road connectivity (roads must connect to the player's existing network or a new settlement), and the special initial-placement turn order (snake draft, 2 settlements + 2 roads per player before normal turns begin). Test this against both the 19-hex and 30-hex adjacency graphs — the 30-hex board's initial placement order needs to account for more players.

### Day 12 — Bank Trading + Ports
- **Focus:** Bank trade ratios
- **Model:** Sonnet
- **Effort:** Medium
- **Tasks:**
  - 4:1 bank trades, 3:1/2:1 port trades
  - Resource UI (basic)
- **Suggested prompt:**
  > Implement bank trading: standard 4:1 trades, and port-based 3:1 (generic) and 2:1 (resource-specific) trades where the player has a settlement/city on a port hex. Add basic resource-count UI to the React frontend.

### Day 13 — Player-to-Player Trading
- **Focus:** Trade offers/counteroffers
- **Model:** Sonnet
- **Effort:** Medium
- **Tasks:**
  - Offer/counteroffer flow between players
  - Accept/reject/cancel handling over WebSocket
- **Suggested prompt:**
  > Implement player-to-player trading: a player can propose a trade to a specific player or broadcast to all, others can counteroffer, accept, or reject. All state changes go through the server; broadcast trade state updates to the relevant players only.

### Day 14 — Dev Cards + Tooling Install
- **Focus:** Deck, hidden hands, knight
- **Model:** Sonnet
- **Effort:** Medium
- **Tasks:**
  - Dev card deck (knights, VP, progress cards)
  - Hidden per-player hands (server enforces visibility)
  - Knight card → robber trigger
  - **Install Graphify** (post-commit hook wired up) and **claude-mem** today
- **Suggested prompt:**
  > Implement the development card deck and per-player hidden hands (14 knights, 5 VP, 2 each of monopoly/road building/year of plenty in the standard deck — adjust proportionally if needed for player count). Ensure the server never sends other players' hidden cards to the client. Implement playing a knight card: triggers robber movement + steal, same as rolling a 7.

### Day 15 — Progress Cards + Longest Road
- **Focus:** Monopoly/road building/year of plenty, longest road recalculation
- **Model:** Opus
- **Effort:** High
- **Tasks:**
  - Monopoly, Road Building, Year of Plenty card effects
  - Longest road recalculation (including branching paths) — flagged as the trickiest rule in the whole project
- **Suggested prompt:**
  > Implement the three progress cards (Monopoly: take all of one resource type from all players; Road Building: place 2 roads free; Year of Plenty: take any 2 resources from the bank). Then implement longest-road calculation: find the longest continuous path of a player's roads, correctly handling branching paths (a Y-shaped network should return the longest single path, not the total road count), and award/transfer the Longest Road card (2 VP) when a player exceeds the current holder's length (minimum 5 to first claim). Write dedicated unit tests for branching-path edge cases.

### Day 16 — Largest Army, Win Conditions, Game Persistence
- **Focus:** Scoring, win check, DB write on game end
- **Model:** Opus
- **Effort:** Medium–High
- **Tasks:**
  - Largest Army (3+ knights played, 2 VP, transferable)
  - Hidden VP dev cards counted at win-check only
  - Win condition check (10 VP) after every state change
  - On game end: write to `games` + `game_players` tables
- **Suggested prompt:**
  > Implement Largest Army (awarded at 3+ knights played, transferable like Longest Road) and the full victory point calculation including hidden VP dev cards (only revealed/counted when checking for a win). Check win condition (10 VP) after every relevant state change. On game end, persist the result to Postgres: insert a row into games (start/end time, winner, player_count, board_size) and one row per player into game_players (final score, placement). This is the full ruleset complete — do a full rules read-through against decisions.md before marking this done.

**✅ Full ruleset playable locally via Docker at this point.**

---

## Phase 2: UI/UX (Days 17–23)

### Day 17 — UI Library Decision + Auth Screens
- **Focus:** Pick component library, build signup/login
- **Model:** Sonnet
- **Effort:** Low–Medium
- **Tasks:**
  - **Decide UI library** (deferred decision — revisit shadcn/ui, Radix, or alternatives now that the app is real)
  - Signup/login screens wired to Day 2 auth endpoints
- **Suggested prompt:**
  > [Fill in once UI library is chosen] Build signup and login screens using [library], wired to the existing auth endpoints. Handle validation errors and loading states.

### Day 18 — Career/Stats Page
- **Focus:** Stats screen
- **Model:** Sonnet
- **Effort:** Low–Medium
- **Tasks:**
  - Wins/losses/games played, win rate
  - Past-opponent history (via `game_players` join)
- **Suggested prompt:**
  > Build a career/stats page: aggregate wins, losses, games played, and win rate for the logged-in user from game_players. Add a match history list showing past games with opponents' usernames and final placements.

### Day 19 — Board Visual Polish
- **Focus:** Board art/styling
- **Model:** Sonnet
- **Effort:** Low
- **Tasks:**
  - Replace plain SVG with styled terrain hexes, harbor icons, robber piece
- **Suggested prompt:**
  > Restyle the board rendering with proper terrain colors/textures, harbor icons at port hexes, and a robber piece that visually sits on its current hex. Keep it clean and readable at a glance — this isn't a full art pass, just clear and pleasant.

### Day 20 — Trade/Build Panels
- **Focus:** Trade and build UI
- **Model:** Sonnet
- **Effort:** Low–Medium
- **Tasks:**
  - Build menu (settlement/road/city/dev card costs shown)
  - Trade panel (bank + player-to-player)
- **Suggested prompt:**
  > Build the trade and build UI panels: a build menu showing available actions with resource costs greyed out if unaffordable, and a trade panel supporting both bank trades and player-to-player offers built in Day 12-13.

### Day 21 — Player Dashboards + Turn Indicators
- **Focus:** Multi-player status UI
- **Model:** Sonnet
- **Effort:** Low
- **Tasks:**
  - Per-player resource/card counts, VP totals, turn indicator
- **Suggested prompt:**
  > Build player dashboard components showing each player's resource card count (not contents, for opponents), visible VP, and dev cards played. Add a clear current-turn indicator.

### Day 22 — Animations
- **Focus:** Dice roll, resource distribution feedback
- **Model:** Sonnet
- **Effort:** Low
- **Tasks:**
  - Dice roll animation, resource-gain feedback
- **Suggested prompt:**
  > Add a dice roll animation and a brief visual feedback animation when players receive resources. Keep animations short (under 1s) so they don't slow down gameplay pacing.

### Day 23 — Responsive Layout + Polish Pass
- **Focus:** Layout, sound, general polish
- **Model:** Sonnet
- **Effort:** Low–Medium
- **Tasks:**
  - Responsive layout check, optional sound feedback, general UI polish pass
- **Suggested prompt:**
  > Do a responsive layout pass across common laptop/desktop screen sizes (this isn't a mobile app, but should not break at smaller windows). Add optional sound effects for dice roll, build, and trade actions. General polish pass on spacing/consistency.

---

## Phase 3: Local Host + LAN Testing (Days 24–25)

### Day 24 — Full Local Docker Test
- **Focus:** Load and correctness testing, all player counts
- **Model:** Sonnet (Opus if bugs found are non-trivial)
- **Effort:** Medium
- **Tasks:**
  - Run full games at 2, 4, and 6 players locally via Docker
  - Check resource usage/limits under 6-player load
- **Suggested prompt:**
  > Run through full test games at 2, 4, and 6 players against the local Docker stack. Log and fix any state-sync bugs, especially around the 30-hex board and 6-player turn order. Check Docker container resource usage stays within the configured limits under 6-player load.

### Day 25 — LAN Playtest with Friends
- **Focus:** Real multi-device test, reconnect handling
- **Model:** Sonnet (Opus for hard bugs)
- **Effort:** Medium
- **Tasks:**
  - Real LAN game with friends' devices
  - Deliberately test disconnect/reconnect mid-game
  - Bug triage list
- **Suggested prompt:**
  > [Session-driven — fix bugs found during the live LAN playtest.] Prioritize reconnect handling: confirm a player who drops mid-game can rejoin and receive a full state resync without breaking the game for others.

---

## Phase 4: Deployment (Days 25–30)

### Day 26 — Cloudflare Pages (Frontend) + DNS
- **Focus:** Frontend hosting, subdomain setup
- **Model:** Sonnet
- **Effort:** Low
- **Tasks:**
  - Deploy React build to Cloudflare Pages
  - Point `catan.mightyeaption.in` subdomain via Cloudflare DNS
- **Suggested prompt:**
  > Set up a Cloudflare Pages deployment for the React frontend build, and configure DNS so catan.mightyeaption.in resolves to it.

### Day 27 — Backend Tunnel + Backup Cron
- **Focus:** Cloudflare Tunnel, env secrets, backup automation
- **Model:** Sonnet
- **Effort:** Low–Medium
- **Tasks:**
  - `cloudflared` tunnel from laptop backend to Cloudflare
  - Env/secrets management (never commit `.env`)
  - Wire up the Day 2 `pg_dump` script to cron
- **Suggested prompt:**
  > Set up a Cloudflare Tunnel from the local Docker backend to Cloudflare, routed through the catan.mightyeaption.in subdomain, with TLS handled automatically. Move all secrets to a gitignored .env file. Wire the existing pg_dump backup script into a daily cron job, syncing dumps to [chosen off-disk location].

### Day 28 — Auth Hardening + Security Review
- **Focus:** Access control before going live
- **Model:** Opus
- **Effort:** Medium
- **Tasks:**
  - Rate limiting on auth endpoints
  - Cloudflare Access or shared-passphrase gate on the subdomain
  - Review exposed ports/services
- **Suggested prompt:**
  > Review the auth flow for basic security gaps: add rate limiting to login/signup endpoints, confirm passwords are never logged, and set up Cloudflare Access (or a fallback shared-passphrase gate) restricting the subdomain to your friend group. Audit docker-compose.yml to confirm no unnecessary ports are exposed to the host network.

### Day 29 — Final Live Playtest
- **Focus:** Real deployed game with friends
- **Model:** Sonnet (Opus for live-fire bug fixes)
- **Effort:** Medium
- **Tasks:**
  - Full game over the real deployed URL, all friends connecting remotely
  - Bug triage
- **Suggested prompt:**
  > [Session-driven — fix bugs found during the live deployed playtest over the internet, not LAN.]

### Day 30 — Buffer, Bug Fixes, Wrap-Up
- **Focus:** Final polish, documentation
- **Model:** Sonnet
- **Effort:** Low–Medium
- **Tasks:**
  - Fix remaining bugs from Day 29
  - Update `decisions.md`/`CLAUDE.md` to reflect final state
  - Write a short README for future-you (how to start server, restore backup, etc.)
- **Suggested prompt:**
  > Fix remaining bugs from the Day 29 playtest. Write a README covering: how to start the full stack, how to restore a Postgres backup, and where the tunnel/DNS config lives, so this is maintainable months from now without re-reading the whole codebase.

---

## Reference: Core DB Schema
```sql
users (
  id, username UNIQUE, password_hash, created_at
)

games (
  id, started_at, ended_at, winner_id, player_count, board_size
)

game_players (
  game_id, user_id, final_score, placement
)
```

## Tooling Checkpoints
- **Day 1:** `CLAUDE.md` + `decisions.md` in repo root
- **Day 14:** Install Graphify (post-commit hook triggers `graphify update`) and claude-mem
- **Ongoing:** one commit/day minimum, tagged `Day N: <summary> (CTN001)`
