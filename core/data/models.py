from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class Position(str, Enum):
    GKP = "GKP"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"

class Player(BaseModel):
    player_id: int
    first_name: str
    second_name: str
    web_name: str
    team_id: int
    position: Position
    current_price: float  # e.g. 12.5
    selected_by_pct: float
    can_select: bool = True
    status: str = "a"  # 'a'=available, 'd'=doubtful, 'i'=injured, 's'=suspended, 'u'=unavailable
    chance_of_playing_next_round: Optional[int] = 100
    news: Optional[str] = ""
    minutes: int = 0
    starts: int = 0
    form: float = 0.0
    ep_next: float = 0.0
    points_per_game: float = 0.0
    total_points: int = 0
    goals_scored: int = 0
    assists: int = 0
    clean_sheets: int = 0
    saves: int = 0
    bonus: int = 0
    expected_goals: float = 0.0
    expected_assists: float = 0.0
    expected_goal_involvements: float = 0.0
    expected_goals_conceded: float = 0.0
    influence: float = 0.0
    creativity: float = 0.0
    threat: float = 0.0
    ict_index: float = 0.0

class Team(BaseModel):
    team_id: int
    name: str
    short_name: str
    strength_attack_home: float = 1.0
    strength_attack_away: float = 1.0
    strength_defence_home: float = 1.0
    strength_defence_away: float = 1.0

class Fixture(BaseModel):
    fixture_id: int
    gameweek: int
    home_team_id: int
    away_team_id: int
    kickoff_time: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    finished: bool = False
    difficulty_home: int = 3
    difficulty_away: int = 3

class Gameweek(BaseModel):
    gameweek: int
    deadline_time: str
    finished: bool = False
    is_current: bool = False
    is_next: bool = False

class PlayerGameweek(BaseModel):
    player_id: int
    gameweek: int
    minutes: int = 0
    starts: int = 0
    fpl_points: int = 0
    goals: int = 0
    assists: int = 0
    clean_sheets: int = 0
    saves: int = 0
    bonus: int = 0
    bps: int = 0
    xg: float = 0.0
    xa: float = 0.0
    xgi: float = 0.0

class Availability(BaseModel):
    player_id: int
    as_of_timestamp: str
    status: str = "a"
    chance_start: float = 1.0
    chance_appearance: float = 1.0
    p_start: float = 1.0
    p_sub: float = 0.0
    minutes_if_start: float = 85.0
    minutes_if_sub: float = 20.0
    expected_minutes: float = 85.0
    expected_return: Optional[str] = None
    source: str = "official_fpl"
    confidence: float = 1.0
    snapshot_id: Optional[str] = None
    model_version: str = "1.0.0"

class OwnershipSnapshot(BaseModel):
    player_id: int
    gameweek: int
    as_of_timestamp: str
    global_ownership: float
    elite_ownership: Optional[float] = None
    mini_league_eo: Optional[float] = None
    captain_pct: Optional[float] = None

class PriceSnapshot(BaseModel):
    player_id: int
    timestamp: str
    price: float
    transfers_in: int = 0
    transfers_out: int = 0
    net_transfers: int = 0
    price_change_probability: Optional[float] = 0.0

class SquadPlayer(BaseModel):
    player_id: int
    position: Position
    purchase_price: float
    selling_price: float
    starting: bool
    captain: bool = False
    vice_captain: bool = False
    multiplier: int = 1  # 0=bench, 1=starter, 2=captain, 3=triple captain

class ManagerState(BaseModel):
    manager_id: int
    manager_name: str = "FPL Manager"
    team_name: str = "Edge Squad"
    gameweek: int
    bank: float = 0.5  # in £m
    free_transfers: int = 1
    free_transfers_confirmed: bool = False
    overall_points: int = 0
    overall_rank: int = 100000
    squad: List[SquadPlayer]
    chips_used: List[str] = []
    snapshot_id: Optional[str] = None

class Projection(BaseModel):
    player_id: int
    gameweek: int
    model_version: str = "1.0.0"
    as_of_timestamp: str
    snapshot_id: Optional[str] = None
    xmins: float
    start_probability: float
    mean_xp: float
    p10_xp: float
    p50_xp: float
    p90_xp: float
    goal_xp: float = 0.0
    assist_xp: float = 0.0
    clean_sheet_xp: float = 0.0
    save_xp: float = 0.0
    bonus_xp: float = 0.0
    fixtures_count: int = 1
    fixture_ids: List[int] = []

class Snapshot(BaseModel):
    snapshot_id: str
    season: str = "2024/25"
    gameweek: int = 1
    as_of_timestamp: str
    source: str = "official_fpl"
    data_mode: str = "live"
    validated: bool = False
    players: int = 0
    teams: int = 0
    fixtures: int = 0
    current_deadline: Optional[str] = None
    last_successful_refresh: Optional[str] = None

class DataStatus(BaseModel):
    provider_name: str
    connected: bool
    last_updated: str
    details: str

class LiveDataStatus(BaseModel):
    season: str
    gameweek: int
    source: str
    data_mode: str
    snapshot_id: str
    as_of_timestamp: str
    players: int
    teams: int
    fixtures: int
    validated: bool
    current_deadline: Optional[str] = None
    last_successful_refresh: Optional[str] = None
    projection_snapshot_status: str = "ready"
    manager_state_available: bool = False
