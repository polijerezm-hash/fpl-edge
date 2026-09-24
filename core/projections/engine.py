import math
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

    @staticmethod
    def _shrunk_rate(total: float, minutes: int, prior_rate: float, prior_minutes: float = 720.0) -> float:
        """Bayesian-style shrinkage keeps small samples from dominating forecasts."""
        if minutes <= 0 or total <= 0:
            return prior_rate
        observed_rate = total / (minutes / 90.0)
        evidence = minutes / (minutes + prior_minutes)
        return evidence * observed_rate + (1.0 - evidence) * prior_rate

    @classmethod
    def _ewma_rate(
        cls,
        history: List[Dict[str, Any]],
        stat_key: str,
        fallback_total: float,
        fallback_minutes: int,
        prior_rate: float,
        half_life_gameweeks: float = 5.0,
    ) -> float:
        """Minutes-weighted EWMA per 90 with prior shrinkage for small samples."""
        usable = []
        for row in history or []:
            try:
                minutes = max(0.0, float(row.get("minutes", 0) or 0))
                value = max(0.0, float(row.get(stat_key, 0) or 0))
                round_id = int(row.get("round", row.get("gameweek", 0)) or 0)
            except (TypeError, ValueError):
                continue
            if minutes > 0:
                usable.append((round_id, minutes, value))

        if not usable:
            return cls._shrunk_rate(fallback_total, fallback_minutes, prior_rate)

        # Aggregate double-Gameweek fixtures before applying recency weights.
        by_round: Dict[int, List[float]] = {}
        for round_id, minutes, value in usable:
            bucket = by_round.setdefault(round_id, [0.0, 0.0])
            bucket[0] += minutes
            bucket[1] += value
        ordered = sorted(by_round.items())[-10:]
        latest_round = ordered[-1][0]
        weighted_minutes = 0.0
        weighted_value = 0.0
        for round_id, (minutes, value) in ordered:
            age = max(0, latest_round - round_id)
            weight = 0.5 ** (age / max(1.0, half_life_gameweeks))
            weighted_minutes += weight * minutes
            weighted_value += weight * value

        if weighted_minutes <= 0:
            return cls._shrunk_rate(fallback_total, fallback_minutes, prior_rate)
        observed_rate = weighted_value / (weighted_minutes / 90.0)
        # Recent data becomes dominant after roughly four full matches.
        evidence = weighted_minutes / (weighted_minutes + 360.0)
        return evidence * observed_rate + (1.0 - evidence) * prior_rate

    @staticmethod
    def _blend_projection_sources(
        bookie_xp: Optional[float],
        ewma_xp: float,
        official_xp: Optional[float],
    ) -> Tuple[float, Dict[str, float]]:
        requested = {"bookie": 0.50, "ewma": 0.35, "official": 0.15}
        available = {
            "bookie": bookie_xp,
            "ewma": ewma_xp,
            "official": official_xp,
        }
        active_weights = {
            key: weight for key, weight in requested.items()
            if available[key] is not None
        }
        total_weight = sum(active_weights.values()) or 1.0
        weights = {key: round(weight / total_weight, 4) for key, weight in active_weights.items()}
        blended = sum(float(available[key]) * weights[key] for key in weights)
        return round(max(0.0, blended), 2), weights

    @staticmethod
    def _risk_distribution(mean_xp: float, position: Position) -> Tuple[float, float, float]:
        positional_noise = {
            Position.GKP: 1.65,
            Position.DEF: 2.05,
            Position.MID: 2.35,
            Position.FWD: 2.45,
        }[position]
        std_dev = max(positional_noise, mean_xp * 0.38 + 0.65)
        return (
            round(max(0.0, mean_xp - 1.28 * std_dev), 2),
            round(max(0.0, mean_xp - 0.06 * std_dev), 2),
            round(mean_xp + 1.28 * std_dev, 2),
        )

    def calculate_projection(
        self,
        player: Player,
        player_team: Team,
        opponent_team: Team,
        fixture: Fixture,
        is_home: bool,
        reconciled_mins: Optional[Dict[str, float]] = None,
        external_inputs: Optional[Dict[str, float]] = None,
        use_official_ep_next: bool = True,
        as_of_timestamp: str = "",
        snapshot_id: Optional[str] = None,
        model_version: str = "3.0.0"
    ) -> Projection:
        scoring = self.rules.get("scoring_rules", {})

        # 1. Minutes & Start Probability
        if not player.can_select or player.status in {"i", "s", "u"}:
            xmins = 0.0
            start_prob = 0.0
            appearance_prob = 0.0
        elif reconciled_mins:
            xmins = reconciled_mins.get("expected_minutes", 70.0)
            start_prob = reconciled_mins.get("start_probability", 0.8)
            appearance_prob = reconciled_mins.get(
                "appearance_probability",
                min(1.0, start_prob + reconciled_mins.get("sub_probability", 0.0)),
            )
        else:
            avail = self.availability_engine.estimate_player_availability(player, player_team, is_home)
            xmins = avail.expected_minutes
            start_prob = avail.chance_start
            appearance_prob = avail.chance_appearance

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

        home_attack_factor = 1.08 if is_home else 0.94
        expected_team_goals = min(3.2, max(0.35, 1.45 * att_str / max(0.65, opp_def_str) * home_attack_factor))
        expected_team_conceded = min(3.2, max(0.25, 1.35 * opp_att_str / max(0.65, def_str) / home_attack_factor))

        # 3. Component Rates per 90 mins (incorporating real player stats where available)
        price_delta = max(0.0, player.current_price - 4.5)
        
        fixture_attack_factor = min(1.65, max(0.55, expected_team_goals / 1.45))
        if player.position == Position.FWD:
            prior_goal_rate = min(0.78, 0.30 + 0.035 * price_delta)
            prior_assist_rate = min(0.34, 0.12 + 0.018 * price_delta)
            clean_sheet_prob = 0.0
            saves_90 = 0.0
            bonus_factor = 0.58
        elif player.position == Position.MID:
            prior_goal_rate = min(0.62, 0.16 + 0.028 * price_delta)
            prior_assist_rate = min(0.44, 0.15 + 0.022 * price_delta)
            clean_sheet_prob = math.exp(-expected_team_conceded) * 0.85
            saves_90 = 0.0
            bonus_factor = 0.52
        elif player.position == Position.DEF:
            prior_goal_rate = min(0.18, 0.025 + 0.008 * price_delta)
            prior_assist_rate = min(0.25, 0.055 + 0.012 * price_delta)
            clean_sheet_prob = math.exp(-expected_team_conceded)
            saves_90 = 0.0
            bonus_factor = 0.38
        else: # GKP
            prior_goal_rate = 0.0
            prior_assist_rate = 0.003
            clean_sheet_prob = math.exp(-expected_team_conceded)
            historical_saves_90 = self._shrunk_rate(float(player.saves), player.minutes, 2.8, 900.0)
            saves_90 = max(1.2, historical_saves_90 * min(1.45, max(0.75, expected_team_conceded / 1.25)))
            bonus_factor = 0.30

        goal_rate_90 = self._ewma_rate(
            player.recent_history,
            "expected_goals",
            player.expected_goals,
            player.minutes,
            prior_goal_rate,
        )
        assist_rate_90 = self._ewma_rate(
            player.recent_history,
            "expected_assists",
            player.expected_assists,
            player.minutes,
            prior_assist_rate,
        )
        # Apply fixture/team context without erasing longer-term player quality.
        goal_rate_90 *= 0.65 + 0.35 * fixture_attack_factor
        assist_rate_90 *= 0.72 + 0.28 * fixture_attack_factor

        # Scale by expected minutes
        expected_goals = goal_rate_90 * mins_fraction
        expected_assists = assist_rate_90 * mins_fraction
        expected_saves = saves_90 * mins_fraction
        
        # Appearance Points
        p_60_plus = min(start_prob, max(0.0, (xmins - 12.0) / 72.0))
        appearance_xp = appearance_prob + p_60_plus

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
        card_deduction = 0.10 * mins_fraction
        historical_bonus_90 = self._shrunk_rate(float(player.bonus), player.minutes, 0.18, 900.0)
        bonus_xp = (
            expected_goals * 1.55
            + expected_assists * 1.05
            + p_60_plus * clean_sheet_prob * (0.55 if player.position in {Position.GKP, Position.DEF} else 0.15)
            + historical_bonus_90 * mins_fraction * 0.25
        ) * bonus_factor

        ewma_model_xp = appearance_xp + goal_xp + assist_xp + cs_xp + save_xp + bonus_xp - conceded_xp_deduction - card_deduction
        ewma_model_xp = round(max(0.0, ewma_model_xp), 2)

        # Convert bookmaker event probabilities into the same FPL point space.
        external_inputs = external_inputs or {}
        has_bookie_signal = any(
            external_inputs.get(key) is not None
            for key in ("goal_probability", "assist_probability", "clean_sheet_probability")
        )
        bookie_xp: Optional[float] = None
        if has_bookie_signal:
            goal_probability = external_inputs.get("goal_probability")
            assist_probability = external_inputs.get("assist_probability")
            cs_probability = external_inputs.get("clean_sheet_probability")
            bookie_goal_xp = (
                float(goal_probability) * appearance_prob * goal_pts
                if goal_probability is not None else goal_xp
            )
            bookie_assist_xp = (
                float(assist_probability) * appearance_prob * scoring.get("assists", 3)
                if assist_probability is not None else assist_xp
            )
            bookie_cs_xp = (
                p_60_plus * float(cs_probability) * cs_pts
                if cs_probability is not None else cs_xp
            )
            return_bonus = 0.28 * (bookie_goal_xp + bookie_assist_xp)
            bookie_xp = round(max(
                0.0,
                appearance_xp + bookie_goal_xp + bookie_assist_xp + bookie_cs_xp
                + save_xp + return_bonus - conceded_xp_deduction - card_deduction,
            ), 2)

        official_xp = (
            round(player.ep_next, 2)
            if use_official_ep_next and player.ep_next > 0 else None
        )
        mean_xp, source_weights = self._blend_projection_sources(
            bookie_xp=bookie_xp,
            ewma_xp=ewma_model_xp,
            official_xp=official_xp,
        )

        p10, p50, p90 = self._risk_distribution(mean_xp, player.position)

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
            fixture_ids=[fixture.fixture_id],
            ewma_xp=ewma_model_xp,
            bookie_xp=bookie_xp,
            official_xp=official_xp,
            source_weights=source_weights,
        )

    def calculate_gameweek_projection(
        self,
        player: Player,
        player_team: Team,
        fixtures_info: List[Tuple[Team, Fixture, bool]],
        gameweek: int,
        reconciled_mins: Optional[Dict[str, float]] = None,
        external_inputs_by_fixture: Optional[Dict[int, Dict[str, float]]] = None,
        use_official_ep_next: bool = True,
        as_of_timestamp: str = "",
        snapshot_id: Optional[str] = None,
        model_version: str = "3.0.0"
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
                external_inputs=(external_inputs_by_fixture or {}).get(fixture.fixture_id),
                use_official_ep_next=use_official_ep_next,
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
                external_inputs=(external_inputs_by_fixture or {}).get(fixture.fixture_id),
                # `ep_next` is already a gameweek-level estimate. Blend it once
                # after aggregating every fixture, never once per DGW match.
                use_official_ep_next=False,
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
        total_ewma_xp = round(sum(p.ewma_xp or 0.0 for p in sub_projections), 2)
        total_bookie_xp = (
            round(sum(p.bookie_xp or 0.0 for p in sub_projections), 2)
            if any(p.bookie_xp is not None for p in sub_projections) else None
        )
        official_xp = (
            round(player.ep_next, 2)
            if use_official_ep_next and player.ep_next > 0 else None
        )
        total_mean_xp, source_weights = self._blend_projection_sources(
            total_bookie_xp,
            total_ewma_xp,
            official_xp,
        )
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
            fixture_ids=fixture_ids,
            ewma_xp=total_ewma_xp,
            bookie_xp=total_bookie_xp,
            official_xp=official_xp,
            source_weights=source_weights,
        )
