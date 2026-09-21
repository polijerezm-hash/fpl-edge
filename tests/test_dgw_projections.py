import pytest
from core.projections.engine import ProjectionEngine
from core.data.models import Player, Team, Fixture, Position

def test_blank_gameweek_projection():
    engine = ProjectionEngine()
    player = Player(
        player_id=1, first_name="Erling", second_name="Haaland", web_name="Haaland",
        team_id=10, position=Position.FWD, current_price=15.0, selected_by_pct=60.0
    )
    p_team = Team(team_id=10, name="Man City", short_name="MCI")

    # 0 fixtures in GW
    proj = engine.calculate_gameweek_projection(
        player=player,
        player_team=p_team,
        fixtures_info=[],
        gameweek=5
    )
    assert proj.fixtures_count == 0
    assert proj.mean_xp == 0.0
    assert proj.xmins == 0.0

def test_single_gameweek_projection():
    engine = ProjectionEngine()
    player = Player(
        player_id=1, first_name="Erling", second_name="Haaland", web_name="Haaland",
        team_id=10, position=Position.FWD, current_price=15.0, selected_by_pct=60.0
    )
    p_team = Team(team_id=10, name="Man City", short_name="MCI")
    opp_team = Team(team_id=8, name="Fulham", short_name="FUL")
    fix = Fixture(fixture_id=101, gameweek=5, home_team_id=10, away_team_id=8, kickoff_time="2024-09-21T14:00:00Z")

    proj = engine.calculate_gameweek_projection(
        player=player,
        player_team=p_team,
        fixtures_info=[(opp_team, fix, True)],
        gameweek=5
    )
    assert proj.fixtures_count == 1
    assert proj.mean_xp > 5.0
    assert len(proj.fixture_ids) == 1

def test_double_gameweek_accumulation():
    """Ensure DGW accumulates points from both fixtures rather than dropping the second match."""
    engine = ProjectionEngine()
    player = Player(
        player_id=1, first_name="Erling", second_name="Haaland", web_name="Haaland",
        team_id=10, position=Position.FWD, current_price=15.0, selected_by_pct=60.0
    )
    p_team = Team(team_id=10, name="Man City", short_name="MCI")
    opp1 = Team(team_id=8, name="Fulham", short_name="FUL")
    fix1 = Fixture(fixture_id=101, gameweek=5, home_team_id=10, away_team_id=8, kickoff_time="2024-09-21T14:00:00Z")

    opp2 = Team(team_id=7, name="Everton", short_name="EVE")
    fix2 = Fixture(fixture_id=102, gameweek=5, home_team_id=10, away_team_id=7, kickoff_time="2024-09-24T19:45:00Z")

    proj1 = engine.calculate_projection(player, p_team, opp1, fix1, True)
    proj2 = engine.calculate_projection(player, p_team, opp2, fix2, True)

    dgw_proj = engine.calculate_gameweek_projection(
        player=player,
        player_team=p_team,
        fixtures_info=[(opp1, fix1, True), (opp2, fix2, True)],
        gameweek=5
    )

    assert dgw_proj.fixtures_count == 2
    assert dgw_proj.fixture_ids == [101, 102]
    # DGW mean xP must equal the sum of both fixtures
    expected_sum = round(proj1.mean_xp + proj2.mean_xp, 2)
    assert dgw_proj.mean_xp == expected_sum
    assert dgw_proj.mean_xp > proj1.mean_xp
