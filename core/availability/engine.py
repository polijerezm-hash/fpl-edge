import numpy as np
from typing import List, Dict, Any, Optional
from core.data.models import Player, Team, Availability, Position

class AvailabilityEngine:
    """
    Estimates expected minutes and start probabilities for players per fixture.
    Accurately distinguishes primary starting goalkeepers from backup goalkeepers,
    and uses real season minutes/starts data to establish accurate start probabilities.
    """
    def __init__(self):
        pass

    def estimate_player_availability(
        self,
        player: Player,
        team: Team,
        is_home: bool,
        is_primary_gkp: bool = True
    ) -> Availability:
        # Base status multiplier based on official status and status text
        status_mult = 1.0
        if player.status == "d":
            status_mult = (player.chance_of_playing_next_round if player.chance_of_playing_next_round is not None else 75) / 100.0
        elif player.status in ["i", "s", "u"]:
            status_mult = 0.0

        # Baseline start probability by position / tier
        if player.position == Position.GKP:
            if is_primary_gkp and status_mult > 0:
                base_p_start = 0.95 * status_mult
                e_mins_start = 90.0
                p_sub = 0.01 * status_mult
                e_mins_sub = 15.0
            else:
                # Backup / reserve goalkeeper
                base_p_start = 0.0
                e_mins_start = 0.0
                p_sub = 0.01 * status_mult
                e_mins_sub = 10.0
        else:
            # Outfield players (DEF, MID, FWD)
            if player.starts > 0 or player.minutes > 0:
                # Based on actual playing history
                # Assuming max team minutes is roughly 90 * GWs played
                mins_per_game = player.minutes / max(1, player.starts if player.starts > 0 else 1)
                
                # Estimate role
                if player.starts >= 3 or player.minutes >= 270:
                    # Regular starter
                    base_p_start = min(0.95, 0.75 + 0.20 * min(1.0, player.minutes / 450.0)) * status_mult
                    e_mins_start = min(90.0, max(75.0, mins_per_game))
                    p_sub = min(0.20, (1.0 - base_p_start) * 0.5)
                    e_mins_sub = 22.0
                elif player.minutes >= 90:
                    # Rotation player
                    base_p_start = 0.45 * status_mult
                    e_mins_start = 70.0
                    p_sub = 0.35 * status_mult
                    e_mins_sub = 25.0
                else:
                    # Fringe / bench player
                    base_p_start = 0.10 * status_mult
                    e_mins_start = 65.0
                    p_sub = 0.25 * status_mult
                    e_mins_sub = 20.0
            else:
                # 0 minutes played so far
                price_factor = min(1.0, max(0.0, (player.current_price - 4.0) / 8.0))
                if player.current_price >= 7.0:
                    # High price marquee player who hasn't played yet (e.g. new transfer/returning)
                    base_p_start = 0.60 * status_mult
                    e_mins_start = 75.0
                    p_sub = 0.25 * status_mult
                    e_mins_sub = 20.0
                elif player.current_price >= 5.5:
                    base_p_start = 0.25 * status_mult
                    e_mins_start = 70.0
                    p_sub = 0.30 * status_mult
                    e_mins_sub = 20.0
                else:
                    # Cheap non-playing budget enabler
                    base_p_start = 0.02 * status_mult
                    e_mins_start = 60.0
                    p_sub = 0.08 * status_mult
                    e_mins_sub = 15.0

        raw_e_mins = base_p_start * e_mins_start + p_sub * e_mins_sub

        return Availability(
            player_id=player.player_id,
            as_of_timestamp="",
            status=player.status,
            chance_start=round(base_p_start, 3),
            chance_appearance=round(min(1.0, base_p_start + p_sub), 3),
            expected_return=player.news,
            source="rule_based_availability_engine",
            confidence=0.90 if player.status == "a" else 0.50
        )

    def reconcile_team_availability(
        self,
        team_players: List[Player],
        team: Team,
        is_home: bool
    ) -> Dict[int, Dict[str, float]]:
        """
        Reconciles starting probabilities across a team squad so the sum of start
        probabilities across all squad players equals exactly 11.0 (1 GKP + 10 outfield).
        """
        if not team_players:
            return {}

        # 1. Identify primary goalkeeper
        gkps = [p for p in team_players if p.position == Position.GKP]
        primary_gkp_id = None
        if gkps:
            # Sort by healthy status, minutes played, starts, ep_next, selected_by_pct, price
            sorted_gkps = sorted(
                gkps,
                key=lambda p: (
                    1 if p.status == "a" else (0.5 if p.status == "d" else 0),
                    p.minutes,
                    p.starts,
                    p.ep_next,
                    p.selected_by_pct,
                    p.current_price
                ),
                reverse=True
            )
            primary_gkp_id = sorted_gkps[0].player_id

        raw_avail = {}
        for p in team_players:
            is_prim_gkp = (p.player_id == primary_gkp_id) if p.position == Position.GKP else False
            avail = self.estimate_player_availability(p, team, is_home, is_primary_gkp=is_prim_gkp)
            
            raw_avail[p.player_id] = {
                "player": p,
                "avail": avail,
                "p_start": avail.chance_start,
                "e_mins_start": 90.0 if p.position == Position.GKP else 80.0,
                "p_sub": 0.02 if p.position == Position.GKP else min(0.35, (1.0 - avail.chance_start) * 0.5),
                "e_mins_sub": 15.0 if p.position == Position.GKP else 22.0
            }

        # Separate GKP and Outfielders for reconciliation
        reconciled = {}
        outfield_items = {pid: item for pid, item in raw_avail.items() if item["player"].position != Position.GKP}
        gkp_items = {pid: item for pid, item in raw_avail.items() if item["player"].position == Position.GKP}

        # GKP Reconciliation (exactly 1.0 total starter for GKP)
        for pid, item in gkp_items.items():
            p_start = item["p_start"]
            p_sub = item["p_sub"] if item["player"].status == "a" else 0.0
            e_mins = round((p_start * 90.0) + (p_sub * 15.0), 1)
            reconciled[pid] = {
                "start_probability": round(p_start, 3),
                "sub_probability": round(p_sub, 3),
                "expected_minutes": round(e_mins, 1)
            }

        # Outfielder Reconciliation (exactly 10.0 target starters for outfield)
        total_outfield_p_start = sum(item["p_start"] for item in outfield_items.values())
        target_outfield = min(10.0, float(len(outfield_items)))
        
        if total_outfield_p_start > 0:
            scaling = target_outfield / total_outfield_p_start
        else:
            scaling = 1.0

        for pid, item in outfield_items.items():
            # Apply soft scaling to prevent key starters (>0.75) from being overly crushed
            raw_p = item["p_start"]
            if raw_p >= 0.70:
                rec_p = min(0.95, max(0.65, raw_p * max(0.85, min(1.15, scaling))))
            else:
                rec_p = min(0.85, max(0.0, raw_p * scaling))

            p_sub = min(0.40, (1.0 - rec_p) * 0.5) if item["player"].status == "a" else 0.0
            e_mins = (rec_p * item["e_mins_start"]) + (p_sub * item["e_mins_sub"])
            e_mins = round(min(90.0, max(0.0, e_mins)), 1)

            reconciled[pid] = {
                "start_probability": round(rec_p, 3),
                "sub_probability": round(p_sub, 3),
                "expected_minutes": e_mins
            }

        return reconciled
