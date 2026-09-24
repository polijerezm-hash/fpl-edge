import pulp
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from core.data.models import (
    Player, Team, Fixture, Position, ManagerState, SquadPlayer, Projection
)

class PlanGameweekStep(dict):
    """Represents the tactical decision for a single gameweek in an optimization plan."""
    pass

class TransferPlan(dict):
    """Represents a multi-gameweek transfer optimization plan."""
    pass

class OptimizationEngine:
    """
    Mixed Integer Linear Programming (MILP) FPL Squad & Transfer Optimizer using PuLP.
    Optimizes 1, 3, or 5 Gameweek horizons, respects budget, FT state evolution,
    hit costs, squad rules, starting XI formation constraints, and returns Top 5 plans.
    """
    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        self.rules = rules or {
            "squad_size": 15, "gkp": 2, "def": 5, "mid": 5, "fwd": 3,
            "max_club": 3, "hit_cost": 4.0, "max_ft": 5,
            "bench_weight": 0.12, "free_transfer_value": 2.0,
            "terminal_ft_value": 0.35, "max_transfers_per_gw": 5,
            "minimum_action_edge": 1.0,
            "min_transfer_xmins": 20.0, "min_transfer_start_probability": 0.20,
            "min_captain_xmins": 45.0, "min_captain_start_probability": 0.55,
        }

    @staticmethod
    def _risk_adjusted_points(projection: Projection, risk_profile: str) -> float:
        """Use the forecast distribution; multiplying every player equally changes nothing."""
        if risk_profile == "safe":
            return 0.72 * projection.mean_xp + 0.28 * projection.p10_xp
        if risk_profile == "aggressive":
            return 0.70 * projection.mean_xp + 0.30 * projection.p90_xp
        return projection.mean_xp

    def optimize_squad(
        self,
        manager_state: ManagerState,
        all_players: List[Player],
        teams: List[Team],
        projections_by_gw: Dict[int, Dict[int, Projection]], # gw -> player_id -> Projection
        horizon: int = 3,
        risk_profile: str = "balanced", # "safe", "balanced", "aggressive"
        locked_player_ids: Optional[List[int]] = None,
        banned_player_ids: Optional[List[int]] = None,
        custom_mins_overrides: Optional[Dict[int, float]] = None,
        top_n_plans: int = 5,
        free_transfers_override: Optional[int] = None
    ) -> Dict[str, Any]:
        
        locked_player_ids = locked_player_ids or []
        banned_player_ids = banned_player_ids or []
        custom_mins_overrides = custom_mins_overrides or {}

        # 1. Target Gameweeks
        target_gws = sorted(list(projections_by_gw.keys()))[:horizon]
        if not target_gws:
            target_gws = [1, 2, 3][:horizon]

        # Free transfers confirmation/override
        if free_transfers_override is not None:
            manager_state = manager_state.model_copy()
            manager_state.free_transfers = max(1, min(5, free_transfers_override))
            manager_state.free_transfers_confirmed = True

        # 2. Candidate pool selection for solver efficiency
        squad_pids = set(sp.player_id for sp in manager_state.squad)
        mandatory_pids = squad_pids | set(locked_player_ids) | set(banned_player_ids)

        if len(all_players) > 130:
            candidate_pids = set(mandatory_pids)
            by_pos = {pos: [] for pos in [Position.GKP, Position.DEF, Position.MID, Position.FWD]}
            for p in all_players:
                total_xp = sum(
                    projections_by_gw.get(g, {}).get(p.player_id, Projection(
                        player_id=p.player_id, gameweek=g, as_of_timestamp="", xmins=0, start_probability=0,
                        mean_xp=0, p10_xp=0, p50_xp=0, p90_xp=0
                    )).mean_xp
                    for g in target_gws
                )
                by_pos[p.position].append((total_xp, p.player_id))

            for pos, limit in [(Position.GKP, 10), (Position.DEF, 35), (Position.MID, 45), (Position.FWD, 25)]:
                by_pos[pos].sort(key=lambda x: x[0], reverse=True)
                candidate_pids.update(pid for _, pid in by_pos[pos][:limit])

            active_players = [p for p in all_players if p.player_id in candidate_pids]
        else:
            active_players = all_players

        # Player buying/selling prices
        buy_prices = {p.player_id: p.current_price for p in all_players}
        sell_prices = {}
        for sp in manager_state.squad:
            sell_prices[sp.player_id] = sp.selling_price
        for p in all_players:
            if p.player_id not in sell_prices:
                sell_prices[p.player_id] = p.current_price

        if risk_profile not in {"safe", "balanced", "aggressive"}:
            risk_profile = "balanced"

        # 3. Create Optimization Problem
        plans = []
        excluded_transfer_sets = []
        seen_plan_signatures = set()

        # Calculate HOLD (do nothing) baseline first
        hold_plan = self._solve_single_pass(
            manager_state, active_players, target_gws, projections_by_gw,
            buy_prices, sell_prices, locked_player_ids, banned_player_ids,
            custom_mins_overrides, risk_profile, force_transfers_limit=0
        )
        baseline_xp = hold_plan["expected_points"] if hold_plan else 0.0
        baseline_eval = hold_plan["evaluation_score"] if hold_plan else 0.0

        for round_idx in range(top_n_plans):
            plan = self._solve_single_pass(
                manager_state, active_players, target_gws, projections_by_gw,
                buy_prices, sell_prices, locked_player_ids, banned_player_ids,
                custom_mins_overrides, risk_profile,
                excluded_transfers=excluded_transfer_sets,
                max_transfers_gw1=2 if round_idx > 0 else None
            )

            if not plan:
                break

            signature = tuple(
                (
                    step["gw"],
                    tuple(sorted(step["transfers_out"])),
                    tuple(sorted(step["transfers_in"])),
                )
                for step in plan["gameweeks"]
            )
            if signature in seen_plan_signatures:
                break
            seen_plan_signatures.add(signature)

            plan["rank"] = round_idx + 1
            has_immediate_transfers = bool(plan["gameweeks"][0]["transfers_in"])
            plan["plan_code"] = chr(65 + round_idx) if has_immediate_transfers else "ROLL"
            plan["gain_vs_hold"] = round(plan["expected_points"] - baseline_xp, 2)
            plan["evaluation_gain_vs_hold"] = round(plan["evaluation_score"] - baseline_eval, 2)
            plans.append(plan)

            # Record transfers to force diversity in next rounds
            transfers_in_gw1 = tuple(sorted(plan["gameweeks"][0]["transfers_in"]))
            if transfers_in_gw1:
                excluded_transfer_sets.append(transfers_in_gw1)
            elif not has_immediate_transfers:
                break

        # Always expose the real roll baseline. If acting now does not clear a
        # meaningful edge, make rolling the recommendation rather than presenting
        # a marginal move as false precision.
        if hold_plan:
            hold_plan["plan_code"] = "ROLL"
            hold_plan["gain_vs_hold"] = 0.0
            hold_plan["evaluation_gain_vs_hold"] = 0.0
            hold_signature = tuple(
                (
                    step["gw"],
                    tuple(sorted(step["transfers_out"])),
                    tuple(sorted(step["transfers_in"])),
                )
                for step in hold_plan["gameweeks"]
            )
            if hold_signature not in seen_plan_signatures:
                plans.append(hold_plan)

            action_plans = [plan for plan in plans if plan["gameweeks"][0]["transfers_in"]]
            best_action_edge = max(
                [plan.get("evaluation_gain_vs_hold", 0.0) for plan in action_plans],
                default=0.0,
            )
            if best_action_edge < float(self.rules.get("minimum_action_edge", 1.0)):
                plans.sort(key=lambda plan: 0 if plan["plan_code"] == "ROLL" else 1)

        for rank, plan in enumerate(plans, start=1):
            plan["rank"] = rank

        return {
            "manager_id": manager_state.manager_id,
            "horizon": horizon,
            "baseline_xp": round(baseline_xp, 2),
            "baseline_evaluation_score": round(baseline_eval, 2),
            "risk_profile": risk_profile,
            "methodology": "distribution_aware_ev_v2",
            "plans": plans[:top_n_plans]
        }

    def _solve_single_pass(
        self,
        manager_state: ManagerState,
        all_players: List[Player],
        target_gws: List[int],
        projections_by_gw: Dict[int, Dict[int, Projection]],
        buy_prices: Dict[int, float],
        sell_prices: Dict[int, float],
        locked_pids: List[int],
        banned_pids: List[int],
        mins_overrides: Dict[int, float],
        risk_profile: str,
        force_transfers_limit: Optional[int] = None,
        excluded_transfers: Optional[List[Tuple[int, ...]]] = None,
        max_transfers_gw1: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:

        prob = pulp.LpProblem("FPL_Edge_Optimization", pulp.LpMaximize)
        pids = [p.player_id for p in all_players]
        initial_squad = set(sp.player_id for sp in manager_state.squad)
        
        # Decision Variables
        squad = pulp.LpVariable.dicts("squad", ((p, g) for p in pids for g in target_gws), cat="Binary")
        start = pulp.LpVariable.dicts("start", ((p, g) for p in pids for g in target_gws), cat="Binary")
        cap = pulp.LpVariable.dicts("cap", ((p, g) for p in pids for g in target_gws), cat="Binary")
        vcap = pulp.LpVariable.dicts("vcap", ((p, g) for p in pids for g in target_gws), cat="Binary")

        # Transfer variables per GW
        transfer_in = pulp.LpVariable.dicts("tin", ((p, g) for p in pids for g in target_gws), cat="Binary")
        transfer_out = pulp.LpVariable.dicts("tout", ((p, g) for p in pids for g in target_gws), cat="Binary")

        # Free transfers and hits per GW
        ft_vars = pulp.LpVariable.dicts("ft", target_gws, lowBound=1, upBound=5, cat="Integer")
        hits_vars = pulp.LpVariable.dicts("hits", target_gws, lowBound=0, cat="Integer")
        used_ft_vars = pulp.LpVariable.dicts("used_ft", target_gws, lowBound=0, upBound=5, cat="Integer")

        # OBJECTIVE FUNCTION: Maximise expected points across horizon - hit penalty
        obj_terms = []
        for g_idx, g in enumerate(target_gws):
            discount = 0.95 ** g_idx  # 5% future discount per GW
            for p in pids:
                proj = projections_by_gw.get(g, {}).get(p)
                if proj:
                    base_xp = self._risk_adjusted_points(proj, risk_profile)
                    if p in mins_overrides:
                        base_xp *= (mins_overrides[p] / max(1.0, proj.xmins))

                    bench_weight = float(self.rules.get("bench_weight", 0.12))
                    obj_terms.append(discount * base_xp * (1.0 - bench_weight) * start[(p, g)])
                    obj_terms.append(discount * base_xp * bench_weight * squad[(p, g)])
                    obj_terms.append(discount * base_xp * cap[(p, g)])

                obj_terms.append(
                    -discount * float(self.rules.get("free_transfer_value", 1.5)) * transfer_in[(p, g)]
                )
            
            # Hit penalty: -4 pts per hit
            obj_terms.append(-discount * 4.0 * hits_vars[g])

        if target_gws:
            obj_terms.append(float(self.rules.get("terminal_ft_value", 0.35)) * ft_vars[target_gws[-1]])

        prob += pulp.lpSum(obj_terms)

        pids_by_pos = {
            pos: [p.player_id for p in all_players if p.position == pos]
            for pos in [Position.GKP, Position.DEF, Position.MID, Position.FWD]
        }

        # CONSTRAINTS
        for g_idx, g in enumerate(target_gws):
            # 1. Total Squad Size = 15
            prob += pulp.lpSum([squad[(p, g)] for p in pids]) == 15

            # 2. Position Limits in 15-man squad
            prob += pulp.lpSum([squad[(p, g)] for p in pids_by_pos[Position.GKP]]) == 2
            prob += pulp.lpSum([squad[(p, g)] for p in pids_by_pos[Position.DEF]]) == 5
            prob += pulp.lpSum([squad[(p, g)] for p in pids_by_pos[Position.MID]]) == 5
            prob += pulp.lpSum([squad[(p, g)] for p in pids_by_pos[Position.FWD]]) == 3

            # 3. Max 3 players per Club
            for team_id in range(1, 21):
                club_pids = [p.player_id for p in all_players if p.team_id == team_id]
                if club_pids:
                    prob += pulp.lpSum([squad[(p, g)] for p in club_pids]) <= 3

            # 4. Starting XI = 11, and start[p,g] <= squad[p,g]
            prob += pulp.lpSum([start[(p, g)] for p in pids]) == 11
            for p in pids:
                prob += start[(p, g)] <= squad[(p, g)]
                prob += cap[(p, g)] <= start[(p, g)]
                prob += vcap[(p, g)] <= start[(p, g)]
                prob += cap[(p, g)] + vcap[(p, g)] <= start[(p, g)]
                prob += transfer_in[(p, g)] + transfer_out[(p, g)] <= 1

            # 5. Formation Constraints (1 GKP, 3-5 DEF, 2-5 MID, 1-3 FWD)
            prob += pulp.lpSum([start[(p, g)] for p in pids_by_pos[Position.GKP]]) == 1
            prob += pulp.lpSum([start[(p, g)] for p in pids_by_pos[Position.DEF]]) >= 3
            prob += pulp.lpSum([start[(p, g)] for p in pids_by_pos[Position.DEF]]) <= 5
            prob += pulp.lpSum([start[(p, g)] for p in pids_by_pos[Position.MID]]) >= 2
            prob += pulp.lpSum([start[(p, g)] for p in pids_by_pos[Position.MID]]) <= 5
            prob += pulp.lpSum([start[(p, g)] for p in pids_by_pos[Position.FWD]]) >= 1
            prob += pulp.lpSum([start[(p, g)] for p in pids_by_pos[Position.FWD]]) <= 3

            # 6. Exactly 1 Captain & 1 Vice Captain (Captains restricted to outfield players)
            prob += pulp.lpSum([cap[(p, g)] for p in pids]) == 1
            prob += pulp.lpSum([vcap[(p, g)] for p in pids]) == 1
            for gkp_pid in pids_by_pos[Position.GKP]:
                prob += cap[(gkp_pid, g)] == 0
                prob += vcap[(gkp_pid, g)] == 0

            # Captains must be credible starters. If data cannot support the armband,
            # fail the solve instead of silently captaining a backup or goalkeeper.
            for player in all_players:
                proj = projections_by_gw.get(g, {}).get(player.player_id)
                captain_eligible = bool(
                    player.position != Position.GKP
                    and player.can_select
                    and player.status not in {"i", "s", "u"}
                    and proj
                    and proj.fixtures_count > 0
                    and proj.xmins >= float(self.rules.get("min_captain_xmins", 45.0))
                    and proj.start_probability >= float(self.rules.get("min_captain_start_probability", 0.55))
                )
                if not captain_eligible:
                    prob += cap[(player.player_id, g)] == 0
                    prob += vcap[(player.player_id, g)] == 0

            # 7. Transfers & Squad Transition
            prev_squad_vars = [1 if p in initial_squad else 0 for p in pids] if g_idx == 0 else [squad[(p, target_gws[g_idx-1])] for p in pids]

            for i, p in enumerate(pids):
                prob += squad[(p, g)] == prev_squad_vars[i] + transfer_in[(p, g)] - transfer_out[(p, g)]

            # 8. Free Transfer & Hit Calculations
            num_transfers = pulp.lpSum([transfer_in[(p, g)] for p in pids])
            prob += num_transfers <= int(self.rules.get("max_transfers_per_gw", 5))
            if force_transfers_limit is not None and g_idx == 0:
                prob += num_transfers == force_transfers_limit
            if max_transfers_gw1 is not None and g_idx == 0:
                prob += num_transfers <= max_transfers_gw1

            for player in all_players:
                proj = projections_by_gw.get(g, {}).get(player.player_id)
                transfer_eligible = bool(
                    player.can_select
                    and player.status not in {"i", "s", "u"}
                    and proj
                    and proj.fixtures_count > 0
                    and proj.xmins >= float(self.rules.get("min_transfer_xmins", 20.0))
                    and proj.start_probability >= float(self.rules.get("min_transfer_start_probability", 0.20))
                )
                if not transfer_eligible:
                    prob += transfer_in[(player.player_id, g)] == 0

            if g_idx == 0:
                prob += ft_vars[g] == manager_state.free_transfers
            else:
                prev_gw = target_gws[g_idx - 1]
                prob += ft_vars[g] <= ft_vars[prev_gw] - used_ft_vars[prev_gw] + 1

            prob += used_ft_vars[g] <= ft_vars[g]
            prob += used_ft_vars[g] <= num_transfers
            prob += hits_vars[g] == num_transfers - used_ft_vars[g]

            # 9. Bank & Budget Constraint: cumulative bank after transfers in GW g must be >= 0.0
            cum_gained = pulp.lpSum([sell_prices[p] * transfer_out[(p, target_gws[g_k])] for p in pids for g_k in range(g_idx + 1)])
            cum_spent = pulp.lpSum([buy_prices[p] * transfer_in[(p, target_gws[g_k])] for p in pids for g_k in range(g_idx + 1)])
            prob += manager_state.bank + cum_gained - cum_spent >= 0.0

            # Locked / Banned constraints
            for lp in locked_pids:
                if lp in pids:
                    prob += squad[(lp, g)] == 1
            for bp in banned_pids:
                if bp in pids:
                    prob += squad[(bp, g)] == 0

        # Avoid short-horizon churn such as selling a player and buying them back
        # two weeks later. A player may cross the squad boundary only once.
        for p in pids:
            prob += pulp.lpSum(
                transfer_in[(p, g)] + transfer_out[(p, g)] for g in target_gws
            ) <= 1

        # Exclude specific transfer in combinations for diversity
        if excluded_transfers:
            g1 = target_gws[0]
            for ex_set in excluded_transfers:
                prob += pulp.lpSum([transfer_in[(p, g1)] for p in ex_set]) <= len(ex_set) - 1

        # Solve MILP problem using PuLP CBC
        solver = pulp.PULP_CBC_CMD(msg=False)
        prob.solve(solver)

        if pulp.LpStatus[prob.status] != "Optimal":
            return None

        # Parse Solution
        evaluation_score = float(pulp.value(prob.objective))
        gw_plans = []
        total_hits = 0
        raw_expected_points = 0.0

        current_bank = manager_state.bank

        for g_idx, g in enumerate(target_gws):
            tin_list = [p for p in pids if pulp.value(transfer_in[(p, g)]) > 0.5]
            tout_list = [p for p in pids if pulp.value(transfer_out[(p, g)]) > 0.5]
            starter_list = [p for p in pids if pulp.value(start[(p, g)]) > 0.5]
            bench_list = [p for p in pids if pulp.value(squad[(p, g)]) > 0.5 and pulp.value(start[(p, g)]) <= 0.5]
            captain_pid = next((p for p in pids if pulp.value(cap[(p, g)]) > 0.5), starter_list[0] if starter_list else 0)
            vcaptain_pid = next((p for p in pids if pulp.value(vcap[(p, g)]) > 0.5), starter_list[1] if len(starter_list)>1 else 0)

            hits_incurred = int(pulp.value(hits_vars[g]))
            total_hits += hits_incurred

            discount = 0.95 ** g_idx
            bench_weight = float(self.rules.get("bench_weight", 0.12))
            raw_expected_points += discount * sum(
                projections_by_gw[g][p].mean_xp for p in starter_list if p in projections_by_gw[g]
            )
            raw_expected_points += discount * sum(
                bench_weight * projections_by_gw[g][p].mean_xp for p in bench_list if p in projections_by_gw[g]
            )
            if captain_pid in projections_by_gw[g]:
                raw_expected_points += discount * projections_by_gw[g][captain_pid].mean_xp
            raw_expected_points -= discount * 4.0 * hits_incurred

            # Bank calculation
            spent = sum(buy_prices[p] for p in tin_list)
            gained = sum(sell_prices[p] for p in tout_list)
            current_bank = round(current_bank + gained - spent, 2)
            ft_rem = int(pulp.value(ft_vars[g]))

            gw_plans.append({
                "gw": g,
                "transfers_out": tout_list,
                "transfers_in": tin_list,
                "starters": starter_list,
                "bench": bench_list,
                "captain": captain_pid,
                "vice_captain": vcaptain_pid,
                "hits": hits_incurred,
                "bank": current_bank,
                "free_transfers": ft_rem
            })

        return {
            "expected_points": round(raw_expected_points, 2),
            "evaluation_score": round(evaluation_score, 2),
            "hits": total_hits,
            "final_bank": current_bank,
            "robustness": 0.88 if total_hits == 0 else 0.76,
            "gameweeks": gw_plans
        }
