from core.data.models import Player, Position, Projection
from core.strategy.engine import StrategyEngine


def projection(player_id: int, mean: float, start: float = 0.9, xmins: float = 78.0) -> Projection:
    return Projection(
        player_id=player_id,
        gameweek=1,
        as_of_timestamp="",
        xmins=xmins,
        start_probability=start,
        mean_xp=mean,
        p10_xp=max(0.0, mean - 3.0),
        p50_xp=mean,
        p90_xp=mean + 4.0,
    )


def test_goalkeeper_is_never_returned_as_captain_candidate():
    players = {
        1: Player(
            player_id=1, first_name="Backup", second_name="Keeper", web_name="Keeper",
            team_id=1, position=Position.GKP, current_price=4.0, selected_by_pct=1.0,
        ),
        2: Player(
            player_id=2, first_name="Safe", second_name="Forward", web_name="Forward",
            team_id=2, position=Position.FWD, current_price=8.0, selected_by_pct=20.0,
        ),
    }
    projections = {1: projection(1, 20.0), 2: projection(2, 6.0)}

    result = StrategyEngine().get_captain_recommendations([1, 2], projections, players)

    assert result["diamond"]["player_id"] == 2
    assert all(candidate["position"] != "GKP" for candidate in result["ranked"])
    assert result["rejected"][0]["player_id"] == 1


def test_non_playing_outfielder_is_rejected():
    player = Player(
        player_id=3, first_name="Bench", second_name="Player", web_name="Bench",
        team_id=3, position=Position.MID, current_price=5.0, selected_by_pct=0.1,
    )
    result = StrategyEngine().get_captain_recommendations(
        [3], {3: projection(3, 9.0, start=0.05, xmins=8.0)}, {3: player}
    )

    assert result["diamond"] is None
    assert result["status"] == "no_eligible_outfield_captain"
