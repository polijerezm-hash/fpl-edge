import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def calculate_selling_price(purchase_price: float, current_price: float) -> float:
    """Apply FPL's half-profit rule exactly in integer £0.1m units."""
    purchase = int(round(purchase_price * 10))
    current = int(round(current_price * 10))
    if current <= purchase:
        return current / 10.0
    return (purchase + (current - purchase) // 2) / 10.0


def reconstruct_free_transfers(
    event_history: List[Dict[str, Any]],
    chips: List[Dict[str, Any]],
    through_event: int,
    max_free_transfers: int = 5,
) -> int:
    """Replay public manager history into the exact next-deadline FT balance."""
    transfer_chip_events = {
        int(row.get("event", 0) or 0)
        for row in chips
        if str(row.get("name", "")).lower() in {"wildcard", "freehit", "free_hit"}
    }
    free_transfers = 1
    for row in sorted(event_history, key=lambda item: int(item.get("event", 0) or 0)):
        event = int(row.get("event", 0) or 0)
        # The initial squad is not a transfer decision. GW2 starts with one FT.
        if event < 2 or event > int(through_event):
            continue
        if event in transfer_chip_events:
            continue
        transfers = max(0, int(row.get("event_transfers", 0) or 0))
        paid_transfers = max(0, int(row.get("event_transfers_cost", 0) or 0) // 4)
        used = max(0, min(free_transfers, transfers - paid_transfers))
        free_transfers = min(
            max_free_transfers,
            max(1, free_transfers - used + 1),
        )
    return free_transfers

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

    def get_manager_leagues(self, manager_id: int) -> List[Dict[str, Any]]:
        return []

    def get_mini_league_analysis(
        self,
        manager_id: int,
        league_id: int,
        gameweek: int,
        players: List[Player]
    ) -> Dict[str, Any]:
        raise LiveDataUnavailableError("Mini-league analysis is not available for this provider")

    def enrich_player_histories(self, players: List[Player], player_ids: List[int]) -> List[Player]:
        return players


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

    def get_manager_leagues(self, manager_id: int) -> List[Dict[str, Any]]:
        return [
            {"id": 9001, "name": "Sunday League Legends", "league_type": "x", "rank": 2, "last_rank": 3, "entries": 12},
            {"id": 9002, "name": "Office Invitational", "league_type": "x", "rank": 5, "last_rank": 5, "entries": 28},
            {"id": 9003, "name": "Family & Friends", "league_type": "x", "rank": 1, "last_rank": 1, "entries": 9},
        ]

    def get_mini_league_analysis(
        self,
        manager_id: int,
        league_id: int,
        gameweek: int,
        players: List[Player]
    ) -> Dict[str, Any]:
        leagues = {league["id"]: league for league in self.get_manager_leagues(manager_id)}
        league = leagues.get(league_id, next(iter(leagues.values())))
        player_map = {p.player_id: p for p in players}
        user_owned = {sp.player_id for sp in DEMO_MANAGER_SQUAD.squad}
        demo_eo = {401: 142.0, 301: 98.0, 303: 85.0, 302: 72.0, 304: 25.0, 305: 18.0, 203: 44.0}
        exposures = []
        for pid, eo in demo_eo.items():
            player = player_map.get(pid)
            if player:
                exposures.append({
                    "player_id": pid,
                    "web_name": player.web_name,
                    "league_eo": eo,
                    "you_own": pid in user_owned,
                    "your_multiplier": 2 if pid == 301 else (1 if pid in user_owned else 0),
                })
        return {
            "league": league,
            "gameweek": gameweek,
            "sample_size": league.get("entries", 12),
            "standings": [
                {"rank": 1, "entry": 81001, "entry_name": "Expected Toulouse", "player_name": "Alex Morgan", "total": 286, "event_total": 63},
                {"rank": league.get("rank", 2), "entry": manager_id, "entry_name": DEMO_MANAGER_SQUAD.team_name, "player_name": DEMO_MANAGER_SQUAD.manager_name, "total": DEMO_MANAGER_SQUAD.overall_points, "event_total": 58},
                {"rank": 3, "entry": 81003, "entry_name": "Moves Like Agger", "player_name": "Sam Taylor", "total": 253, "event_total": 51},
            ],
            "exposures": sorted(exposures, key=lambda row: row["league_eo"], reverse=True),
        }


class FplOfficialProvider(DataProvider):
    data_mode: str = "live"
    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._bootstrap_cache: Optional[Dict[str, Any]] = None
        self._last_fetch: float = 0
        self._history_cache: Dict[int, tuple] = {}
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

            def safe_float(val, default=0.0):
                try:
                    return float(val) if val is not None else default
                except (ValueError, TypeError):
                    return default

            def safe_int(val, default=0):
                try:
                    return int(val) if val is not None else default
                except (ValueError, TypeError):
                    return default

            player_id = el["id"]
            cached_history = self._history_cache.get(player_id)
            recent_history = cached_history[1] if cached_history and time.time() - cached_history[0] < 1800 else []
            players.append(Player(
                player_id=player_id,
                first_name=el.get("first_name", ""),
                second_name=el.get("second_name", ""),
                web_name=el.get("web_name", "Unknown"),
                team_id=el["team"],
                position=pos_map.get(el.get("element_type", 3), Position.MID),
                current_price=round(safe_float(el.get("now_cost", 50)) / 10.0, 1),
                selected_by_pct=sel_pct,
                season_start_price=round(
                    (
                        safe_float(el.get("now_cost", 50))
                        - safe_float(el.get("cost_change_start", 0))
                    )
                    / 10.0,
                    1,
                ),
                can_select=bool(el.get("can_select", True)),
                status=el.get("status", "a"),
                chance_of_playing_next_round=el.get("chance_of_playing_next_round"),
                news=el.get("news", "") or "",
                minutes=safe_int(el.get("minutes")),
                starts=safe_int(el.get("starts")),
                form=safe_float(el.get("form")),
                ep_next=safe_float(el.get("ep_next")),
                points_per_game=safe_float(el.get("points_per_game")),
                total_points=safe_int(el.get("total_points")),
                goals_scored=safe_int(el.get("goals_scored")),
                assists=safe_int(el.get("assists")),
                clean_sheets=safe_int(el.get("clean_sheets")),
                saves=safe_int(el.get("saves")),
                bonus=safe_int(el.get("bonus")),
                expected_goals=safe_float(el.get("expected_goals")),
                expected_assists=safe_float(el.get("expected_assists")),
                expected_goal_involvements=safe_float(el.get("expected_goal_involvements")),
                expected_goals_conceded=safe_float(el.get("expected_goals_conceded")),
                influence=safe_float(el.get("influence")),
                creativity=safe_float(el.get("creativity")),
                threat=safe_float(el.get("threat")),
                ict_index=safe_float(el.get("ict_index")),
                recent_history=recent_history,
            ))
        return players

    def enrich_player_histories(self, players: List[Player], player_ids: List[int]) -> List[Player]:
        """Fetch bounded, cached element histories for the projection candidate pool."""
        requested = list(dict.fromkeys(int(pid) for pid in player_ids))[:130]
        now = time.time()
        missing = [
            pid for pid in requested
            if pid not in self._history_cache or now - self._history_cache[pid][0] >= 1800
        ]

        def fetch(pid: int):
            payload = self._get_json(f"/element-summary/{pid}/")
            history = payload.get("history", [])
            # Eight rounds is enough for a 4-6 GW half-life without making the
            # snapshot unnecessarily large.
            return pid, history[-10:]

        if missing:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(fetch, pid): pid for pid in missing}
                for future in as_completed(futures):
                    pid = futures[future]
                    try:
                        _, history = future.result()
                        self._history_cache[pid] = (now, history)
                    except Exception:
                        # History is an enhancement, never a reason to make the
                        # live official snapshot unavailable.
                        self._history_cache.setdefault(pid, (now, []))

        enriched = []
        requested_set = set(requested)
        for player in players:
            if player.player_id in requested_set:
                cached = self._history_cache.get(player.player_id)
                enriched.append(player.model_copy(update={"recent_history": cached[1] if cached else []}))
            else:
                enriched.append(player)
        return enriched

    def _get_json(self, path: str) -> Any:
        try:
            response = requests.get(
                f"{self.BASE_URL}{path}",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            if response.status_code == 404:
                raise InvalidTeamIdError(f"FPL resource was not found: {path}")
            if response.status_code != 200:
                raise LiveDataUnavailableError(
                    f"Official FPL API returned HTTP {response.status_code}",
                    details={"path": path, "status_code": response.status_code},
                )
            return response.json()
        except requests.RequestException as exc:
            raise LiveDataUnavailableError(
                f"Failed to fetch official FPL data: {str(exc)}",
                details={"path": path},
            ) from exc

    def get_manager_leagues(self, manager_id: int) -> List[Dict[str, Any]]:
        entry = self._get_json(f"/entry/{manager_id}/")
        classic = entry.get("leagues", {}).get("classic", [])
        leagues = []
        for league in classic:
            if league.get("league_type") not in {"x", "s"}:
                continue
            leagues.append({
                "id": int(league["id"]),
                "name": league.get("name", f"League {league['id']}"),
                "league_type": league.get("league_type", "x"),
                "rank": league.get("entry_rank") or league.get("rank"),
                "last_rank": league.get("entry_last_rank") or league.get("last_rank"),
                "entries": league.get("max_entries") or 0,
            })
        return leagues

    def get_mini_league_analysis(
        self,
        manager_id: int,
        league_id: int,
        gameweek: int,
        players: List[Player]
    ) -> Dict[str, Any]:
        manager_leagues = {league["id"]: league for league in self.get_manager_leagues(manager_id)}
        if league_id not in manager_leagues:
            raise InvalidTeamIdError(f"League {league_id} is not available for manager {manager_id}")

        standings_payload = self._get_json(
            f"/leagues-classic/{league_id}/standings/?page_standings=1"
        )
        standings = standings_payload.get("standings", {}).get("results", [])[:30]
        if not standings:
            return {
                "league": manager_leagues[league_id],
                "gameweek": gameweek,
                "sample_size": 0,
                "standings": [],
                "exposures": [],
            }

        def fetch_picks(entry_id: int) -> tuple[int, List[Dict[str, Any]]]:
            try:
                payload = self._get_json(f"/entry/{entry_id}/event/{gameweek}/picks/")
                return entry_id, payload.get("picks", [])
            except (LiveDataUnavailableError, InvalidTeamIdError):
                return entry_id, []

        picks_by_entry: Dict[int, List[Dict[str, Any]]] = {}
        entry_ids = [int(row["entry"]) for row in standings]
        if manager_id not in entry_ids:
            entry_ids.append(manager_id)

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(fetch_picks, entry_id) for entry_id in entry_ids]
            for future in as_completed(futures):
                entry_id, picks = future.result()
                if picks:
                    picks_by_entry[entry_id] = picks

        sample_size = len(picks_by_entry)
        if sample_size == 0:
            return {
                "league": manager_leagues[league_id],
                "gameweek": gameweek,
                "sample_size": 0,
                "standings": standings,
                "exposures": [],
            }

        ownership_counts: Dict[int, int] = {}
        multiplier_totals: Dict[int, int] = {}
        for picks in picks_by_entry.values():
            for pick in picks:
                pid = int(pick["element"])
                ownership_counts[pid] = ownership_counts.get(pid, 0) + 1
                multiplier_totals[pid] = multiplier_totals.get(pid, 0) + int(pick.get("multiplier", 0))

        user_picks = {
            int(pick["element"]): int(pick.get("multiplier", 0))
            for pick in picks_by_entry.get(manager_id, [])
        }
        player_map = {p.player_id: p for p in players}
        exposures = []
        for pid, count in ownership_counts.items():
            player = player_map.get(pid)
            if not player:
                continue
            exposures.append({
                "player_id": pid,
                "web_name": player.web_name,
                "league_ownership": round(100.0 * count / sample_size, 1),
                "league_eo": round(100.0 * multiplier_totals.get(pid, 0) / sample_size, 1),
                "you_own": pid in user_picks,
                "your_multiplier": user_picks.get(pid, 0),
            })

        return {
            "league": manager_leagues[league_id],
            "gameweek": gameweek,
            "sample_size": sample_size,
            "standings": standings,
            "exposures": sorted(exposures, key=lambda row: row["league_eo"], reverse=True),
        }

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

        # Reconstructed below from the full event history. The public API does
        # not expose the manager's current free-transfer balance directly.
        free_transfers = 1

        # Map player elements
        players_dict = {p.player_id: p for p in self.get_players()}
        # The public picks endpoint normally omits acquisition values. Rebuild
        # purchase prices for transferred-in players from the manager's public
        # transfer ledger. Players retained from the original squad fall back to
        # current price because their historic purchase price is not public.
        acquisition_prices: Dict[int, float] = {}
        chips_used: List[str] = []
        try:
            transfer_rows = self._get_json(f"/entry/{manager_id}/transfers/")
            for row in sorted(transfer_rows if isinstance(transfer_rows, list) else [], key=lambda x: x.get("time", "")):
                acquisition_prices.pop(int(row.get("element_out", 0)), None)
                incoming = int(row.get("element_in", 0))
                if incoming:
                    acquisition_prices[incoming] = round(float(row.get("element_in_cost", 0)) / 10.0, 1)
        except (LiveDataUnavailableError, InvalidTeamIdError, TypeError, ValueError):
            acquisition_prices = {}

        try:
            history_payload = self._get_json(f"/entry/{manager_id}/history/")
            raw_chips = history_payload.get("chips", []) if isinstance(history_payload, dict) else []
            chips_used = [str(row.get("name", "")) for row in raw_chips if row.get("name")]
        except (LiveDataUnavailableError, InvalidTeamIdError, TypeError, ValueError):
            history_payload = {}
            raw_chips = []

        half_start, half_end = (1, 19) if int(target_event) <= 19 else (20, 38)
        chip_aliases = {
            "wildcard": "wildcard",
            "freehit": "free_hit",
            "free_hit": "free_hit",
            "bboost": "bench_boost",
            "bench_boost": "bench_boost",
            "3xc": "triple_captain",
            "triple_captain": "triple_captain",
        }
        free_transfers = reconstruct_free_transfers(
            history_payload.get("current", []) if isinstance(history_payload, dict) else [],
            raw_chips,
            int(target_event),
        )

        used_this_half = {
            chip_aliases.get(str(row.get("name", "")).lower())
            for row in raw_chips
            if half_start <= int(row.get("event", 0) or 0) <= half_end
        }
        chips_available = {
            chip: 0 if chip in used_this_half else 1
            for chip in ("wildcard", "free_hit", "bench_boost", "triple_captain")
        }
        squad_players = []

        for pick in picks_data.get("picks", []):
            pid = pick["element"]
            player_info = players_dict.get(pid)
            if not player_info:
                raise CurrentSquadInvalidError(
                    f"Player ID {pid} in imported squad does not exist in the active FPL elements universe."
                )

            raw_purchase = pick.get("purchase_price")
            if raw_purchase is not None:
                purchase_price = round(float(raw_purchase) / 10.0, 1) if float(raw_purchase) > 25 else round(float(raw_purchase), 1)
            else:
                purchase_price = acquisition_prices.get(
                    pid,
                    player_info.season_start_price or player_info.current_price,
                )

            raw_selling = pick.get("selling_price")
            if raw_selling is not None:
                selling_price = round(float(raw_selling) / 10.0, 1) if float(raw_selling) > 25 else round(float(raw_selling), 1)
            else:
                selling_price = calculate_selling_price(purchase_price, player_info.current_price)

            squad_players.append(SquadPlayer(
                player_id=pid,
                position=player_info.position,
                purchase_price=purchase_price,
                selling_price=selling_price,
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
            chips_used=chips_used,
            chips_available=chips_available,
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
