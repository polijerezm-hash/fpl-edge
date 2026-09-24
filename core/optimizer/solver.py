from typing import Any, Dict, List, Optional, Tuple

import pulp

from core.data.models import ManagerState, Player, Position, Projection, Team


class PlanGameweekStep(dict):
    """Tactical decisions for one gameweek."""


class TransferPlan(dict):
    """A multi-gameweek transfer and chip plan."""


class OptimizationEngine:
    """Multi-period FPL MILP with transfers, ordered bench and native chips."""

    CHIP_NAMES = ("wildcard", "free_hit", "bench_boost", "triple_captain")

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        defaults: Dict[str, Any] = {
            "squad_size": 15,
            "gkp": 2,
            "def": 5,
            "mid": 5,
            "fwd": 3,
            "max_club": 3,
            "hit_cost": 4.0,
            "max_ft": 5,
            "time_decay": 0.90,
            "terminal_ft_value": 1.75,
            # FPL permits a full squad overhaul; only transfers beyond saved FTs
            # cost four points. The objective, not an invented hard cap, controls it.
            "max_transfers_per_gw": 15,
            "minimum_action_edge": 1.0,
            "min_transfer_xmins": 20.0,
            "min_transfer_start_probability": 0.20,
            "min_captain_xmins": 45.0,
            "min_captain_start_probability": 0.55,
            # Slot 0 is the reserve goalkeeper; 1-3 are ordered outfield subs.
            "bench_slot_weights": {0: 0.03, 1: 0.30, 2: 0.10, 3: 0.03},
            # Opportunity cost stops a short horizon from burning every chip.
            "chip_reserve_values": {
                "wildcard": 12.0,
                "free_hit": 10.0,
                "bench_boost": 8.0,
                "triple_captain": 8.0,
            },
        }
        if rules:
            defaults.update(rules)
        self.rules = defaults

    @staticmethod
    def _risk_adjusted_points(projection: Projection, risk_profile: str) -> float:
        if risk_profile == "safe":
            return 0.72 * projection.mean_xp + 0.28 * projection.p10_xp
        if risk_profile == "aggressive":
            return 0.70 * projection.mean_xp + 0.30 * projection.p90_xp
        return projection.mean_xp

    def _candidate_pool(
        self,
        all_players: List[Player],
        manager_state: ManagerState,
        projections_by_gw: Dict[int, Dict[int, Projection]],
        target_gws: List[int],
        locked_player_ids: List[int],
        banned_player_ids: List[int],
    ) -> List[Player]:
        """Keep high-EV options and at least three active budget enablers per position."""
        if len(all_players) <= 130:
            return list(all_players)

        mandatory = {sp.player_id for sp in manager_state.squad}
        mandatory.update(locked_player_ids)
        mandatory.update(banned_player_ids)
        selected = set(mandatory)
        limits = {
            Position.GKP: 10,
            Position.DEF: 35,
            Position.MID: 45,
            Position.FWD: 25,
        }

        for position, limit in limits.items():
            position_players = [p for p in all_players if p.position == position]
            ranked = sorted(
                position_players,
                key=lambda player: sum(
                    projections_by_gw.get(gw, {}).get(
                        player.player_id,
                        Projection(
                            player_id=player.player_id,
                            gameweek=gw,
                            as_of_timestamp="",
                            xmins=0,
                            start_probability=0,
                            mean_xp=0,
                            p10_xp=0,
                            p50_xp=0,
                            p90_xp=0,
                        ),
                    ).mean_xp
                    for gw in target_gws
                ),
                reverse=True,
            )
            selected.update(player.player_id for player in ranked[:limit])

            budget_enablers = sorted(
                (
                    player
                    for player in position_players
                    if player.can_select and player.status not in {"i", "s", "u"}
                ),
                key=lambda player: (player.current_price, -player.ep_next),
            )[:3]
            selected.update(player.player_id for player in budget_enablers)

        return [player for player in all_players if player.player_id in selected]

    def optimize_squad(
        self,
        manager_state: ManagerState,
        all_players: List[Player],
        teams: List[Team],
        projections_by_gw: Dict[int, Dict[int, Projection]],
        horizon: int = 3,
        risk_profile: str = "balanced",
        locked_player_ids: Optional[List[int]] = None,
        banned_player_ids: Optional[List[int]] = None,
        custom_mins_overrides: Optional[Dict[int, float]] = None,
        top_n_plans: int = 5,
        free_transfers_override: Optional[int] = None,
        allow_chips: bool = True,
        forced_chip: Optional[str] = None,
    ) -> Dict[str, Any]:
        del teams  # Club membership already lives on Player.
        locked_player_ids = locked_player_ids or []
        banned_player_ids = banned_player_ids or []
        custom_mins_overrides = custom_mins_overrides or {}
        target_gws = sorted(projections_by_gw)[:horizon]
        if not target_gws:
            target_gws = list(range(1, horizon + 1))

        if free_transfers_override is not None:
            manager_state = manager_state.model_copy()
            manager_state.free_transfers = max(
                1, min(int(self.rules["max_ft"]), int(free_transfers_override))
            )
            manager_state.free_transfers_confirmed = True

        if risk_profile not in {"safe", "balanced", "aggressive"}:
            risk_profile = "balanced"
        if forced_chip and forced_chip not in self.CHIP_NAMES:
            forced_chip = None

        active_players = self._candidate_pool(
            all_players,
            manager_state,
            projections_by_gw,
            target_gws,
            locked_player_ids,
            banned_player_ids,
        )
        buy_prices = {player.player_id: player.current_price for player in active_players}
        sell_prices = dict(buy_prices)
        sell_prices.update({sp.player_id: sp.selling_price for sp in manager_state.squad})

        hold_plan = self._solve_single_pass(
            manager_state,
            active_players,
            target_gws,
            projections_by_gw,
            buy_prices,
            sell_prices,
            locked_player_ids,
            banned_player_ids,
            custom_mins_overrides,
            risk_profile,
            force_transfers_limit=0,
            allow_chips=False,
        )
        baseline_xp = hold_plan["expected_points"] if hold_plan else 0.0
        baseline_eval = hold_plan["evaluation_score"] if hold_plan else 0.0

        plans: List[Dict[str, Any]] = []
        excluded_transfer_sets: List[Tuple[int, ...]] = []
        seen_signatures = set()
        for round_idx in range(max(1, top_n_plans)):
            plan = self._solve_single_pass(
                manager_state,
                active_players,
                target_gws,
                projections_by_gw,
                buy_prices,
                sell_prices,
                locked_player_ids,
                banned_player_ids,
                custom_mins_overrides,
                risk_profile,
                excluded_transfers=excluded_transfer_sets,
                max_transfers_gw1=2 if round_idx else None,
                allow_chips=allow_chips,
                forced_chip=forced_chip,
            )
            if not plan:
                break

            signature = tuple(
                (
                    step["gw"],
                    step.get("chip"),
                    tuple(sorted(step["transfers_out"])),
                    tuple(sorted(step["transfers_in"])),
                    tuple(sorted(step.get("free_hit_transfers_out", []))),
                    tuple(sorted(step.get("free_hit_transfers_in", []))),
                )
                for step in plan["gameweeks"]
            )
            if signature in seen_signatures:
                break
            seen_signatures.add(signature)
            plan["plan_code"] = chr(65 + round_idx)
            plan["gain_vs_hold"] = round(plan["expected_points"] - baseline_xp, 2)
            plan["evaluation_gain_vs_hold"] = round(
                plan["evaluation_score"] - baseline_eval, 2
            )
            plans.append(plan)

            first_in = tuple(sorted(plan["gameweeks"][0]["transfers_in"]))
            if first_in:
                excluded_transfer_sets.append(first_in)
            else:
                break

        if hold_plan:
            hold_plan["plan_code"] = "ROLL"
            hold_plan["gain_vs_hold"] = 0.0
            hold_plan["evaluation_gain_vs_hold"] = 0.0
            hold_signature = tuple(
                (
                    step["gw"],
                    step.get("chip"),
                    tuple(sorted(step["transfers_out"])),
                    tuple(sorted(step["transfers_in"])),
                    (),
                    (),
                )
                for step in hold_plan["gameweeks"]
            )
            if hold_signature not in seen_signatures:
                plans.append(hold_plan)

            action_plans = [
                plan
                for plan in plans
                if plan["gameweeks"][0]["transfers_in"]
                or plan["gameweeks"][0].get("chip")
            ]
            best_edge = max(
                (plan.get("evaluation_gain_vs_hold", 0.0) for plan in action_plans),
                default=0.0,
            )
            if best_edge < float(self.rules["minimum_action_edge"]):
                plans.sort(key=lambda item: 0 if item["plan_code"] == "ROLL" else 1)

        for rank, plan in enumerate(plans[:top_n_plans], start=1):
            plan["rank"] = rank

        return {
            "manager_id": manager_state.manager_id,
            "horizon": horizon,
            "baseline_xp": round(baseline_xp, 2),
            "baseline_evaluation_score": round(baseline_eval, 2),
            "risk_profile": risk_profile,
            "methodology": "hybrid_ewma_odds_chip_milp_v3",
            "plans": plans[:top_n_plans],
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
        max_transfers_gw1: Optional[int] = None,
        allow_chips: bool = True,
        forced_chip: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not target_gws:
            return None

        problem = pulp.LpProblem("FPL_Edge_Optimization_v3", pulp.LpMaximize)
        pids = [player.player_id for player in all_players]
        players_by_id = {player.player_id: player for player in all_players}
        initial_squad = {sp.player_id for sp in manager_state.squad}
        if not initial_squad.issubset(set(pids)):
            return None

        slots = range(4)
        squad = pulp.LpVariable.dicts(
            "squad", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )
        active = pulp.LpVariable.dicts(
            "active", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )
        start = pulp.LpVariable.dicts(
            "start", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )
        captain = pulp.LpVariable.dicts(
            "captain", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )
        vice = pulp.LpVariable.dicts(
            "vice", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )
        bench = pulp.LpVariable.dicts(
            "bench",
            ((pid, gw, slot) for pid in pids for gw in target_gws for slot in slots),
            cat="Binary",
        )
        transfer_in = pulp.LpVariable.dicts(
            "tin", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )
        transfer_out = pulp.LpVariable.dicts(
            "tout", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )
        free_hit_in = pulp.LpVariable.dicts(
            "fhin", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )
        free_hit_out = pulp.LpVariable.dicts(
            "fhout", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )

        chip = {
            name: pulp.LpVariable.dicts(name, target_gws, cat="Binary")
            for name in self.CHIP_NAMES
        }
        bb_bench = pulp.LpVariable.dicts(
            "bb_bench",
            ((pid, gw, slot) for pid in pids for gw in target_gws for slot in slots),
            cat="Binary",
        )
        tc_captain = pulp.LpVariable.dicts(
            "tc_captain", ((pid, gw) for pid in pids for gw in target_gws), cat="Binary"
        )

        max_ft = int(self.rules["max_ft"])
        ft = pulp.LpVariable.dicts(
            "ft", target_gws, lowBound=1, upBound=max_ft, cat="Integer"
        )
        used_ft = pulp.LpVariable.dicts(
            "used_ft", target_gws, lowBound=0, upBound=max_ft, cat="Integer"
        )
        paid_hits = pulp.LpVariable.dicts(
            "paid_hits", target_gws, lowBound=0, upBound=15, cat="Integer"
        )
        over_free_transfer_limit = pulp.LpVariable.dicts(
            "over_ft_limit", target_gws, cat="Binary"
        )
        rolled_ft = pulp.LpVariable.dicts(
            "rolled_ft", target_gws, lowBound=1, upBound=max_ft, cat="Integer"
        )
        next_ft = pulp.LpVariable.dicts(
            "next_ft", target_gws, lowBound=1, upBound=max_ft, cat="Integer"
        )
        ft_cap = pulp.LpVariable.dicts("ft_cap", target_gws, cat="Binary")

        bench_weights = {
            int(slot): float(weight)
            for slot, weight in self.rules["bench_slot_weights"].items()
        }
        time_decay = float(self.rules["time_decay"])
        objective_terms = []
        for gw_idx, gw in enumerate(target_gws):
            discount = time_decay**gw_idx
            for pid in pids:
                projection = projections_by_gw.get(gw, {}).get(pid)
                if not projection:
                    continue
                adjusted_xp = self._risk_adjusted_points(projection, risk_profile)
                if pid in mins_overrides:
                    adjusted_xp *= float(mins_overrides[pid]) / max(1.0, projection.xmins)
                objective_terms.append(discount * adjusted_xp * start[(pid, gw)])
                objective_terms.append(discount * adjusted_xp * captain[(pid, gw)])
                objective_terms.append(discount * adjusted_xp * tc_captain[(pid, gw)])
                for slot in slots:
                    weight = bench_weights[slot]
                    objective_terms.append(
                        discount * adjusted_xp * weight * bench[(pid, gw, slot)]
                    )
                    objective_terms.append(
                        discount
                        * adjusted_xp
                        * (1.0 - weight)
                        * bb_bench[(pid, gw, slot)]
                    )

            objective_terms.append(
                -discount * float(self.rules["hit_cost"]) * paid_hits[gw]
            )
            for chip_name in self.CHIP_NAMES:
                objective_terms.append(
                    -discount
                    * float(self.rules["chip_reserve_values"].get(chip_name, 0.0))
                    * chip[chip_name][gw]
                )

        objective_terms.append(
            float(self.rules["terminal_ft_value"]) * next_ft[target_gws[-1]]
        )
        problem += pulp.lpSum(objective_terms)

        pids_by_position = {
            position: [p.player_id for p in all_players if p.position == position]
            for position in Position
        }
        team_ids = sorted({player.team_id for player in all_players})
        available_chips = manager_state.chips_available or {}
        for chip_name in self.CHIP_NAMES:
            availability = int(bool(available_chips.get(chip_name, 0)))
            if not allow_chips:
                availability = 0
            problem += pulp.lpSum(chip[chip_name][gw] for gw in target_gws) <= availability

        if forced_chip:
            first_gw = target_gws[0]
            problem += chip[forced_chip][first_gw] == 1

        for gw_idx, gw in enumerate(target_gws):
            transfer_chip = chip["wildcard"][gw] + chip["free_hit"][gw]
            problem += pulp.lpSum(chip[name][gw] for name in self.CHIP_NAMES) <= 1

            previous = {
                pid: (1 if pid in initial_squad else 0)
                if gw_idx == 0
                else squad[(pid, target_gws[gw_idx - 1])]
                for pid in pids
            }

            num_in = pulp.lpSum(transfer_in[(pid, gw)] for pid in pids)
            num_out = pulp.lpSum(transfer_out[(pid, gw)] for pid in pids)
            num_fh_in = pulp.lpSum(free_hit_in[(pid, gw)] for pid in pids)
            num_fh_out = pulp.lpSum(free_hit_out[(pid, gw)] for pid in pids)
            problem += num_in == num_out
            problem += num_fh_in == num_fh_out
            problem += num_in <= int(self.rules["max_transfers_per_gw"]) + 10 * chip["wildcard"][gw]
            problem += num_in <= 15 * (1 - chip["free_hit"][gw])
            problem += num_fh_in <= 15 * chip["free_hit"][gw]

            if force_transfers_limit is not None and gw_idx == 0:
                problem += num_in == force_transfers_limit
            if max_transfers_gw1 is not None and gw_idx == 0:
                problem += num_in <= max_transfers_gw1

            for pid in pids:
                problem += (
                    squad[(pid, gw)]
                    == previous[pid] + transfer_in[(pid, gw)] - transfer_out[(pid, gw)]
                )
                problem += transfer_out[(pid, gw)] <= previous[pid]
                problem += transfer_in[(pid, gw)] <= 1 - previous[pid]
                problem += transfer_in[(pid, gw)] + transfer_out[(pid, gw)] <= 1

                problem += (
                    active[(pid, gw)]
                    == squad[(pid, gw)] + free_hit_in[(pid, gw)] - free_hit_out[(pid, gw)]
                )
                problem += free_hit_in[(pid, gw)] <= chip["free_hit"][gw]
                problem += free_hit_out[(pid, gw)] <= chip["free_hit"][gw]
                problem += free_hit_in[(pid, gw)] <= 1 - squad[(pid, gw)]
                problem += free_hit_out[(pid, gw)] <= squad[(pid, gw)]

                problem += start[(pid, gw)] + pulp.lpSum(
                    bench[(pid, gw, slot)] for slot in slots
                ) == active[(pid, gw)]
                problem += captain[(pid, gw)] <= start[(pid, gw)]
                problem += vice[(pid, gw)] <= start[(pid, gw)]
                problem += captain[(pid, gw)] + vice[(pid, gw)] <= start[(pid, gw)]

                for slot in slots:
                    problem += bb_bench[(pid, gw, slot)] <= bench[(pid, gw, slot)]
                    problem += bb_bench[(pid, gw, slot)] <= chip["bench_boost"][gw]
                    problem += (
                        bb_bench[(pid, gw, slot)]
                        >= bench[(pid, gw, slot)] + chip["bench_boost"][gw] - 1
                    )
                problem += tc_captain[(pid, gw)] <= captain[(pid, gw)]
                problem += tc_captain[(pid, gw)] <= chip["triple_captain"][gw]
                problem += (
                    tc_captain[(pid, gw)]
                    >= captain[(pid, gw)] + chip["triple_captain"][gw] - 1
                )

            for selection in (squad, active):
                problem += pulp.lpSum(selection[(pid, gw)] for pid in pids) == 15
                problem += pulp.lpSum(
                    selection[(pid, gw)] for pid in pids_by_position[Position.GKP]
                ) == 2
                problem += pulp.lpSum(
                    selection[(pid, gw)] for pid in pids_by_position[Position.DEF]
                ) == 5
                problem += pulp.lpSum(
                    selection[(pid, gw)] for pid in pids_by_position[Position.MID]
                ) == 5
                problem += pulp.lpSum(
                    selection[(pid, gw)] for pid in pids_by_position[Position.FWD]
                ) == 3
                for team_id in team_ids:
                    club_pids = [
                        pid for pid in pids if players_by_id[pid].team_id == team_id
                    ]
                    problem += pulp.lpSum(
                        selection[(pid, gw)] for pid in club_pids
                    ) <= int(self.rules["max_club"])

            problem += pulp.lpSum(start[(pid, gw)] for pid in pids) == 11
            problem += pulp.lpSum(captain[(pid, gw)] for pid in pids) == 1
            problem += pulp.lpSum(vice[(pid, gw)] for pid in pids) == 1
            problem += pulp.lpSum(
                start[(pid, gw)] for pid in pids_by_position[Position.GKP]
            ) == 1
            problem += pulp.lpSum(
                start[(pid, gw)] for pid in pids_by_position[Position.DEF]
            ) >= 3
            problem += pulp.lpSum(
                start[(pid, gw)] for pid in pids_by_position[Position.DEF]
            ) <= 5
            problem += pulp.lpSum(
                start[(pid, gw)] for pid in pids_by_position[Position.MID]
            ) >= 2
            problem += pulp.lpSum(
                start[(pid, gw)] for pid in pids_by_position[Position.MID]
            ) <= 5
            problem += pulp.lpSum(
                start[(pid, gw)] for pid in pids_by_position[Position.FWD]
            ) >= 1
            problem += pulp.lpSum(
                start[(pid, gw)] for pid in pids_by_position[Position.FWD]
            ) <= 3

            for slot in slots:
                problem += pulp.lpSum(bench[(pid, gw, slot)] for pid in pids) == 1
            problem += pulp.lpSum(
                bench[(pid, gw, 0)] for pid in pids_by_position[Position.GKP]
            ) == 1
            for pid in pids_by_position[Position.GKP]:
                for slot in (1, 2, 3):
                    problem += bench[(pid, gw, slot)] == 0
            for pid in pids:
                if players_by_id[pid].position != Position.GKP:
                    problem += bench[(pid, gw, 0)] == 0

            for player in all_players:
                pid = player.player_id
                projection = projections_by_gw.get(gw, {}).get(pid)
                can_transfer = bool(
                    player.can_select
                    and player.status not in {"i", "s", "u"}
                    and projection
                    and projection.fixtures_count > 0
                    and projection.xmins >= float(self.rules["min_transfer_xmins"])
                    and projection.start_probability
                    >= float(self.rules["min_transfer_start_probability"])
                )
                if not can_transfer:
                    problem += transfer_in[(pid, gw)] == 0
                    problem += free_hit_in[(pid, gw)] == 0

                can_captain = bool(
                    player.position != Position.GKP
                    and player.can_select
                    and player.status not in {"i", "s", "u"}
                    and projection
                    and projection.fixtures_count > 0
                    and projection.xmins >= float(self.rules["min_captain_xmins"])
                    and projection.start_probability
                    >= float(self.rules["min_captain_start_probability"])
                )
                if not can_captain:
                    problem += captain[(pid, gw)] == 0
                    problem += vice[(pid, gw)] == 0

            for locked_pid in locked_pids:
                if locked_pid in pids:
                    problem += squad[(locked_pid, gw)] == 1
            for banned_pid in banned_pids:
                if banned_pid in pids:
                    problem += squad[(banned_pid, gw)] == 0
                    problem += active[(banned_pid, gw)] == 0

            if gw_idx == 0:
                problem += ft[gw] == max(
                    1, min(max_ft, int(manager_state.free_transfers))
                )
            else:
                problem += ft[gw] == next_ft[target_gws[gw_idx - 1]]

            # Hits are exactly transfers above available FTs. Wildcard and Free Hit
            # consume no FT and incur no hits.
            big_m = 15
            problem += paid_hits[gw] >= num_in - ft[gw] - big_m * transfer_chip
            problem += paid_hits[gw] <= (
                num_in - ft[gw]
                + big_m * (1 - over_free_transfer_limit[gw])
                + big_m * transfer_chip
            )
            problem += paid_hits[gw] <= big_m * over_free_transfer_limit[gw]
            problem += over_free_transfer_limit[gw] <= 1 - transfer_chip
            problem += num_in - ft[gw] <= big_m * (
                over_free_transfer_limit[gw] + transfer_chip
            )
            problem += num_in - ft[gw] >= (
                1
                - big_m * (1 - over_free_transfer_limit[gw])
                - big_m * transfer_chip
            )
            problem += used_ft[gw] <= ft[gw]
            problem += used_ft[gw] <= num_in
            problem += used_ft[gw] <= big_m * (1 - transfer_chip)
            problem += used_ft[gw] - (num_in - paid_hits[gw]) <= big_m * transfer_chip
            problem += (num_in - paid_hits[gw]) - used_ft[gw] <= big_m * transfer_chip

            # Exact min(5, entering FT - used FT + 1), then preserve saved FTs
            # during Wildcard and Free Hit weeks as required by the game rules.
            raw_roll = ft[gw] - used_ft[gw] + 1
            problem += raw_roll <= max_ft + ft_cap[gw]
            problem += raw_roll >= (max_ft + 1) * ft_cap[gw]
            problem += rolled_ft[gw] == raw_roll - ft_cap[gw]
            problem += next_ft[gw] - rolled_ft[gw] <= big_m * transfer_chip
            problem += rolled_ft[gw] - next_ft[gw] <= big_m * transfer_chip
            problem += next_ft[gw] - ft[gw] <= big_m * (1 - transfer_chip)
            problem += ft[gw] - next_ft[gw] <= big_m * (1 - transfer_chip)

            cumulative_income = pulp.lpSum(
                sell_prices[pid] * transfer_out[(pid, prior_gw)]
                for pid in pids
                for prior_gw in target_gws[: gw_idx + 1]
            )
            cumulative_spend = pulp.lpSum(
                buy_prices[pid] * transfer_in[(pid, prior_gw)]
                for pid in pids
                for prior_gw in target_gws[: gw_idx + 1]
            )
            persistent_bank = manager_state.bank + cumulative_income - cumulative_spend
            problem += persistent_bank >= 0
            problem += pulp.lpSum(
                buy_prices[pid] * free_hit_in[(pid, gw)] for pid in pids
            ) <= persistent_bank + pulp.lpSum(
                sell_prices[pid] * free_hit_out[(pid, gw)] for pid in pids
            )

        for pid in pids:
            problem += pulp.lpSum(
                transfer_in[(pid, gw)] + transfer_out[(pid, gw)] for gw in target_gws
            ) <= 1

        if excluded_transfers:
            first_gw = target_gws[0]
            for excluded in excluded_transfers:
                if excluded:
                    problem += pulp.lpSum(
                        transfer_in[(pid, first_gw)]
                        for pid in excluded
                        if pid in pids
                    ) <= len(excluded) - 1

        problem.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[problem.status] != "Optimal":
            return None

        evaluation_score = float(pulp.value(problem.objective) or 0.0)
        gameweeks: List[Dict[str, Any]] = []
        current_bank = float(manager_state.bank)
        total_hits = 0
        raw_expected_points = 0.0

        for gw_idx, gw in enumerate(target_gws):
            discount = time_decay**gw_idx
            tin = [pid for pid in pids if (pulp.value(transfer_in[(pid, gw)]) or 0) > 0.5]
            tout = [pid for pid in pids if (pulp.value(transfer_out[(pid, gw)]) or 0) > 0.5]
            fh_in = [pid for pid in pids if (pulp.value(free_hit_in[(pid, gw)]) or 0) > 0.5]
            fh_out = [pid for pid in pids if (pulp.value(free_hit_out[(pid, gw)]) or 0) > 0.5]
            persistent_squad = [pid for pid in pids if (pulp.value(squad[(pid, gw)]) or 0) > 0.5]
            active_squad = [pid for pid in pids if (pulp.value(active[(pid, gw)]) or 0) > 0.5]
            starters = [pid for pid in pids if (pulp.value(start[(pid, gw)]) or 0) > 0.5]
            ordered_bench = [
                next(
                    pid
                    for pid in pids
                    if (pulp.value(bench[(pid, gw, slot)]) or 0) > 0.5
                )
                for slot in slots
            ]
            captain_pid = next(
                pid for pid in pids if (pulp.value(captain[(pid, gw)]) or 0) > 0.5
            )
            vice_pid = next(
                pid for pid in pids if (pulp.value(vice[(pid, gw)]) or 0) > 0.5
            )
            selected_chip = next(
                (
                    name
                    for name in self.CHIP_NAMES
                    if (pulp.value(chip[name][gw]) or 0) > 0.5
                ),
                None,
            )
            hits = int(round(pulp.value(paid_hits[gw]) or 0))
            total_hits += hits
            current_bank = round(
                current_bank
                + sum(sell_prices[pid] for pid in tout)
                - sum(buy_prices[pid] for pid in tin),
                2,
            )

            gw_points = sum(
                projections_by_gw.get(gw, {}).get(pid).mean_xp
                for pid in starters
                if projections_by_gw.get(gw, {}).get(pid)
            )
            chip_points_added = 0.0
            for slot, pid in enumerate(ordered_bench):
                projection = projections_by_gw.get(gw, {}).get(pid)
                if projection:
                    weight = 1.0 if selected_chip == "bench_boost" else bench_weights[slot]
                    gw_points += weight * projection.mean_xp
                    if selected_chip == "bench_boost":
                        chip_points_added += (
                            1.0 - bench_weights[slot]
                        ) * projection.mean_xp
            captain_projection = projections_by_gw.get(gw, {}).get(captain_pid)
            if captain_projection:
                gw_points += captain_projection.mean_xp
                if selected_chip == "triple_captain":
                    gw_points += captain_projection.mean_xp
                    chip_points_added += captain_projection.mean_xp
            gw_points -= float(self.rules["hit_cost"]) * hits
            raw_expected_points += discount * gw_points

            gameweeks.append(
                {
                    "gw": gw,
                    "chip": selected_chip,
                    "transfers_out": tout,
                    "transfers_in": tin,
                    "free_hit_transfers_out": fh_out,
                    "free_hit_transfers_in": fh_in,
                    "persistent_squad": persistent_squad,
                    "active_squad": active_squad,
                    "starters": starters,
                    "bench": ordered_bench,
                    "bench_order": {
                        "reserve_goalkeeper": ordered_bench[0],
                        "first_sub": ordered_bench[1],
                        "second_sub": ordered_bench[2],
                        "third_sub": ordered_bench[3],
                    },
                    "captain": captain_pid,
                    "vice_captain": vice_pid,
                    "hits": hits,
                    "bank": current_bank,
                    "free_transfers": int(round(pulp.value(ft[gw]) or 1)),
                    "next_free_transfers": int(round(pulp.value(next_ft[gw]) or 1)),
                    "expected_points": round(gw_points, 2),
                    "chip_points_added": round(chip_points_added, 2),
                }
            )

        return {
            "expected_points": round(raw_expected_points, 2),
            "evaluation_score": round(evaluation_score, 2),
            "hits": total_hits,
            "final_bank": current_bank,
            "robustness": 0.88 if total_hits == 0 else 0.76,
            "gameweeks": gameweeks,
        }
