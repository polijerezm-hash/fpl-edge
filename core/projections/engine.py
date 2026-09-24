import math
import numpy as np
import yaml
from typing import List, Dict, Any, Optional, Tuple
from core.data.models import Player, Team, Fixture, Position, Projection
from core.availability.engine import AvailabilityEngine

class ProjectionEngine:
    def __init__(self, rules_path: str = "config/season_rules.yaml"):
        self.availability_engine = AvailabilityEngine()
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path: str) -> Dict[str, Any]:
        try:
            with open(rules_path, "r") as f:
                return yaml.safe_load(f)
        except Exception:
            return {
                "scoring_rules": {
                    "appearance_less_than_60": 1,
                    "appearance_60_or_more": 2,
                    "goals": {"GKP": 6, "DEF": 6, "MID": 5, "FWD": 4},
                    "assists": 3,
                    "clean_sheets": {"GKP": 4, "DEF": 4, "MID": 1, "FWD": 0},
                    "saves_per_point": 3,
                    "yellow_cards": -1,
                }
            }

    def calculate_projection(
        self,
        player: Player,
        player_team: Team,
        opponent_team: Team,
        fixture: Fixture,
        is_home: bool,
        reconciled_mins: Optional[Dict[str, float]] = None,
        as_of_timestamp: str = "",
        snapshot_id: Optional[str] = None,
        model_version: str = "1.0.0"
    ) -> Projection:
        scoring = self.rules.get("scoring_rules", {})

        # 1. Minutes & Start Probability
        if reconciled_mins:
            xmins = reconciled_mins.get("expected_minutes", 70.0)
            start_prob = reconciled_mins.get("start_probability", 0.8)
        else:
            avail = self.availability_engine.estimate_player_availability(player, player_team, is_home)
            xmins = avail.expected_minutes
            start_prob = avail.chance_start

        mins_fraction = min(1.0, max(0.0, xmins / 90.0))

        # If zero expected minutes, return zero projection immediately
        if mins_fraction <= 0.01 or start_prob <= 0.01:
            return Projection(
                player_id=player.player_id,
                gameweek=fixture.gameweek,
                model_version=model_version,
                as_of_timestamp=as_of_timestamp,
                snapshot_id=snapshot_id,
                xmins=0.0,
                start_probability=0.0,
                mean_xp=0.0,
                p10_xp=0.0,
                p50_xp=0.0,
                p90_xp=0.0,
                goal_xp=0.0,
                assist_xp=0.0,
                clean_sheet_xp=0.0,
                save_xp=0.0,
                bonus_xp=0.0,
                fixtures_count=1,
                fixture_ids=[fixture.fixture_id]
            )

        # 2. Match Context Dynamics
        att_str = player_team.strength_attack_home if is_home else player_team.strength_attack_away
        opp_def_str = opponent_team.strength_defence_away if is_home else opponent_team.strength_defence_home
        
        def_str = player_team.strength_defence_home if is_home else player_team.strength_defence_away
        opp_att_str = opponent_team.strength_attack_away if is_home else opponent_team.strength_attack_home

        expected_team_goals = max(0.4, 1.35 * att_str / max(0.6, opp_def_str))
        expected_team_conceded = max(0.3, 1.25 * opp_att_str / max(0.6, def_str))

        # 3. Component Rates per 90 mins (incorporating real player stats where available)
        price_delta = max(0.0, player.current_price - 4.5)
        
        # Calculate empirical xG per 90 / xA per 90 if player has played significant minutes
        has_stats = player.minutes >= 180
        empirical_xg_90 = (player.expected_goals / (player.minutes / 90.0)) if has_stats and player.expected_goals > 0 else None
        empirical_xa_90 = (player.expected_assists / (player.minutes / 90.0)) if has_stats and player.expected_assists > 0 else None

        if player.position == Position.FWD:
            baseline_goal_rate = (0.35 + 0.04 * price_delta) * (expected_team_goals / 1.35)
            goal_rate_90 = (0.5 * empirical_xg_90 + 0.5 * baseline_goal_rate) if empirical_xg_90 is not None else baseline_goal_rate
            
            baseline_assist_rate = 0.14 + 0.02 * price_delta
            assist_rate_90 = (0.5 * empirical_xa_90 + 0.5 * baseline_assist_rate) if empirical_xa_90 is not None else baseline_assist_rate
            
            clean_sheet_prob = 0.0
            saves_90 = 0.0
            bonus_factor = 0.60
        elif player.position == Position.MID:
            baseline_goal_rate = (0.22 + 0.035 * price_delta) * (expected_team_goals / 1.35)
            goal_rate_90 = (0.5 * empirical_xg_90 + 0.5 * baseline_goal_rate) if empirical_xg_90 is not None else baseline_goal_rate
            
            baseline_assist_rate = 0.18 + 0.025 * price_delta
            assist_rate_90 = (0.5 * empirical_xa_90 + 0.5 * baseline_assist_rate) if empirical_xa_90 is not None else baseline_assist_rate
            
            clean_sheet_prob = math.exp(-expected_team_conceded) * 0.85
            saves_90 = 0.0
            bonus_factor = 0.55
        elif player.position == Position.DEF:
            goal_rate_90 = 0.04 + 0.01 * price_delta
            assist_rate_90 = 0.08 + 0.015 * price_delta
            clean_sheet_prob = math.exp(-expected_team_conceded)
            saves_90 = 0.0
            bonus_factor = 0.40
        else: # GKP
            goal_rate_90 = 0.0
            assist_rate_90 = 0.005
            clean_sheet_prob = math.exp(-expected_team_conceded)
            saves_90 = max(1.5, 2.5 * (expected_team_conceded / 1.2))
            bonus_factor = 0.30

        # Scale by expected minutes
        expected_goals = goal_rate_90 * mins_fraction
        expected_assists = assist_rate_90 * mins_fraction
        expected_saves = saves_90 * mins_fraction
        
        # Appearance Points
        p_60_plus = start_prob * min(1.0, max(0.0, (xmins - 15.0) / 75.0))
        appearance_xp = p_60_plus * 2.0 + (1.0 - p_60_plus) * (1.0 if xmins > 5 else 0.0)

        # FPL Component Scoring
        goal_pts = scoring.get("goals", {}).get(player.position.value, 4)
        cs_pts = scoring.get("clean_sheets", {}).get(player.position.value, 0)
        
        goal_xp = expected_goals * goal_pts
        assist_xp = expected_assists * scoring.get("assists", 3)
        cs_xp = (p_60_plus * clean_sheet_prob) * cs_pts
        save_xp = (expected_saves / 3.0) * 1.0
        
        # Conceded deduction for DEF & GKP
        if player.position in [Position.DEF, Position.GKP]:
            conceded_xp_deduction = max(0.0, (expected_team_conceded - 1.0) * 0.5) * mins_fraction
        else:
            conceded_xp_deduction = 0.0

        # Cards & Bonus xP
        card_deduction = 0.12 * mins_fraction
        bonus_xp = (expected_goals * 1.8 + expected_assists * 1.2 + (1.0 if clean_sheet_prob > 0.4 else 0.0) * 0.8) * bonus_factor

        model_mean_xp = appearance_xp + goal_xp + assist_xp + cs_xp + save_xp + bonus_xp - conceded_xp_deduction - card_deduction
        model_mean_xp = round(max(0.0, model_mean_xp), 2)

        # Blend with official FPL ep_next / form signal if available
        if player.ep_next > 0:
            ep_next_mins = player.ep_next * mins_fraction
            mean_xp = round(0.50 * model_mean_xp + 0.50 * ep_next_mins, 2)
        elif player.form > 0:
            form_mult = min(1.25, max(0.75, player.form / 4.5))
            mean_xp = round(model_mean_xp * form_mult, 2)
        else:
            mean_xp = model_mean_xp

        # Monte Carlo Distribution Percentiles (P10, P50, P90)
        std_dev = max(1.2, mean_xp * 0.45 + 0.8)
        p10 = round(max(0.0, mean_xp - 1.28 * std_dev), 2)
        p50 = round(max(0.0, mean_xp - 0.1 * std_dev), 2)
        p90 = round(mean_xp + 1.28 * std_dev, 2)

        return Projection(
            player_id=player.player_id,
            gameweek=fixture.gameweek,
            model_version=model_version,
            as_of_timestamp=as_of_timestamp,
            snapshot_id=snapshot_id,
            xmins=round(xmins, 1),
            start_probability=round(start_prob, 3),
            mean_xp=mean_xp,
            p10_xp=p10,
            p50_xp=p50,
            p90_xp=p90,
            goal_xp=round(goal_xp, 2),
            assist_xp=round(assist_xp, 2),
            clean_sheet_xp=round(cs_xp, 2),
            save_xp=round(save_xp, 2),
            bonus_xp=round(bonus_xp, 2),
            fixtures_count=1,
            fixture_ids=[fixture.fixture_id]
        )

    def calculate_gameweek_projection(
        self,
        player: Player,
        player_team: Team,
        fixtures_info: List[Tuple[Team, Fixture, bool]],
        gameweek: int,
        reconciled_mins: Optional[Dict[str, float]] = None,
        as_of_timestamp: str = "",
        snapshot_id: Optional[str] = None,
        model_version: str = "1.0.0"
    ) -> Projection:
        """
        Calculates gameweek projection supporting Blank Gameweeks (0 fixtures),
        Single Gameweeks (1 fixture), and Double/Triple Gameweeks (>= 2 fixtures).
        Accumulates component xP across fixtures without dropping secondary matches.
        """
        if not fixtures_info:
            # Blank Gameweek (BGW)
            return Projection(
                player_id=player.player_id,
                gameweek=gameweek,
                model_version=model_version,
                as_of_timestamp=as_of_timestamp,
                snapshot_id=snapshot_id,
                xmins=0.0,
                start_probability=0.0,
                mean_xp=0.0,
                p10_xp=0.0,
                p50_xp=0.0,
                p90_xp=0.0,
                fixtures_count=0,
                fixture_ids=[]
            )

        if len(fixtures_info) == 1:
            opp_team, fixture, is_home = fixtures_info[0]
            return self.calculate_projection(
                player=player,
                player_team=player_team,
                opponent_team=opp_team,
                fixture=fixture,
                is_home=is_home,
                reconciled_mins=reconciled_mins,
                as_of_timestamp=as_of_timestamp,
                snapshot_id=snapshot_id,
                model_version=model_version
            )

        # Double / Multi-Fixture Gameweek (DGW)
        sub_projections = []
        variances = []
        fixture_ids = []

        for opp_team, fixture, is_home in fixtures_info:
            proj = self.calculate_projection(
                player=player,
                player_team=player_team,
                opponent_team=opp_team,
                fixture=fixture,
                is_home=is_home,
                reconciled_mins=reconciled_mins,
                as_of_timestamp=as_of_timestamp,
                snapshot_id=snapshot_id,
                model_version=model_version
            )
            sub_projections.append(proj)
            std_dev = max(1.2, proj.mean_xp * 0.45 + 0.8)
            variances.append(std_dev ** 2)
            fixture_ids.append(fixture.fixture_id)

        # Aggregate components across matches
        total_xmins = round(sum(p.xmins for p in sub_projections), 1)
        max_start_prob = round(max(p.start_probability for p in sub_projections), 3)
        total_mean_xp = round(sum(p.mean_xp for p in sub_projections), 2)
        total_goal_xp = round(sum(p.goal_xp for p in sub_projections), 2)
        total_assist_xp = round(sum(p.assist_xp for p in sub_projections), 2)
        total_cs_xp = round(sum(p.clean_sheet_xp for p in sub_projections), 2)
        total_save_xp = round(sum(p.save_xp for p in sub_projections), 2)
        total_bonus_xp = round(sum(p.bonus_xp for p in sub_projections), 2)

        compound_std_dev = math.sqrt(sum(variances))
        p10 = round(max(0.0, total_mean_xp - 1.28 * compound_std_dev), 2)
        p50 = round(max(0.0, total_mean_xp - 0.1 * compound_std_dev), 2)
        p90 = round(total_mean_xp + 1.28 * compound_std_dev, 2)

        return Projection(
            player_id=player.player_id,
            gameweek=gameweek,
            model_version=model_version,
            as_of_timestamp=as_of_timestamp,
            snapshot_id=snapshot_id,
            xmins=total_xmins,
            start_probability=max_start_prob,
            mean_xp=total_mean_xp,
            p10_xp=p10,
            p50_xp=p50,
            p90_xp=p90,
            goal_xp=total_goal_xp,
            assist_xp=total_assist_xp,
            clean_sheet_xp=total_cs_xp,
            save_xp=total_save_xp,
            bonus_xp=total_bonus_xp,
            fixtures_count=len(fixtures_info),
            fixture_ids=fixture_ids
        )
