import numpy as np
from typing import List, Dict, Any, Optional
from core.data.models import Player, Team, Availability, Position

class AvailabilityEngine:
    """
    Estimates expected minutes and start probabilities for players per fixture.
    Enforces team-level starting probability reconciliation so the expected
    number of starters per team equals 11.0.
    """
    def __init__(self):
        pass

    def estimate_player_availability(self, player: Player, team: Team, is_home: bool) -> Availability:
        # Base start probability based on official status and status text
        status_mult = 1.0
        if player.status == "d":
            status_mult = (player.chance_of_playing_next_round or 75) / 100.0
        elif player.status in ["i", "s", "u"]:
            status_mult = 0.0

        # Baseline start probability by position / tier
        if player.position == Position.GKP:
            base_p_start = 0.95 * status_mult
            e_mins_start = 90.0
            p_sub = 0.02 * status_mult
            e_mins_sub = 20.0
        else:
            # Premium/regular starters vs budget rotation players based on price and selection %
            price_factor = min(1.0, max(0.4, (player.current_price - 4.0) / 6.0))
            base_p_start = (0.50 + 0.45 * price_factor) * status_mult
            e_mins_start = 82.0 + 6.0 * price_factor
            p_sub = min(0.35, (1.0 - base_p_start) * 0.7)
            e_mins_sub = 22.0

        raw_e_mins = base_p_start * e_mins_start + p_sub * e_mins_sub

        return Availability(
            player_id=player.player_id,
            as_of_timestamp="",
            status=player.status,
            chance_start=round(base_p_start, 3),
            chance_appearance=round(min(1.0, base_p_start + p_sub), 3),
            expected_return=player.news,
            source="rule_based_availability_engine",
            confidence=0.85 if player.status == "a" else 0.50
        )

    def reconcile_team_availability(self, team_players: List[Player], team: Team, is_home: bool) -> Dict[int, Dict[str, float]]:
        """
        Reconciles starting probabilities across a team squad so the sum of start
        probabilities across all squad players equals exactly 11.0.
        """
        raw_avail = {}
        total_p_start = 0.0

        for p in team_players:
            avail = self.estimate_player_availability(p, team, is_home)
            raw_avail[p.player_id] = {
                "player": p,
                "avail": avail,
                "p_start": avail.chance_start,
                "e_mins_start": 85.0 if p.position != Position.GKP else 90.0,
                "p_sub": min(0.4, (1.0 - avail.chance_start) * 0.6),
                "e_mins_sub": 22.0 if p.position != Position.GKP else 10.0
            }
            total_p_start += avail.chance_start

        # Reconcile if total starters deviate from 11.0
        target_starters = min(11.0, float(len(team_players)))
        scaling_factor = target_starters / total_p_start if total_p_start > 0 else 1.0

        reconciled = {}
        for pid, item in raw_avail.items():
            reconciled_p_start = min(1.0, max(0.0, item["p_start"] * scaling_factor))
            p_sub = min(0.5, (1.0 - reconciled_p_start) * 0.6) if item["player"].status == "a" else 0.0
            
            e_mins = (reconciled_p_start * item["e_mins_start"]) + (p_sub * item["e_mins_sub"])
            e_mins = round(min(90.0, max(0.0, e_mins)), 1)

            reconciled[pid] = {
                "start_probability": round(reconciled_p_start, 3),
                "sub_probability": round(p_sub, 3),
                "expected_minutes": e_mins
            }

        return reconciled
