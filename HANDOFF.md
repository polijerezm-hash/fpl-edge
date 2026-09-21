# FPL Edge — Agent Handoff Document

## Project Overview
**FPL Edge** is an enterprise-grade Fantasy Premier League (FPL) analytics and AI decision-support web application.

- **Working Product Name**: FPL Edge (Configurable branding & logo)
- **Architecture**: Decoupled 7-layer architecture (Data -> Availability -> Projection -> Optimizer -> Strategy -> Explanation -> Web Interface).
- **Core Architectural Principle**: The LLM is NOT the decision engine. Recommendations are generated deterministically by a PuLP Mixed Integer Linear Programming (MILP) solver and component xP / xMinutes models. The LLM strictly explains an immutable `DECISION_CONTEXT` payload.

---

## Current Implementation State (Phases 1–10 COMPLETE)

### 1. Live Data Ingestion & Governance (`core/data/`)
- **`core/data/errors.py`**: Production structured errors (`LiveDataUnavailableError`, `LiveDataInvalidError`, `InvalidTeamIdError`, `CurrentSquadInvalidError`, `StaleSnapshotError`, `OptimisationFailedError`, `RecommendationValidationFailedError`).
- **`core/data/models.py`**: Pydantic schemas including `Snapshot`, `LiveDataStatus`, `Player`, `Team`, `Fixture`, `Gameweek`, `Availability`, `Projection`, `ManagerState`, `SquadPlayer`.
- **`core/data/providers.py`**:
  - `FplOfficialProvider`: Pulls live official FPL API (`bootstrap-static/`, `fixtures/`, `entry/{id}/`, `entry/{id}/event/{gw}/picks/`). **Zero silent fallbacks** — network or schema errors strictly raise `LiveDataUnavailableError` or `LiveDataInvalidError`.
  - `DemoProvider`: Offline seed dataset clearly isolated for testing and deterministic evaluation.
- **`core/data/repository.py`**:
  - `DataRepository(data_mode="live")` defaults to strict live official FPL data. Demo mode requires explicit opt-in (`data_mode="demo"`).
  - Snapshot promote/rollback semantics: candidate snapshots are validated through `LiveDataValidator.validate_snapshot_integrity` before promotion.
  - Snapshot tracking: `snapshot_id`, `season`, `gameweek`, `as_of_timestamp`, `source`, `data_mode`, `validated`, player/team/fixture counts.
- **`core/data/validators.py`**:
  - `validate_snapshot_integrity`: Confirms player counts (>400 in live), 20 Premier League teams, valid IDs and prices.
  - `validate_squad_against_snapshot`: Validates imported manager squad (15 players, valid positions, 11 starters, 1 GKP, 3-5 DEF, 2-5 MID, 1-3 FWD, max 3 per club, exactly 1 captain & 1 vice captain).
  - `validate_optimiser_plan`: Post-solve validation of every generated transfer plan (transfers in exist in snapshot, transfers out exist in squad, formation rules, max 3 per club, bank balance non-negative).

### 2. Availability & Double Gameweek (DGW) Projections (`core/availability/`, `core/projections/`)
- **`core/availability/engine.py`**: Expected minutes $E(\text{minutes})$, start probability $P(\text{start})$, substitute probability $P(\text{sub})$, normalized via team-level starting probability reconciliation ($\sum P(\text{start}) = 11.0$).
- **`core/projections/engine.py`**:
  - Full support for **Blank Gameweeks (0 fixtures)**, **Single Gameweeks (1 fixture)**, and **Double/Triple Gameweeks ($\ge 2$ fixtures)** via `team_fixtures_map[team_id] = [fixture_1, fixture_2, ...]`.
  - Aggregates component xP (goals, assists, clean sheets, saves, bonus, appearance) across all fixtures in a gameweek without dropping matches.
  - Multi-fixture variance accumulation: $\sigma_{\text{compound}} = \sqrt{\sum \sigma_i^2}$ for robust Monte Carlo percentiles ($P10, P50, P90$).

### 3. MILP Transfer Optimizer (`core/optimizer/solver.py`)
- PuLP MILP solver optimizing 1, 3, or 5 Gameweek planning horizons.
- Candidate pre-filtering for solvers with >130 players to guarantee < 2s solve time.
- Supports manual confirmation/override of rolling Free Transfers (1 to 5 FT).
- Returns Top 5 feasible plans (Plans A, B, C, D, E) and evaluates HOLD / Roll Transfer as a baseline.
- All plans validated post-solve through `LiveDataValidator.validate_optimiser_plan`.

### 4. Strategy & Grounded Explanation (`core/strategy/`, `core/explanation/`)
- Captaincy engine: Shield (safe), Diamond (balanced), Sword (differential) profiles.
- Chip strategy analyzer: Wildcard, Free Hit, Bench Boost, Triple Captain.
- Grounded Explainer: Builds standardized `DECISION_CONTEXT` payload; deterministic template explainer or optional OpenAI LLM.

### 5. FastAPI Backend (`services/api/main.py`)
- Endpoints:
  - `GET /`: Health check and active snapshot metadata.
  - `GET /api/data/status`: Full `LiveDataStatus` report.
  - `POST /api/data/refresh`: Controlled snapshot refresh and validation.
  - `GET /api/gameweeks`, `GET /api/fixtures`, `GET /api/teams`, `GET /api/players`, `GET /api/players/{id}`.
  - `GET /api/team/{id}`: Live manager squad import with validation against active snapshot.
  - `GET /api/projections`: Gameweek projections with DGW aggregation.
  - `POST /api/optimise`: Solver endpoint with mandatory Free Transfers confirmation gate.
  - `POST /api/captaincy`, `POST /api/chips/analyse`, `POST /api/assistant`, `GET /api/evaluation`.

### 6. Frontend Web Application (`apps/web/`)
- **Architecture**: Vite + React with Tailwind CSS (all legacy Next.js files purged).
- **`apps/web/src/app/page.tsx`**: Dynamic gameweek resolution, `data_mode` propagation (`?mode=demo` query param support), live status monitoring, error banners (`LIVE_DATA_UNAVAILABLE`).
- **`apps/web/src/components/Header.tsx`**: Team import form, interactive Free Transfers confirmation input (prefilled as unconfirmed, blocking optimization until confirmed), live deadline countdown, demo toggle, snapshot refresh trigger.
- **`apps/web/src/components/DataStatusBanner.tsx`**: Live snapshot badge (`LIVE • Official FPL • GW X • Updated X min ago`) or prominent `DEMO DATA` warning banner.
- **`apps/web/src/components/OverviewDashboard.tsx`**: Completely purged of hardcoded mock players ("Salah", "Haaland", "Foden"). Dynamic squad availability watchlist, dynamic captain picks, and **Recommendation Provenance & Audit Trail** section.

---

## How to Run the Application

### 1. Backend API (FastAPI)
```bash
cd /Users/miguelpolijerez/.gemini/antigravity/scratch/fpl-edge
source /Users/miguelpolijerez/.gemini/antigravity/scratch/venv/bin/activate
uvicorn services.api.main:app --port 8000 --reload
```

### 2. Frontend Application (Vite + React)
```bash
cd /Users/miguelpolijerez/.gemini/antigravity/scratch/fpl-edge/apps/web
npm run dev
# App available at http://localhost:3000
# To open directly in demo mode: http://localhost:3000/?mode=demo
```

### 3. Run Automated Unit & Regression Tests (21 Passing Tests)
```bash
cd /Users/miguelpolijerez/.gemini/antigravity/scratch/fpl-edge
PYTHONPATH=. /Users/miguelpolijerez/.gemini/antigravity/scratch/venv/bin/pytest tests/ -v
```

### 4. Run Live Production Smoke Test
```bash
cd /Users/miguelpolijerez/.gemini/antigravity/scratch/fpl-edge
PYTHONPATH=. /Users/miguelpolijerez/.gemini/antigravity/scratch/venv/bin/python scripts/live_smoke_test.py --team-id 1
```

---

## Verification Summary
- **Unit Test Suite**: 21 / 21 tests passing in 2.67s.
  - `tests/test_data_isolation.py`: Verified zero silent fallback; demo sentinel rejected in live mode; snapshot isolation confirmed.
  - `tests/test_validation.py`: Verified snapshot integrity, squad composition, and optimizer plan validation gates.
  - `tests/test_dgw_projections.py`: Verified multi-fixture accumulation and BGW zeroing.
  - `tests/test_api_endpoints.py`: Verified `/api/data/status`, FT confirmation requirement, demo mode execution.
  - `tests/test_availability.py`, `tests/test_fpl_rules.py`, `tests/test_optimizer.py`, `tests/test_projections.py`.
- **Live Smoke Test**: Passed end-to-end with Official FPL Team ID 1 (Chris Musson, Solio Moose) in 1.29s. All 15 squad members validated against active 659-element live snapshot.
- **Frontend Build**: `npm run build` succeeds cleanly in 1.33s.
