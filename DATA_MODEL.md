# FPL Edge — Data Model Documentation

The database schema is structured around explicit time-stamped entities and immutable historical snapshots.

## Core Models

### `players`
- `player_id` (Integer, Primary Key)
- `first_name` (String)
- `second_name` (String)
- `web_name` (String)
- `team_id` (Integer, Foreign Key -> teams.team_id)
- `position` (Enum: GKP, DEF, MID, FWD)
- `current_price` (Float - in £m, e.g., 12.5)
- `selected_by_pct` (Float)
- `status` (String: a, d, i, s, u)

### `teams`
- `team_id` (Integer, Primary Key)
- `name` (String)
- `short_name` (String)
- `strength_attack_home` (Float)
- `strength_attack_away` (Float)
- `strength_defence_home` (Float)
- `strength_defence_away` (Float)

### `fixtures`
- `fixture_id` (Integer, Primary Key)
- `gameweek` (Integer)
- `home_team_id` (Integer)
- `away_team_id` (Integer)
- `kickoff_time` (String / ISO Timestamp)
- `home_score` (Integer, Optional)
- `away_score` (Integer, Optional)
- `finished` (Boolean)

### `gameweeks`
- `gameweek` (Integer, Primary Key)
- `deadline_time` (String / ISO Timestamp)
- `finished` (Boolean)

### `player_gameweek`
- `player_id` (Integer)
- `gameweek` (Integer)
- `minutes` (Integer)
- `starts` (Integer)
- `fpl_points` (Integer)
- `goals` (Integer)
- `assists` (Integer)
- `clean_sheets` (Integer)
- `saves` (Integer)
- `bonus` (Integer)
- `bps` (Integer)
- `xg` (Float, Optional)
- `xa` (Float, Optional)
- `xgi` (Float, Optional)

### `availability`
- `player_id` (Integer)
- `as_of_timestamp` (String)
- `status` (String)
- `chance_start` (Float, 0.0 - 1.0)
- `chance_appearance` (Float, 0.0 - 1.0)
- `expected_return` (String, Optional)
- `source` (String)
- `confidence` (Float)

### `projections`
- `player_id` (Integer)
- `gameweek` (Integer)
- `model_version` (String)
- `as_of_timestamp` (String)
- `xmins` (Float)
- `start_probability` (Float)
- `mean_xp` (Float)
- `p10_xp` (Float)
- `p50_xp` (Float)
- `p90_xp` (Float)
- `goal_xp` (Float)
- `assist_xp` (Float)
- `clean_sheet_xp` (Float)
- `save_xp` (Float)
- `bonus_xp` (Float)

### `manager_state` & `squad_snapshot`
- Tracks user budget, free transfers, bank, overall rank, purchase prices, selling prices, starting XI, captain, and vice captain.
