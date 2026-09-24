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
        fixtures_by_gw: Dict[int, List[Fixture]],
        optimization_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Explain the chip choices made by the same multi-period solver as transfers."""
        del projections_by_gw, fixtures_by_gw
        labels = {
            "wildcard": "Wildcard",
            "free_hit": "Free Hit",
            "bench_boost": "Bench Boost",
            "triple_captain": "Triple Captain",
        }
        best_plan = ((optimization_result or {}).get("plans") or [{}])[0]
        selected_steps = {
            step.get("chip"): step
            for step in best_plan.get("gameweeks", [])
            if step.get("chip")
        }
        total_gain = max(0.0, float(best_plan.get("gain_vs_hold", 0.0)))
        results: Dict[str, Any] = {}
        for chip_name, label in labels.items():
            available = bool((manager_state.chips_available or {}).get(chip_name, 0))
            step = selected_steps.get(chip_name)
            if not available:
                results[chip_name] = {
                    "chip": label,
                    "recommended_gw": None,
                    "projected_incremental_benefit": 0.0,
                    "confidence": "Unavailable",
                    "reasoning": "This chip is not available in the current chip period.",
                }
            elif step:
                benefit = (
                    float(step.get("chip_points_added", 0.0))
                    if chip_name in {"bench_boost", "triple_captain"}
                    else total_gain
                )
                results[chip_name] = {
                    "chip": label,
                    "recommended_gw": step["gw"],
                    "projected_incremental_benefit": round(benefit, 2),
                    "confidence": "Moderate" if benefit < 8 else "High",
                    "reasoning": (
                        f"The joint transfer-and-chip model selects {label} in GW{step['gw']} "
                        "after accounting for hits, saved transfers, bench order and future value."
                    ),
                }
            else:
                results[chip_name] = {
                    "chip": label,
                    "recommended_gw": None,
                    "projected_incremental_benefit": 0.0,
                    "confidence": "Hold",
                    "reasoning": (
                        "No week in the current planning horizon clears the model's value "
                        "threshold, so retaining the chip is preferred."
                    ),
                }
        return results
