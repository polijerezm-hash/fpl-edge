from typing import List, Dict, Any, Tuple, Optional
from core.data.models import Player, Team, Fixture, Gameweek, SquadPlayer, Position
from core.data.errors import (
    LiveDataInvalidError, CurrentSquadInvalidError, RecommendationValidationFailedError
)

class LiveDataValidator:
    """
    Validates data integrity at every critical junction in the FPL Edge pipeline.
    Ensures stale, obsolete, or mixed-snapshot records never enter or exit modelling layers.
    """

    @staticmethod
    def validate_snapshot_integrity(
        players: List[Player],
        teams: List[Team],
        fixtures: List[Fixture],
        gameweeks: List[Gameweek],
        data_mode: str = "live"
    ) -> Tuple[bool, List[str]]:
        errors = []

        # 1. Counts check
        min_players = 400 if data_mode == "live" else 20
        if len(players) < min_players:
            errors.append(f"Insufficient players: expected at least {min_players}, got {len(players)}")

        expected_teams = 20 if data_mode == "live" else 16
        if data_mode == "live" and len(teams) != 20:
            errors.append(f"Live Premier League must have exactly 20 teams, got {len(teams)}")
        elif len(teams) < 16:
            errors.append(f"Insufficient teams: got {len(teams)}")

        if len(fixtures) == 0:
            errors.append("Fixtures list is empty")
        if len(gameweeks) == 0:
            errors.append("Gameweeks list is empty")

        # 2. Team reference integrity
        valid_team_ids = set(t.team_id for t in teams)
        for p in players:
            if p.team_id not in valid_team_ids:
                errors.append(f"Player {p.player_id} ({p.web_name}) assigned to invalid team_id {p.team_id}")
                if len(errors) > 20:
                    break
            if p.current_price <= 0:
                errors.append(f"Player {p.player_id} ({p.web_name}) has non-positive price {p.current_price}")
            if p.position not in [Position.GKP, Position.DEF, Position.MID, Position.FWD]:
                errors.append(f"Player {p.player_id} ({p.web_name}) has invalid position {p.position}")

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_squad_against_snapshot(
        squad: List[SquadPlayer],
        players_dict: Dict[int, Player],
        data_mode: str = "live"
    ) -> Tuple[bool, List[str]]:
        errors = []

        if len(squad) != 15:
            errors.append(f"Squad must contain exactly 15 players, got {len(squad)}")
            return False, errors

        # Check all players exist in snapshot
        unknown_pids = []
        club_counts: Dict[int, int] = {}
        pos_counts: Dict[Position, int] = {Position.GKP: 0, Position.DEF: 0, Position.MID: 0, Position.FWD: 0}
        starters = []
        bench = []
        captains = []
        vice_captains = []

        for sp in squad:
            if sp.player_id not in players_dict:
                unknown_pids.append(sp.player_id)
                continue

            real_p = players_dict[sp.player_id]
            
            # Verify position consistency
            if sp.position != real_p.position:
                errors.append(
                    f"Player {sp.player_id} ({real_p.web_name}) position mismatch: squad has {sp.position}, snapshot has {real_p.position}"
                )

            pos_counts[real_p.position] = pos_counts.get(real_p.position, 0) + 1
            club_counts[real_p.team_id] = club_counts.get(real_p.team_id, 0) + 1

            if sp.starting:
                starters.append(sp)
            else:
                bench.append(sp)

            if sp.captain:
                captains.append(sp)
            if sp.vice_captain:
                vice_captains.append(sp)

        if unknown_pids:
            errors.append(f"Squad contains player IDs not present in active snapshot: {unknown_pids}")
            return False, errors

        # Check composition (2 GKP, 5 DEF, 5 MID, 3 FWD)
        if pos_counts[Position.GKP] != 2:
            errors.append(f"Squad must have exactly 2 GKPs, found {pos_counts[Position.GKP]}")
        if pos_counts[Position.DEF] != 5:
            errors.append(f"Squad must have exactly 5 DEFs, found {pos_counts[Position.DEF]}")
        if pos_counts[Position.MID] != 5:
            errors.append(f"Squad must have exactly 5 MIDs, found {pos_counts[Position.MID]}")
        if pos_counts[Position.FWD] != 3:
            errors.append(f"Squad must have exactly 3 FWDs, found {pos_counts[Position.FWD]}")

        # Check max 3 per club
        for team_id, count in club_counts.items():
            if count > 3:
                errors.append(f"Max 3 players per club exceeded for team_id {team_id}: has {count}")

        # Check starters & bench counts
        if len(starters) != 11:
            errors.append(f"Starting XI must have exactly 11 players, found {len(starters)}")
        if len(bench) != 4:
            errors.append(f"Bench must have exactly 4 players, found {len(bench)}")

        # Check captaincy
        if len(captains) != 1:
            errors.append(f"Squad must have exactly 1 captain, found {len(captains)}")
        elif not captains[0].starting:
            errors.append(f"Captain {captains[0].player_id} must be in starting XI")

        if len(vice_captains) != 1:
            errors.append(f"Squad must have exactly 1 vice-captain, found {len(vice_captains)}")
        elif not vice_captains[0].starting:
            errors.append(f"Vice-captain {vice_captains[0].player_id} must be in starting XI")

        # Check starting formation validity
        starter_positions = [players_dict[s.player_id].position for s in starters]
        gkps = starter_positions.count(Position.GKP)
        defs = starter_positions.count(Position.DEF)
        mids = starter_positions.count(Position.MID)
        fwds = starter_positions.count(Position.FWD)

        if gkps != 1:
            errors.append(f"Starting XI must have exactly 1 GKP, found {gkps}")
        if defs < 3 or defs > 5:
            errors.append(f"Starting XI must have 3-5 DEFs, found {defs}")
        if mids < 2 or mids > 5:
            errors.append(f"Starting XI must have 2-5 MIDs, found {mids}")
        if fwds < 1 or fwds > 3:
            errors.append(f"Starting XI must have 1-3 FWDs, found {fwds}")

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_optimiser_plan(
        plan: Dict[str, Any],
        players_dict: Dict[int, Player],
        initial_squad_pids: List[int],
        initial_bank: float
    ) -> Tuple[bool, List[str]]:
        errors = []
        # Persistent squad and one-week Free Hit squad are deliberately tracked
        # separately. A Free Hit must never leak into the following gameweek.
        current_squad = set(initial_squad_pids)
        current_bank = initial_bank

        gw_steps = plan.get("gameweeks", [])
        if not gw_steps:
            errors.append("Plan contains no gameweek steps")
            return False, errors

        for idx, gw_step in enumerate(gw_steps):
            gw = gw_step.get("gw", idx + 1)
            tin = gw_step.get("transfers_in", [])
            tout = gw_step.get("transfers_out", [])
            starters = gw_step.get("starters", [])
            bench = gw_step.get("bench", [])
            captain = gw_step.get("captain")
            vcaptain = gw_step.get("vice_captain")
            chip = gw_step.get("chip")
            fh_in = gw_step.get("free_hit_transfers_in", [])
            fh_out = gw_step.get("free_hit_transfers_out", [])
            if chip not in {None, "wildcard", "free_hit", "bench_boost", "triple_captain"}:
                errors.append(f"GW{gw}: Unknown chip {chip}")

            # 1. Incoming transfers must exist in snapshot
            for pid in tin:
                if pid not in players_dict:
                    errors.append(f"GW{gw}: Transfer in player_id {pid} does not exist in active snapshot")
                else:
                    incoming = players_dict[pid]
                    if not incoming.can_select or incoming.status in {"i", "s", "u"}:
                        errors.append(f"GW{gw}: Transfer target {incoming.web_name} is not selectable/available")
            for pid in fh_in:
                if pid not in players_dict:
                    errors.append(f"GW{gw}: Free Hit target player_id {pid} does not exist")
                else:
                    incoming = players_dict[pid]
                    if not incoming.can_select or incoming.status in {"i", "s", "u"}:
                        errors.append(f"GW{gw}: Free Hit target {incoming.web_name} is unavailable")

            # 2. Outgoing transfers must exist in squad prior to transfer
            for pid in tout:
                if pid not in current_squad:
                    errors.append(f"GW{gw}: Transfer out player_id {pid} was not in manager squad")
            for pid in fh_out:
                if pid not in current_squad:
                    errors.append(f"GW{gw}: Free Hit out player_id {pid} was not in persistent squad")

            # Normal/Wildcard transfers change the persistent squad. Free Hit
            # swaps only create the active squad for this gameweek.
            current_squad = (current_squad - set(tout)) | set(tin)
            if chip == "free_hit":
                if tin or tout:
                    errors.append(f"GW{gw}: Free Hit must not contain persistent transfers")
                active_squad = (current_squad - set(fh_out)) | set(fh_in)
            else:
                if fh_in or fh_out:
                    errors.append(f"GW{gw}: Free Hit transfers supplied without the Free Hit chip")
                active_squad = set(current_squad)

            reported_persistent = set(gw_step.get("persistent_squad", current_squad))
            reported_active = set(gw_step.get("active_squad", active_squad))
            if reported_persistent != current_squad:
                errors.append(f"GW{gw}: Reported persistent squad does not match transfers")
            if reported_active != active_squad:
                errors.append(f"GW{gw}: Reported active squad does not match chip/transfers")

            # 3. Squad size must be 15
            if len(current_squad) != 15:
                errors.append(f"GW{gw}: Resulting squad size is {len(current_squad)}, expected 15")

            # 4. Starters & Bench must match current_squad
            combined = set(starters) | set(bench)
            if combined != active_squad:
                errors.append(f"GW{gw}: Starters + Bench does not match active squad")

            if len(starters) != 11:
                errors.append(f"GW{gw}: Starting XI has {len(starters)} players, expected 11")
            if len(bench) != 4 or len(set(bench)) != 4:
                errors.append(f"GW{gw}: Ordered bench must contain four unique players")
            elif (
                bench[0] not in players_dict
                or players_dict[bench[0]].position != Position.GKP
                or any(
                    pid in players_dict and players_dict[pid].position == Position.GKP
                    for pid in bench[1:]
                )
            ):
                errors.append(f"GW{gw}: Bench must contain reserve goalkeeper then three outfield substitutes")
            if len(set(starters)) != 11:
                errors.append(f"GW{gw}: Starting XI must contain eleven unique players")

            # 5. Captain and VC in starters
            if captain not in starters:
                errors.append(f"GW{gw}: Captain {captain} is not in starting XI")
            if vcaptain not in starters:
                errors.append(f"GW{gw}: Vice-captain {vcaptain} is not in starting XI")
            if captain in players_dict and players_dict[captain].position == Position.GKP:
                errors.append(f"GW{gw}: Goalkeeper {players_dict[captain].web_name} cannot be recommended as captain")
            if vcaptain in players_dict and players_dict[vcaptain].position == Position.GKP:
                errors.append(f"GW{gw}: Goalkeeper {players_dict[vcaptain].web_name} cannot be recommended as vice-captain")

            # 6. Max 3 per club
            team_counts: Dict[int, int] = {}
            for pid in active_squad:
                if pid in players_dict:
                    tid = players_dict[pid].team_id
                    team_counts[tid] = team_counts.get(tid, 0) + 1
            for tid, count in team_counts.items():
                if count > 3:
                    errors.append(f"GW{gw}: Team {tid} has {count} players (max 3 allowed)")

            # 7. Non-negative bank
            gw_bank = gw_step.get("bank", 0.0)
            if gw_bank < -0.01:
                errors.append(f"GW{gw}: Bank balance is negative (£{gw_bank}m)")

            # 8. Position and formation checks on the actual gameweek squad.
            position_counts = {position: 0 for position in Position}
            for pid in active_squad:
                if pid in players_dict:
                    position_counts[players_dict[pid].position] += 1
            expected = {
                Position.GKP: 2,
                Position.DEF: 5,
                Position.MID: 5,
                Position.FWD: 3,
            }
            for position, count in expected.items():
                if position_counts[position] != count:
                    errors.append(
                        f"GW{gw}: Active squad has {position_counts[position]} {position.value}, expected {count}"
                    )

            starter_positions = [
                players_dict[pid].position for pid in starters if pid in players_dict
            ]
            if starter_positions.count(Position.GKP) != 1:
                errors.append(f"GW{gw}: Starting XI must contain exactly one goalkeeper")
            if not 3 <= starter_positions.count(Position.DEF) <= 5:
                errors.append(f"GW{gw}: Starting XI must contain 3-5 defenders")
            if not 2 <= starter_positions.count(Position.MID) <= 5:
                errors.append(f"GW{gw}: Starting XI must contain 2-5 midfielders")
            if not 1 <= starter_positions.count(Position.FWD) <= 3:
                errors.append(f"GW{gw}: Starting XI must contain 1-3 forwards")

            entering_ft = gw_step.get("free_transfers")
            leaving_ft = gw_step.get("next_free_transfers")
            if entering_ft is not None and not 1 <= int(entering_ft) <= 5:
                errors.append(f"GW{gw}: Entering free transfers must be between 1 and 5")
            if leaving_ft is not None and not 1 <= int(leaving_ft) <= 5:
                errors.append(f"GW{gw}: Rolled free transfers must be between 1 and 5")

        return (len(errors) == 0, errors)
