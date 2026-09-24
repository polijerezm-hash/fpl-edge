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
            "max_club": 3, "hit_cost": 4.0, "max_ft": 5
        }

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

        # Risk factor weights
        risk_mult = 1.0
        if risk_profile == "safe":
            risk_mult = 0.90 # Penalty for variance
        elif risk_profile == "aggressive":
            risk_mult = 1.10 # Boost for high ceiling

        # 3. Create Optimization Problem
        plans = []
        excluded_transfer_sets = []

        # Calculate HOLD (do nothing) baseline first
        hold_plan = self._solve_single_pass(
            manager_state, active_players, target_gws, projections_by_gw,
            buy_prices, sell_prices, locked_player_ids, banned_player_ids,
            custom_mins_overrides, risk_mult, force_transfers_limit=0
        )
        baseline_xp = hold_plan["expected_points"] if hold_plan else 0.0

        for round_idx in range(top_n_plans):
            plan = self._solve_single_pass(
                manager_state, active_players, target_gws, projections_by_gw,
                buy_prices, sell_prices, locked_player_ids, banned_player_ids,
                custom_mins_overrides, risk_mult,
                excluded_transfers=excluded_transfer_sets,
                max_transfers_gw1=2 if round_idx > 0 else None
            )

            if not plan:
                break

            plan["rank"] = round_idx + 1
            plan["plan_code"] = chr(65 + round_idx)  # A, B, C, D, E
            plan["gain_vs_hold"] = round(plan["expected_points"] - baseline_xp, 2)
            plans.append(plan)

            # Record transfers to force diversity in next rounds
            transfers_in_gw1 = tuple(sorted(plan["gameweeks"][0]["transfers_in"]))
            if transfers_in_gw1:
                excluded_transfer_sets.append(transfers_in_gw1)

        # Ensure HOLD plan is included if not present
        if not any(p["gain_vs_hold"] == 0.0 for p in plans):
            if hold_plan:
                hold_plan["rank"] = len(plans) + 1
                hold_plan["plan_code"] = "ROLL"
                hold_plan["gain_vs_hold"] = 0.0
                plans.append(hold_plan)

        return {
            "manager_id": manager_state.manager_id,
            "horizon": horizon,
            "baseline_xp": round(baseline_xp, 2),
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
        risk_mult: float,
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

        # OBJECTIVE FUNCTION: Maximise expected points across horizon - hit penalty
        obj_terms = []
        for g_idx, g in enumerate(target_gws):
            discount = 0.95 ** g_idx  # 5% future discount per GW
            for p in pids:
                proj = projections_by_gw.get(g, {}).get(p)
                if proj:
                    base_xp = proj.mean_xp
                    if p in mins_overrides:
                        base_xp *= (mins_overrides[p] / max(1.0, proj.xmins))
                    
                    adjusted_xp = base_xp * risk_mult
                    obj_terms.append(discount * adjusted_xp * start[(p, g)])
                    obj_terms.append(discount * adjusted_xp * cap[(p, g)]) # Captain double points
            
            # Hit penalty: -4 pts per hit
            obj_terms.append(-discount * 4.0 * hits_vars[g])

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

            # 7. Transfers & Squad Transition
            prev_squad_vars = [1 if p in initial_squad else 0 for p in pids] if g_idx == 0 else [squad[(p, target_gws[g_idx-1])] for p in pids]

            for i, p in enumerate(pids):
                prob += squad[(p, g)] == prev_squad_vars[i] + transfer_in[(p, g)] - transfer_out[(p, g)]

            # 8. Free Transfer & Hit Calculations
            num_transfers = pulp.lpSum([transfer_in[(p, g)] for p in pids])
            if force_transfers_limit is not None and g_idx == 0:
                prob += num_transfers == force_transfers_limit

            if g_idx == 0:
                prob += ft_vars[g] == manager_state.free_transfers
            else:
                prev_gw = target_gws[g_idx - 1]
                prob += ft_vars[g] <= ft_vars[prev_gw] - pulp.lpSum([transfer_in[(p, prev_gw)] for p in pids]) + 1

            prob += hits_vars[g] >= num_transfers - ft_vars[g]

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
        total_xp_val = float(pulp.value(prob.objective))
        gw_plans = []
        total_hits = 0

        current_bank = manager_state.bank

        for g in target_gws:
            tin_list = [p for p in pids if pulp.value(transfer_in[(p, g)]) > 0.5]
            tout_list = [p for p in pids if pulp.value(transfer_out[(p, g)]) > 0.5]
            starter_list = [p for p in pids if pulp.value(start[(p, g)]) > 0.5]
            bench_list = [p for p in pids if pulp.value(squad[(p, g)]) > 0.5 and pulp.value(start[(p, g)]) <= 0.5]
            captain_pid = next((p for p in pids if pulp.value(cap[(p, g)]) > 0.5), starter_list[0] if starter_list else 0)
            vcaptain_pid = next((p for p in pids if pulp.value(vcap[(p, g)]) > 0.5), starter_list[1] if len(starter_list)>1 else 0)

            hits_incurred = int(pulp.value(hits_vars[g]))
            total_hits += hits_incurred

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
            "expected_points": round(total_xp_val, 2),
            "hits": total_hits,
            "final_bank": current_bank,
            "robustness": 0.88 if total_hits == 0 else 0.76,
            "gameweeks": gw_plans
        }
