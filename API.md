# FPL Edge — API Specification

The REST API is implemented in FastAPI and exposes clean, typed JSON contracts.

## Endpoints

### 1. Data & Status
- `GET /api/data/status`: Returns provider connectivity, snapshot timestamps, and source freshness.
- `GET /api/gameweeks`: Returns list of all gameweeks and deadline timestamps.
- `GET /api/fixtures`: Returns upcoming fixtures with opponent strength ratings.

### 2. Players & Projections
- `GET /api/players`: Searchable, filterable list of players with current prices, form, and team IDs.
- `GET /api/players/{id}`: Detailed player profile with component xP breakdown and fixture forecasts.
- `GET /api/projections?gw=5`: Projections for all players for target gameweek.

### 3. Manager & Squad
- `GET /api/team/{manager_id}`: Import squad, bank, free transfers, and rank for a given FPL Manager ID.

### 4. Planning & Optimization
- `POST /api/optimise`: Runs MILP solver.
  - Body: `{ manager_id, horizon: 1|3|5, risk_profile: "safe"|"balanced"|"aggressive", locked_players, banned_players, custom_overrides }`
  - Returns: `{ baseline_xp, plans: [ Top 5 Feasible Plans with Transfer Sequence, Bank, FT state, xP Gain vs HOLD ] }`

### 5. Strategy & Captaincy
- `POST /api/captaincy`: Returns Shield, Diamond, and Sword captain candidates with floor/ceiling distribution statistics.
- `POST /api/chips/analyse`: Evaluates candidate gameweeks for Wildcard, Free Hit, Bench Boost, and Triple Captain.

### 6. AI Assistant
- `POST /api/assistant`: Grounded Q&A engine using deterministic `DECISION_CONTEXT`.
- `GET /api/evaluation`: Model performance, MAE by position, start accuracy, and captain efficiency metrics.
