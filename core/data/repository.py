import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.data.models import (
    Player, Team, Fixture, Gameweek, ManagerState, DataStatus, LiveDataStatus, Snapshot
)
from core.data.providers import DataProvider, DemoProvider, FplOfficialProvider
from core.data.validators import LiveDataValidator
from core.data.errors import (
    LiveDataUnavailableError, LiveDataInvalidError, StaleSnapshotError, CurrentSquadInvalidError
)

class DataRepository:
    """
    Strict repository managing immutable data snapshots.
    Guarantees that all queries operate strictly on a validated snapshot.
    Live and Demo modes are logically and physically isolated.
    """

    def __init__(self, data_mode: str = "live", provider: Optional[DataProvider] = None):
        self.data_mode = data_mode.lower()
        if provider:
            self.provider = provider
        elif self.data_mode == "demo":
            self.provider = DemoProvider()
        else:
            self.provider = FplOfficialProvider()

        self._snapshot_timestamp: str = datetime.utcnow().isoformat() + "Z"
        self._current_snapshot: Optional[Snapshot] = None
        self._last_successful_refresh: Optional[str] = None

        # In-memory snapshot cache
        self._players_cache: Optional[List[Player]] = None
        self._teams_cache: Optional[List[Team]] = None
        self._fixtures_cache: Optional[List[Fixture]] = None
        self._gameweeks_cache: Optional[List[Gameweek]] = None
        self._custom_manager_states: Dict[int, ManagerState] = {}

    @property
    def current_snapshot(self) -> Snapshot:
        if not self._current_snapshot:
            self.refresh_snapshots()
        return self._current_snapshot

    def refresh_snapshots(self) -> Snapshot:
        """
        Controlled snapshot refresh.
        Retrieves fresh data, validates all entities, and only promotes to active
        if validation succeeds. If validation fails, preserves the previous snapshot.
        """
        now_str = datetime.utcnow().isoformat() + "Z"
        
        # 1. Fetch fresh candidate data from provider
        candidate_players = self.provider.get_players()
        candidate_teams = self.provider.get_teams()
        candidate_fixtures = self.provider.get_fixtures()
        candidate_gameweeks = self.provider.get_gameweeks()

        # 2. Run validation gate
        is_valid, errors = LiveDataValidator.validate_snapshot_integrity(
            candidate_players, candidate_teams, candidate_fixtures, candidate_gameweeks,
            data_mode=self.data_mode
        )
        if not is_valid:
            raise LiveDataInvalidError(
                f"Candidate snapshot failed validation gate: {'; '.join(errors[:5])}",
                details={"errors": errors}
            )

        # 3. Determine the decision gameweek. Once a deadline has passed, FPL's
        # `is_current` event is the live/just-finished round; recommendations must
        # target `is_next` instead.
        active_gw = 1
        current_deadline = None
        for g in candidate_gameweeks:
            if g.is_next:
                active_gw = g.gameweek
                current_deadline = g.deadline_time
                break
        if not current_deadline:
            for g in candidate_gameweeks:
                if g.is_current:
                    active_gw = g.gameweek
                    current_deadline = g.deadline_time
                    break

        snap_id = f"snap_{int(time.time())}_{self.data_mode}_gw{active_gw}"
        season_start = now_str[:4]
        current_month = int(now_str[5:7])
        start_year = int(season_start) if current_month >= 7 else int(season_start) - 1
        season_name = f"{start_year}/{str(start_year + 1)[-2:]}"
        if self.data_mode == "demo":
            season_name += " (Demo)"

        new_snapshot = Snapshot(
            snapshot_id=snap_id,
            season=season_name,
            gameweek=active_gw,
            as_of_timestamp=now_str,
            source="official_fpl" if self.data_mode == "live" else "demo_seed",
            data_mode=self.data_mode,
            validated=True,
            players=len(candidate_players),
            teams=len(candidate_teams),
            fixtures=len(candidate_fixtures),
            current_deadline=current_deadline,
            last_successful_refresh=now_str
        )

        # 4. Atomically promote
        self._players_cache = candidate_players
        self._teams_cache = candidate_teams
        self._fixtures_cache = candidate_fixtures
        self._gameweeks_cache = candidate_gameweeks
        self._snapshot_timestamp = now_str
        self._last_successful_refresh = now_str
        self._current_snapshot = new_snapshot

        return new_snapshot

    def get_as_of_timestamp(self) -> str:
        return self._snapshot_timestamp

    def get_snapshot_id(self) -> str:
        return self.current_snapshot.snapshot_id

    def get_players(self) -> List[Player]:
        if not self._players_cache:
            self.refresh_snapshots()
        return self._players_cache

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        for p in self.get_players():
            if p.player_id == player_id:
                return p
        return None

    def get_teams(self) -> List[Team]:
        if not self._teams_cache:
            self.refresh_snapshots()
        return self._teams_cache

    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        for t in self.get_teams():
            if t.team_id == team_id:
                return t
        return None

    def get_fixtures(self) -> List[Fixture]:
        if not self._fixtures_cache:
            self.refresh_snapshots()
        return self._fixtures_cache

    def get_gameweeks(self) -> List[Gameweek]:
        if not self._gameweeks_cache:
            self.refresh_snapshots()
        return self._gameweeks_cache

    def get_current_gameweek(self) -> int:
        return self.current_snapshot.gameweek

    def get_manager_state(self, manager_id: int) -> ManagerState:
        if manager_id in self._custom_manager_states:
            state = self._custom_manager_states[manager_id]
            # Ensure custom state attaches active snapshot ID
            state.snapshot_id = self.current_snapshot.snapshot_id
            return state

        # Fetch from provider
        manager_state = self.provider.get_manager_state(manager_id)
        manager_state.snapshot_id = self.current_snapshot.snapshot_id

        # Validate imported squad against active snapshot
        players_dict = {p.player_id: p for p in self.get_players()}
        is_valid, errors = LiveDataValidator.validate_squad_against_snapshot(
            manager_state.squad, players_dict, data_mode=self.data_mode
        )
        if not is_valid:
            raise CurrentSquadInvalidError(
                f"Imported squad for manager {manager_id} failed snapshot validation: {'; '.join(errors[:3])}",
                details={"errors": errors}
            )

        return manager_state

    def get_manager_leagues(self, manager_id: int) -> List[Dict[str, Any]]:
        return self.provider.get_manager_leagues(manager_id)

    def get_mini_league_analysis(self, manager_id: int, league_id: int) -> Dict[str, Any]:
        return self.provider.get_mini_league_analysis(
            manager_id=manager_id,
            league_id=league_id,
            gameweek=self.get_current_gameweek(),
            players=self.get_players(),
        )

    def save_custom_manager_state(self, manager_state: ManagerState):
        manager_state.snapshot_id = self.current_snapshot.snapshot_id
        self._custom_manager_states[manager_state.manager_id] = manager_state

    def get_live_status(self) -> LiveDataStatus:
        snap = self.current_snapshot
        return LiveDataStatus(
            season=snap.season,
            gameweek=snap.gameweek,
            source=snap.source,
            data_mode=snap.data_mode,
            snapshot_id=snap.snapshot_id,
            as_of_timestamp=snap.as_of_timestamp,
            players=snap.players,
            teams=snap.teams,
            fixtures=snap.fixtures,
            validated=snap.validated,
            current_deadline=snap.current_deadline,
            last_successful_refresh=self._last_successful_refresh,
            projection_snapshot_status="ready" if snap.validated else "pending",
            manager_state_available=len(self._custom_manager_states) > 0
        )

    def get_status(self) -> List[DataStatus]:
        return [self.provider.get_status()]
