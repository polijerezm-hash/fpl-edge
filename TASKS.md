# FPL Edge - Development Tasks & Implementation Checklist

- [x] **Phase 1: Foundation & Monorepo Setup**
  - [x] Create directory hierarchy (`core/`, `services/`, `apps/`, `config/`, `tests/`)
  - [x] Configure Python environment & dependencies (`FastAPI`, `PuLP`, `Pandas`, `DuckDB`, `Pydantic`)
  - [x] Write project documentation (`README.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, `MODEL_CARD.md`, `API.md`)
  - [x] Write configuration (`config/season_rules.yaml`)

- [x] **Phase 2: Data Engine & Data Providers**
  - [x] Implement `DataProvider` interface
  - [x] Implement `FplOfficialProvider` (handles FPL API endpoints with error handling/timeouts)
  - [x] Implement `DemoProvider` (realistic seed dataset for offline/demo execution)
  - [x] Implement snapshotting mechanism with `as_of_timestamp` tracking
  - [x] Implement DuckDB/SQLite database schemas and repositories

- [x] **Phase 3: Availability & Projection Engine**
  - [x] Implement `AvailabilityEngine` (xMinutes, P(start), P(sub), team-level reconciliation)
  - [x] Implement `ProjectionEngine` (component expected points: goals, assists, clean sheets, saves, bonus)
  - [x] Implement configurable FPL scoring rule engine
  - [x] Implement basic Monte Carlo distribution calculator (mean, P10, P50, P90)

- [x] **Phase 4: Optimization Engine (MILP Solver)**
  - [x] Implement PuLP MILP optimization model for 1, 3, and 5 GW planning horizons
  - [x] Enforce strict FPL constraints (squad composition, 3 per club, budget, XI rules, captaincy)
  - [x] Support free transfer rollover, hits (-4 per extra move), selling price calculations
  - [x] Evaluate HOLD / Roll Transfer as a genuine option
  - [x] Return Top 5 feasible plans sorted by expected utility with trade-off details
  - [x] Implement sensitivity/robustness analysis & player lock/ban overrides

- [x] **Phase 5: Strategy Engine & Grounded AI Assistant**
  - [x] Implement risk profiles (Safe/Protect, Balanced, Aggressive/Chase)
  - [x] Implement Effective Ownership (EO) tracker and league exposure calculations
  - [x] Implement Chip Strategy Analyzer (Wildcard, Free Hit, Bench Boost, Triple Captain)
  - [x] Implement Captaincy Engine (Shield, Diamond, Sword profiles)
  - [x] Implement grounded AI engine: deterministic `DECISION_CONTEXT` builder + LLM provider adapter & template fallback

- [x] **Phase 6: Evaluation Infrastructure**
  - [x] Implement historical backtesting framework (MAE by position, start accuracy, captain efficiency, regret)
  - [x] Build evaluation run repository

- [x] **Phase 7: FastAPI Backend Services**
  - [x] Implement `/api/players`, `/api/fixtures`, `/api/gameweeks`
  - [x] Implement `/api/team/{manager_id}` & squad import
  - [x] Implement `/api/projections` & `/api/availability`
  - [x] Implement `/api/optimise`
  - [x] Implement `/api/captaincy` & `/api/chips/analyse`
  - [x] Implement `/api/assistant`
  - [x] Implement `/api/evaluation` & `/api/data/status`

- [x] **Phase 8: Web Interface (Vite + React)**
  - [x] Build Vite + React application with Tailwind CSS & custom dark sports-analytics theme
  - [x] Landing page with FPL Team ID import & Demo Mode toggle
  - [x] Overview Dashboard with deadline countdown, recommendation hero card, captain picks, watchlist
  - [x] My Team page with interactive football pitch visual & player side panels
  - [x] Transfer Planner page with horizon (1/3/5 GW), risk modes, Top 5 plans, plan comparison, locks/bans
  - [x] Captaincy page (Shield / Diamond / Sword) & distribution chart
  - [x] Player Explorer with sorting, filtering, and component breakdown
  - [x] Fixture Planner matrix with heatmap difficulty & swings
  - [x] Chip Strategy timeline & recommendations
  - [x] Mini-League exposure analyzer
  - [x] Model Accuracy dashboard with empirical performance metrics
  - [x] AI Assistant drawer / modal with context-grounded Q&A

- [x] **Phase 9: Testing & Verification**
  - [x] Write unit tests for FPL squad/transfer rules
  - [x] Write unit tests for xMinutes team reconciliation
  - [x] Write unit tests for component xP calculation
  - [x] Write unit tests for MILP solver (validity, top 5 plans, budget enforcement)
  - [x] Write unit tests for grounded AI context generator

- [x] **Phase 10: Live Data Production Iteration & Defect Resolution**
  - [x] Root cause obsolete-player defect identified & fixed (DataRepository defaulted to DemoProvider + silent fallback)
  - [x] Removed ALL silent live->demo fallbacks in `FplOfficialProvider`; raise structured `LiveDataUnavailableError`
  - [x] Added `core/data/errors.py` with structured production error types
  - [x] Added `core/data/validators.py` (snapshot integrity, squad validation, optimizer plan validation gate)
  - [x] Added immutable `Snapshot` governance with `snapshot_id`, `season`, `gameweek`, `as_of_timestamp`
  - [x] Implemented proper Double Gameweek (DGW) multi-fixture accumulation in `ProjectionEngine`
  - [x] Upgraded `/api/data/status` to return complete live snapshot metadata
  - [x] Added `POST /api/data/refresh` endpoint
  - [x] Implemented mandatory Free Transfers confirmation gate before running MILP optimizer
  - [x] Candidate-filtered MILP solver (< 2s execution across all horizons)
  - [x] Resolved frontend architecture: confirmed Vite + React; removed all dead Next.js files
  - [x] Removed all hardcoded mock player names/stats from `OverviewDashboard.tsx`
  - [x] Added Recommendation Provenance & Audit Trail section to UI
  - [x] Rewrote `Header.tsx` and `page.tsx` for end-to-end `data_mode` propagation and FT confirmation
  - [x] Expanded test suite to 21 passing unit tests (`tests/`)
- [x] Created `scripts/live_smoke_test.py` passing 100% with real FPL data

- [x] **Phase 11: Recommendation Quality & Product Rework**
  - [x] Rebuilt expected-minutes model with exclusive goalkeeper roles and club-level reconciliation
  - [x] Added sample-size shrinkage and distribution-aware expected-points projections
  - [x] Added hard captain and transfer eligibility gates for unavailable/non-playing players
  - [x] Added saved-transfer value, minimum action edge, weighted bench value, and anti-churn constraints
  - [x] Unified planner and explanation context so chat cannot independently re-plan
  - [x] Corrected live decision target to the upcoming gameweek and dynamic season metadata
  - [x] Added live mini-league listings, standings, effective ownership, differentials, and threats
  - [x] Rebranded the interface with the FPL Edge mark and a restrained matchday-analysis visual system
  - [x] Expanded the regression suite to 25 passing tests
