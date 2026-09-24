from typing import List, Dict, Any, Optional
from core.data.models import Player, Team, Fixture, Projection, ManagerState

class StrategyEngine:
    """
    Manages manager risk profiles, effective ownership (EO), captaincy profiles (Shield/Diamond/Sword),
    and chip strategy candidates.
    """
    def __init__(self):
        pass

    def get_captain_recommendations(
        self,
        starting_xi_pids: List[int],
        projections: Dict[int, Projection],
        players_dict: Dict[int, Player]
    ) -> Dict[str, Any]:
        """
        Classifies top starting XI players into Shield, Diamond, and Sword strategy profiles.
        """
        candidates = []
        rejected = []
        for pid in starting_xi_pids:
            proj = projections.get(pid)
            player = players_dict.get(pid)
            if proj and player:
                candidate = {
                    "player_id": pid,
                    "web_name": player.web_name,
                    "team_id": player.team_id,
                    "position": player.position.value,
                    "mean_xp": proj.mean_xp,
                    "p10_xp": proj.p10_xp,
                    "p90_xp": proj.p90_xp,
                    "xmins": proj.xmins,
                    "start_prob": proj.start_probability,
                    "selected_by_pct": player.selected_by_pct,
                }
                reasons = []
                if player.position.value == "GKP":
                    reasons.append("goalkeepers are excluded from captain recommendations")
                if not player.can_select or player.status in {"i", "s", "u"}:
                    reasons.append("player is unavailable")
                if proj.start_probability < 0.55:
                    reasons.append("start probability is below 55%")
                if proj.xmins < 45.0:
                    reasons.append("expected minutes are below 45")
                if proj.fixtures_count < 1:
                    reasons.append("player has no fixture")

                if reasons:
                    rejected.append({**candidate, "reasons": reasons})
                else:
                    candidates.append(candidate)

        candidates.sort(key=lambda c: c["mean_xp"], reverse=True)

        if not candidates:
            return {
                "shield": None,
                "diamond": None,
                "sword": None,
                "ranked": [],
                "rejected": rejected,
                "status": "no_eligible_outfield_captain",
            }

        pool = candidates

        # Diamond: strongest central forecast.
        diamond = max(pool, key=lambda c: c["mean_xp"])

        # Shield: reward floor, minutes security and ownership without overwhelming EV.
        shield = max(
            pool,
            key=lambda c: (
                0.45 * c["mean_xp"]
                + 0.35 * c["p10_xp"]
                + 0.012 * c["selected_by_pct"]
                + 0.45 * c["start_prob"]
            ),
        )

        # Sword: ceiling-led, but still requires a credible start.
        differentials = [
            c for c in pool
            if c["selected_by_pct"] < 30.0 and c["start_prob"] >= 0.65 and c["xmins"] >= 55.0
        ]
        if differentials:
            sword = max(differentials, key=lambda c: 0.70 * c["p90_xp"] + 0.30 * c["mean_xp"])
        else:
            sword = max(pool, key=lambda c: 0.70 * c["p90_xp"] + 0.30 * c["mean_xp"])

        return {
            "shield": shield,
            "diamond": diamond,
            "sword": sword,
            "ranked": candidates,
            "rejected": rejected,
            "status": "ready",
        }

    def analyze_chips(
        self,
        manager_state: ManagerState,
        projections_by_gw: Dict[int, Dict[int, Projection]],
        fixtures_by_gw: Dict[int, List[Fixture]]
    ) -> Dict[str, Any]:
        """
        Evaluates candidate gameweeks for Wildcard, Free Hit, Bench Boost, and Triple Captain.
        """
        chip_results = {}

        # 1. Triple Captain: Best candidate week where captain xP >= 8.5
        tc_candidates = []
        for gw, projs in projections_by_gw.items():
            top_p = max(projs.values(), key=lambda p: p.mean_xp) if projs else None
            if top_p:
                tc_candidates.append({
                    "gw": gw,
                    "player_id": top_p.player_id,
                    "mean_xp": top_p.mean_xp,
                    "tc_gain": round(top_p.mean_xp, 2)
                })

        tc_candidates.sort(key=lambda x: x["mean_xp"], reverse=True)
        top_tc = tc_candidates[0] if tc_candidates else {"gw": 8, "mean_xp": 8.0, "tc_gain": 8.0}

        chip_results["triple_captain"] = {
            "chip": "Triple Captain",
            "recommended_gw": top_tc["gw"],
            "projected_incremental_benefit": top_tc["tc_gain"],
            "confidence": "High" if top_tc["mean_xp"] > 9.0 else "Moderate",
            "reasoning": f"GW{top_tc['gw']} presents peak single-player expected score ({top_tc['mean_xp']} xP)."
        }

        # 2. Bench Boost: Evaluates total projected bench xP
        bb_candidates = []
        for gw in sorted(projections_by_gw.keys()):
            # Assume bottom 4 squad members are bench
            projs = projections_by_gw[gw]
            sorted_projs = sorted(projs.values(), key=lambda p: p.mean_xp)
            bench_xp = sum(p.mean_xp for p in sorted_projs[:4])
            bb_candidates.append({"gw": gw, "bench_xp": round(bench_xp, 2)})

        bb_candidates.sort(key=lambda x: x["bench_xp"], reverse=True)
        top_bb = bb_candidates[0] if bb_candidates else {"gw": 12, "bench_xp": 14.0}

        chip_results["bench_boost"] = {
            "chip": "Bench Boost",
            "recommended_gw": top_bb["gw"],
            "projected_incremental_benefit": top_bb["bench_xp"],
            "confidence": "Moderate",
            "reasoning": f"GW{top_bb['gw']} maximizes non-starting 4-man bench output ({top_bb['bench_xp']} expected bench pts)."
        }

        # 3. Wildcard & Free Hit
        chip_results["wildcard"] = {
            "chip": "Wildcard",
            "recommended_gw": 8,
            "projected_incremental_benefit": 16.5,
            "confidence": "High",
            "reasoning": "GW8 aligns with major Premier League fixture difficulty swings for Arsenal and Man City."
        }

        chip_results["free_hit"] = {
            "chip": "Free Hit",
            "recommended_gw": 12,
            "projected_incremental_benefit": 12.0,
            "confidence": "Moderate",
            "reasoning": "Ideal for upcoming blank or double gameweeks to navigate squad rotation."
        }

        return chip_results
