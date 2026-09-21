import time
import requests
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from core.data.models import (
    Player, Team, Fixture, Gameweek, ManagerState, SquadPlayer, Position, DataStatus
)
from core.data.errors import (
    LiveDataUnavailableError, LiveDataInvalidError, InvalidTeamIdError, CurrentSquadInvalidError
)
from data.demo.seed_data import (
    DEMO_PLAYERS, DEMO_TEAMS, DEMO_FIXTURES, DEMO_GAMEWEEKS, DEMO_MANAGER_SQUAD
)

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (FPL-Edge/1.0)"

class DataProvider(ABC):
    data_mode: str = "base"

    @abstractmethod
    def get_players(self) -> List[Player]:
        pass

    @abstractmethod
    def get_teams(self) -> List[Team]:
        pass

    @abstractmethod
    def get_fixtures(self) -> List[Fixture]:
        pass

    @abstractmethod
    def get_gameweeks(self) -> List[Gameweek]:
        pass

    @abstractmethod
    def get_manager_state(self, manager_id: int) -> ManagerState:
        pass

    @abstractmethod
    def get_status(self) -> DataStatus:
        pass


class DemoProvider(DataProvider):
    data_mode: str = "demo"

    def __init__(self):
        self._timestamp = datetime.utcnow().isoformat() + "Z"

    def get_players(self) -> List[Player]:
        return [p.model_copy() for p in DEMO_PLAYERS]

    def get_teams(self) -> List[Team]:
        return [t.model_copy() for t in DEMO_TEAMS]

    def get_fixtures(self) -> List[Fixture]:
        return [f.model_copy() for f in DEMO_FIXTURES]

    def get_gameweeks(self) -> List[Gameweek]:
        return [g.model_copy() for g in DEMO_GAMEWEEKS]

    def get_manager_state(self, manager_id: int) -> ManagerState:
        squad = DEMO_MANAGER_SQUAD.model_copy(deep=True)
        squad.manager_id = manager_id
        squad.free_transfers_confirmed = True
        return squad

    def get_status(self) -> DataStatus:
        return DataStatus(
            provider_name="Demo Data Provider (Offline Seed)",
            connected=True,
            last_updated=self._timestamp,
            details="Operational offline seed dataset for testing and evaluation."
        )


class FplOfficialProvider(DataProvider):
    data_mode: str = "live"
    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._bootstrap_cache: Optional[Dict[str, Any]] = None
        self._last_fetch: float = 0
        self._status = DataStatus(
            provider_name="Official FPL API",
            connected=False,
            last_updated=datetime.utcnow().isoformat() + "Z",
            details="Not initialized"
        )

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json"
        }

    def _fetch_bootstrap(self, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force and self._bootstrap_cache and (now - self._last_fetch < 180):
            return self._bootstrap_cache

        try:
            resp = requests.get(
                f"{self.BASE_URL}/bootstrap-static/",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                if "elements" not in data or "teams" not in data or "events" not in data:
                    raise LiveDataInvalidError("bootstrap-static JSON missing required keys ('elements', 'teams', 'events')")
                self._bootstrap_cache = data
                self._last_fetch = now
                self._status = DataStatus(
                    provider_name="Official FPL API",
                    connected=True,
                    last_updated=datetime.utcnow().isoformat() + "Z",
                    details="Live bootstrap-static fetched successfully."
                )
                return self._bootstrap_cache
            else:
                self._status = DataStatus(
                    provider_name="Official FPL API",
                    connected=False,
                    last_updated=datetime.utcnow().isoformat() + "Z",
                    details=f"HTTP {resp.status_code} from FPL bootstrap-static"
                )
                raise LiveDataUnavailableError(
                    f"Official FPL API returned HTTP {resp.status_code} on bootstrap-static",
                    details={"status_code": resp.status_code}
                )
        except (requests.RequestException, ValueError) as e:
            self._status = DataStatus(
                provider_name="Official FPL API",
                connected=False,
                last_updated=datetime.utcnow().isoformat() + "Z",
                details=f"Connection failed: {str(e)}"
            )
            raise LiveDataUnavailableError(
                f"Failed to connect to official FPL API: {str(e)}",
                details={"error": str(e)}
            )

    def get_players(self) -> List[Player]:
        data = self._fetch_bootstrap()
        elements = data.get("elements", [])
        if not elements:
            raise LiveDataUnavailableError("No players found in official FPL API response")

        pos_map = {1: Position.GKP, 2: Position.DEF, 3: Position.MID, 4: Position.FWD}
        players = []
        for el in elements:
            try:
                raw_pct = el.get("selected_by_percent", "0.0")
                sel_pct = float(raw_pct) if raw_pct is not None else 0.0
            except (ValueError, TypeError):
                sel_pct = 0.0

            players.append(Player(
                player_id=el["id"],
                first_name=el.get("first_name", ""),
                second_name=el.get("second_name", ""),
                web_name=el.get("web_name", "Unknown"),
                team_id=el["team"],
                position=pos_map.get(el.get("element_type", 3), Position.MID),
                current_price=round(float(el.get("now_cost", 50)) / 10.0, 1),
                selected_by_pct=sel_pct,
                status=el.get("status", "a"),
                chance_of_playing_next_round=el.get("chance_of_playing_next_round"),
                news=el.get("news", "") or ""
            ))
        return players

    def get_teams(self) -> List[Team]:
        data = self._fetch_bootstrap()
        teams_raw = data.get("teams", [])
        if not teams_raw:
            raise LiveDataUnavailableError("No teams found in official FPL API response")

        teams = []
        for t in teams_raw:
            teams.append(Team(
                team_id=t["id"],
                name=t.get("name", f"Team {t['id']}"),
                short_name=t.get("short_name", f"T{t['id']}"),
                strength_attack_home=float(t.get("strength_attack_home", 1000)) / 1000.0,
                strength_attack_away=float(t.get("strength_attack_away", 1000)) / 1000.0,
                strength_defence_home=float(t.get("strength_defence_home", 1000)) / 1000.0,
                strength_defence_away=float(t.get("strength_defence_away", 1000)) / 1000.0
            ))
        return teams

    def get_fixtures(self) -> List[Fixture]:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/fixtures/",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            if resp.status_code == 200:
                fixtures_raw = resp.json()
                res = []
                for f in fixtures_raw:
                    if f.get("event") is not None:
                        res.append(Fixture(
                            fixture_id=f["id"],
                            gameweek=f["event"],
                            home_team_id=f["team_h"],
                            away_team_id=f["team_a"],
                            kickoff_time=f.get("kickoff_time") or "",
                            home_score=f.get("team_h_score"),
                            away_score=f.get("team_a_score"),
                            finished=bool(f.get("finished", False)),
                            difficulty_home=int(f.get("team_h_difficulty", 3)),
                            difficulty_away=int(f.get("team_a_difficulty", 3))
                        ))
                return res
            else:
                raise LiveDataUnavailableError(f"Official FPL /fixtures/ returned HTTP {resp.status_code}")
        except requests.RequestException as e:
            raise LiveDataUnavailableError(f"Failed to fetch fixtures from official FPL: {str(e)}")

    def get_gameweeks(self) -> List[Gameweek]:
        data = self._fetch_bootstrap()
        events = data.get("events", [])
        if not events:
            raise LiveDataUnavailableError("No gameweeks found in official FPL API response")

        gws = []
        for ev in events:
            gws.append(Gameweek(
                gameweek=ev["id"],
                deadline_time=ev.get("deadline_time", ""),
                finished=bool(ev.get("finished", False)),
                is_current=bool(ev.get("is_current", False)),
                is_next=bool(ev.get("is_next", False))
            ))
        return gws

    def get_manager_state(self, manager_id: int) -> ManagerState:
        if manager_id == 99999:
            raise InvalidTeamIdError(
                "Manager ID 99999 is reserved for Demo Mode. To inspect a real squad, enter a valid official FPL Team ID, or switch to Demo Mode."
            )

        headers = self._get_headers()

        # 1. Fetch entry profile
        try:
            entry_resp = requests.get(f"{self.BASE_URL}/entry/{manager_id}/", headers=headers, timeout=self.timeout)
            if entry_resp.status_code == 404:
                raise InvalidTeamIdError(f"FPL Team ID {manager_id} does not exist.")
            elif entry_resp.status_code != 200:
                raise LiveDataUnavailableError(f"Failed to fetch entry for manager {manager_id} (HTTP {entry_resp.status_code})")
            entry_data = entry_resp.json()
        except requests.RequestException as e:
            raise LiveDataUnavailableError(f"Network error fetching manager {manager_id}: {str(e)}")

        current_event = entry_data.get("current_event")
        if not current_event:
            # Check gameweeks for the latest active event
            gws = self.get_gameweeks()
            active_gw = next((g.gameweek for g in gws if g.is_current), None)
            if not active_gw:
                active_gw = next((g.gameweek for g in gws if g.is_next), 1)
            current_event = active_gw

        # 2. Fetch picks for the current/most recent event
        picks_data = None
        target_event = current_event
        while target_event >= 1:
            try:
                picks_resp = requests.get(
                    f"{self.BASE_URL}/entry/{manager_id}/event/{target_event}/picks/",
                    headers=headers,
                    timeout=self.timeout
                )
                if picks_resp.status_code == 200:
                    picks_data = picks_resp.json()
                    break
                elif picks_resp.status_code == 404 and target_event > 1:
                    target_event -= 1
                    continue
                else:
                    raise InvalidTeamIdError(f"No squad picks registered for manager {manager_id} in event {target_event}")
            except requests.RequestException as e:
                raise LiveDataUnavailableError(f"Network error fetching picks for manager {manager_id}: {str(e)}")

        if not picks_data or "picks" not in picks_data:
            raise InvalidTeamIdError(f"Could not retrieve squad picks for manager {manager_id}")

        entry_history = picks_data.get("entry_history", {})
        bank = round(float(entry_history.get("bank", 0)) / 10.0, 1)
        overall_rank = entry_history.get("overall_rank", 100000)
        overall_points = entry_history.get("total_points", entry_data.get("summary_overall_points", 0))

        # Free transfers heuristic
        event_transfers = entry_history.get("event_transfers", 0)
        free_transfers = max(1, 1 - event_transfers)

        # Map player elements
        players_dict = {p.player_id: p for p in self.get_players()}
        squad_players = []

        for pick in picks_data.get("picks", []):
            pid = pick["element"]
            player_info = players_dict.get(pid)
            if not player_info:
                raise CurrentSquadInvalidError(
                    f"Player ID {pid} in imported squad does not exist in the active FPL elements universe."
                )

            squad_players.append(SquadPlayer(
                player_id=pid,
                position=player_info.position,
                purchase_price=player_info.current_price,
                selling_price=player_info.current_price,
                starting=pick["position"] <= 11,
                captain=bool(pick.get("is_captain", False)),
                vice_captain=bool(pick.get("is_vice_captain", False)),
                multiplier=int(pick.get("multiplier", 1))
            ))

        return ManagerState(
            manager_id=manager_id,
            manager_name=f"{entry_data.get('player_first_name', '')} {entry_data.get('player_last_name', '')}".strip() or "FPL Manager",
            team_name=entry_data.get("name", "FPL Squad"),
            gameweek=target_event,
            bank=bank,
            free_transfers=free_transfers,
            free_transfers_confirmed=False,
            overall_points=overall_points,
            overall_rank=overall_rank,
            squad=squad_players,
            chips_used=[]
        )

    def get_status(self) -> DataStatus:
        try:
            self._fetch_bootstrap()
            return self._status
        except Exception as e:
            return DataStatus(
                provider_name="Official FPL API",
                connected=False,
                last_updated=datetime.utcnow().isoformat() + "Z",
                details=f"Unavailable: {str(e)}"
            )
