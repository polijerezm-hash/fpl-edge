from typing import Dict, List

from core.data.models import Availability, Player, Position, Team


class AvailabilityEngine:
    """Estimate role, start probability, appearance probability and expected minutes.

    The official FPL feed exposes season-to-date usage rather than a predicted team
    sheet. This model shrinks observed starts/minutes toward a conservative role prior
    and reconciles each club to one goalkeeper and ten outfield starts.
    """

    UNAVAILABLE_STATUSES = {"i", "s", "u"}

    @staticmethod
    def _status_multiplier(player: Player) -> float:
        if not player.can_select or player.status in AvailabilityEngine.UNAVAILABLE_STATUSES:
            return 0.0
        if player.status == "d":
            chance = player.chance_of_playing_next_round
            return max(0.0, min(1.0, float(75 if chance is None else chance) / 100.0))
        return 1.0

    @staticmethod
    def _role_prior(player: Player) -> float:
        """Pre-season/new-signing prior that avoids treating every zero as a starter."""
        ownership = min(1.0, max(0.0, player.selected_by_pct / 30.0))
        ep_signal = min(1.0, max(0.0, player.ep_next / 5.0))
        price_floor = {
            Position.GKP: 4.0,
            Position.DEF: 4.0,
            Position.MID: 4.5,
            Position.FWD: 4.5,
        }[player.position]
        price_signal = min(1.0, max(0.0, (player.current_price - price_floor) / 4.0))
        prior = 0.12 + 0.52 * ownership + 0.12 * ep_signal + 0.24 * price_signal
        return min(0.92, max(0.03, prior))

    def estimate_player_availability(
        self,
        player: Player,
        team: Team,
        is_home: bool,
        is_primary_gkp: bool = True,
    ) -> Availability:
        status_mult = self._status_multiplier(player)
        prior = self._role_prior(player)

        if player.position == Position.GKP:
            chance_start = (0.94 if is_primary_gkp else 0.02) * status_mult
            chance_sub = (0.01 if is_primary_gkp else 0.03) * status_mult
            minutes_if_start = 90.0
            minutes_if_sub = 10.0
        else:
            if player.starts > 0 or player.minutes > 0:
                inferred_matches = max(1.0, float(player.starts), player.minutes / 90.0)
                start_share = min(1.0, player.starts / inferred_matches)
                minutes_share = min(1.0, player.minutes / (90.0 * inferred_matches))
                observed_role = 0.65 * start_share + 0.35 * minutes_share
                evidence = min(0.85, inferred_matches / 8.0)
                chance_start = (evidence * observed_role + (1.0 - evidence) * prior) * status_mult
            else:
                chance_start = prior * status_mult

            chance_start = min(0.96, max(0.0, chance_start))
            chance_sub = min(0.35, (1.0 - chance_start) * (0.30 if chance_start < 0.55 else 0.12)) * status_mult
            minutes_if_start = 84.0 if player.position == Position.DEF else 78.0
            minutes_if_sub = 21.0

        expected_minutes = chance_start * minutes_if_start + chance_sub * minutes_if_sub
        chance_appearance = min(1.0, chance_start + chance_sub)

        return Availability(
            player_id=player.player_id,
            as_of_timestamp="",
            status=player.status,
            chance_start=round(chance_start, 3),
            chance_appearance=round(chance_appearance, 3),
            p_start=round(chance_start, 3),
            p_sub=round(chance_sub, 3),
            minutes_if_start=minutes_if_start,
            minutes_if_sub=minutes_if_sub,
            expected_minutes=round(expected_minutes, 1),
            expected_return=player.news,
            source="role_and_usage_model_v2",
            confidence=0.88 if player.starts >= 4 and status_mult == 1.0 else 0.62,
            model_version="2.0.0",
        )

    @staticmethod
    def _normalise_probabilities(raw: Dict[int, float], target: float, cap: float = 0.97) -> Dict[int, float]:
        """Scale role scores to a team-level starting total while respecting caps."""
        result = {pid: 0.0 for pid in raw}
        active = {pid for pid, value in raw.items() if value > 0.0}
        remaining = min(target, float(len(active)))

        while active and remaining > 1e-8:
            total = sum(raw[pid] for pid in active)
            if total <= 0:
                break
            scale = remaining / total
            capped = {pid for pid in active if raw[pid] * scale >= cap}
            if not capped:
                for pid in active:
                    result[pid] = raw[pid] * scale
                break
            for pid in capped:
                result[pid] = cap
                remaining -= cap
            active -= capped

        return result

    def reconcile_team_availability(
        self,
        team_players: List[Player],
        team: Team,
        is_home: bool,
    ) -> Dict[int, Dict[str, float]]:
        if not team_players:
            return {}

        inferred_team_matches = max(
            [0.0]
            + [float(player.starts) for player in team_players]
            + [player.minutes / 90.0 for player in team_players]
        )
        has_usage_sample = inferred_team_matches >= 1.0

        gkps = [player for player in team_players if player.position == Position.GKP]
        outfielders = [player for player in team_players if player.position != Position.GKP]

        gkp_scores: Dict[int, float] = {}
        for player in gkps:
            status_mult = self._status_multiplier(player)
            if status_mult == 0:
                gkp_scores[player.player_id] = 0.0
                continue
            if has_usage_sample:
                start_share = min(1.0, player.starts / inferred_team_matches)
                minute_share = min(1.0, player.minutes / (90.0 * inferred_team_matches))
                score = 0.75 * start_share + 0.25 * minute_share
                score += 0.04 * self._role_prior(player)
            else:
                score = self._role_prior(player)
            gkp_scores[player.player_id] = max(0.001, score * status_mult)

        gkp_probs = self._normalise_probabilities(gkp_scores, 1.0, cap=0.98)

        outfield_scores: Dict[int, float] = {}
        for player in outfielders:
            status_mult = self._status_multiplier(player)
            if status_mult == 0:
                outfield_scores[player.player_id] = 0.0
                continue

            prior = self._role_prior(player)
            if has_usage_sample:
                start_share = min(1.0, player.starts / inferred_team_matches)
                minute_share = min(1.0, player.minutes / (90.0 * inferred_team_matches))
                observed = 0.65 * start_share + 0.35 * minute_share
                evidence = min(0.88, inferred_team_matches / 8.0)
                role_score = evidence * observed + (1.0 - evidence) * prior
            else:
                role_score = prior
            outfield_scores[player.player_id] = max(0.001, role_score * status_mult)

        target_outfield = min(10.0, float(sum(value > 0 for value in outfield_scores.values())))
        outfield_probs = self._normalise_probabilities(outfield_scores, target_outfield, cap=0.97)

        reconciled: Dict[int, Dict[str, float]] = {}
        for player in team_players:
            if player.position == Position.GKP:
                chance_start = gkp_probs.get(player.player_id, 0.0)
                chance_sub = min(0.03, max(0.0, 1.0 - chance_start) * 0.03) * self._status_multiplier(player)
                minutes_if_start = 90.0
                minutes_if_sub = 10.0
            else:
                chance_start = outfield_probs.get(player.player_id, 0.0)
                substitution_share = 0.30 if chance_start < 0.55 else 0.12
                chance_sub = min(0.35, max(0.0, 1.0 - chance_start) * substitution_share)
                chance_sub *= self._status_multiplier(player)
                minutes_if_start = 84.0 if player.position == Position.DEF else 78.0
                if player.minutes and player.starts:
                    observed_start_minutes = player.minutes / max(1, player.starts)
                    minutes_if_start = min(90.0, max(62.0, observed_start_minutes))
                minutes_if_sub = 21.0

            expected_minutes = chance_start * minutes_if_start + chance_sub * minutes_if_sub
            reconciled[player.player_id] = {
                "start_probability": round(chance_start, 3),
                "appearance_probability": round(min(1.0, chance_start + chance_sub), 3),
                "sub_probability": round(chance_sub, 3),
                "expected_minutes": round(min(90.0, max(0.0, expected_minutes)), 1),
            }

        return reconciled
