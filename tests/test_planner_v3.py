from unittest.mock import Mock, patch

import pytest

from core.data.models import ManagerState, Player, Position, Projection, SquadPlayer
from core.data.providers import calculate_selling_price, reconstruct_free_transfers
from core.data.repository import DataRepository
from core.integrations.ai_connectors import ExternalDataConnector, FPLAdvisorAI
from core.optimizer.solver import OptimizationEngine
from core.projections.engine import ProjectionEngine


def make_projection(player_id: int, gw: int, xp: float) -> Projection:
    return Projection(
        player_id=player_id,
        gameweek=gw,
        as_of_timestamp="test",
        xmins=80,
        start_probability=0.9,
        mean_xp=xp,
        p10_xp=max(0, xp - 2),
        p50_xp=xp,
        p90_xp=xp + 3,
    )


def synthetic_squad(free_transfers: int = 1):
    positions = {
        **{pid: Position.GKP for pid in (1, 2)},
        **{pid: Position.DEF for pid in range(3, 8)},
        **{pid: Position.MID for pid in range(8, 13)},
        **{pid: Position.FWD for pid in range(13, 16)},
        16: Position.MID,
    }
    players = [
        Player(
            player_id=pid,
            first_name=f"P{pid}",
            second_name="Test",
            web_name=f"P{pid}",
            team_id=6 if pid == 16 else ((pid - 1) % 6) + 1,
            position=position,
            current_price=5.0,
            selected_by_pct=5.0,
            minutes=900,
        )
        for pid, position in positions.items()
    ]
    starters = {1, 3, 4, 5, 8, 9, 10, 11, 13, 14, 15}
    squad = [
        SquadPlayer(
            player_id=pid,
            position=positions[pid],
            purchase_price=5.0,
            selling_price=5.0,
            starting=pid in starters,
            captain=pid == 8,
            vice_captain=pid == 9,
        )
        for pid in range(1, 16)
    ]
    manager = ManagerState(
        manager_id=1,
        gameweek=1,
        bank=0.0,
        free_transfers=free_transfers,
        squad=squad,
    )
    return manager, players


def projections(players, gw: int, standout: float = 1.0):
    values = {pid: 5.0 for pid in range(1, 16)}
    values.update({2: 2.0, 6: 3.0, 7: 3.0, 12: 0.0, 16: standout})
    return {player.player_id: make_projection(player.player_id, gw, values[player.player_id]) for player in players}


def solve_private(engine, manager, players, projections_by_gw, **kwargs):
    prices = {player.player_id: player.current_price for player in players}
    prices.update({sp.player_id: sp.selling_price for sp in manager.squad})
    return engine._solve_single_pass(
        manager,
        players,
        sorted(projections_by_gw),
        projections_by_gw,
        {player.player_id: player.current_price for player in players},
        prices,
        [],
        [],
        {},
        "balanced",
        **kwargs,
    )


def test_selling_price_uses_half_profit_and_full_loss():
    assert calculate_selling_price(5.0, 5.3) == 5.1
    assert calculate_selling_price(5.0, 5.4) == 5.2
    assert calculate_selling_price(5.0, 4.7) == 4.7
    assert calculate_selling_price(5.0, 5.0) == 5.0


def test_public_history_reconstructs_ft_rollover_and_preserves_it_on_chips():
    history = [
        {"event": 2, "event_transfers": 0, "event_transfers_cost": 0},
        {"event": 3, "event_transfers": 1, "event_transfers_cost": 0},
        {"event": 4, "event_transfers": 0, "event_transfers_cost": 0},
        {"event": 5, "event_transfers": 0, "event_transfers_cost": 0},
        {"event": 6, "event_transfers": 0, "event_transfers_cost": 0},
        {"event": 7, "event_transfers": 0, "event_transfers_cost": 0},
        {"event": 8, "event_transfers": 2, "event_transfers_cost": 0},
        {"event": 9, "event_transfers": 10, "event_transfers_cost": 0},
        {"event": 10, "event_transfers": 15, "event_transfers_cost": 0},
    ]
    chips = [
        {"event": 9, "name": "wildcard"},
        {"event": 10, "name": "freehit"},
    ]
    assert reconstruct_free_transfers(history, chips, through_event=7) == 5
    assert reconstruct_free_transfers(history, chips, through_event=10) == 4


def test_projection_blend_and_ewma_recency():
    blended, weights = ProjectionEngine._blend_projection_sources(10.0, 6.0, 6.0)
    assert blended == 8.0
    assert weights == {"bookie": 0.5, "ewma": 0.35, "official": 0.15}

    old_hot = [
        {"round": 1, "minutes": 90, "expected_goals": 1.0},
        {"round": 6, "minutes": 90, "expected_goals": 0.0},
    ]
    recent_hot = list(reversed([
        {"round": 6, "minutes": 90, "expected_goals": 1.0},
        {"round": 1, "minutes": 90, "expected_goals": 0.0},
    ]))
    old_rate = ProjectionEngine._ewma_rate(old_hot, "expected_goals", 0, 0, 0.2)
    recent_rate = ProjectionEngine._ewma_rate(recent_hot, "expected_goals", 0, 0, 0.2)
    assert recent_rate > old_rate


def test_candidate_pool_keeps_three_cheapest_active_players_per_position():
    repo = DataRepository(data_mode="demo")
    manager = repo.get_manager_state(99999)
    players = repo.get_players()
    cheap_ids = set()
    next_id = 1000
    for position in Position:
        for index in range(30):
            price = 3.0 + index / 10
            players.append(
                Player(
                    player_id=next_id,
                    first_name="Budget",
                    second_name=str(next_id),
                    web_name=str(next_id),
                    team_id=(index % 16) + 1,
                    position=position,
                    current_price=price,
                    selected_by_pct=0.1,
                )
            )
            if index < 3:
                cheap_ids.add(next_id)
            next_id += 1

    engine = OptimizationEngine()
    pool = engine._candidate_pool(players, manager, {}, [5], [], [])
    assert cheap_ids.issubset({player.player_id for player in pool})


def test_free_transfers_roll_exactly_to_five_and_free_moves_have_no_fake_cost():
    manager, players = synthetic_squad(free_transfers=4)
    engine = OptimizationEngine(
        {"terminal_ft_value": 0.0, "minimum_action_edge": 0.0, "time_decay": 1.0}
    )
    hold = solve_private(
        engine,
        manager,
        players,
        {1: projections(players, 1), 2: projections(players, 2)},
        force_transfers_limit=0,
        allow_chips=False,
    )
    assert hold["gameweeks"][0]["next_free_transfers"] == 5
    assert hold["gameweeks"][1]["free_transfers"] == 5
    assert hold["gameweeks"][1]["next_free_transfers"] == 5

    manager.free_transfers = 1
    result = engine.optimize_squad(
        manager,
        players,
        [],
        {1: projections(players, 1, standout=1.0)},
        horizon=1,
        top_n_plans=1,
        allow_chips=False,
    )
    step = result["plans"][0]["gameweeks"][0]
    assert step["transfers_in"] == [16]
    assert step["transfers_out"] == [12]
    assert step["hits"] == 0

    demo_repo = DataRepository(data_mode="demo")
    demo_manager = demo_repo.get_manager_state(99999)
    demo_manager.free_transfers = 1
    demo_players = demo_repo.get_players()
    forced_hits = solve_private(
        engine,
        demo_manager,
        demo_players,
        {5: {
            player.player_id: make_projection(player.player_id, 5, 5.0)
            for player in demo_players
        }},
        force_transfers_limit=3,
        allow_chips=False,
    )
    assert forced_hits["gameweeks"][0]["hits"] == 2


def test_free_hit_reverts_and_preserves_saved_transfers():
    manager, players = synthetic_squad(free_transfers=4)
    engine = OptimizationEngine(
        {
            "terminal_ft_value": 0.0,
            "time_decay": 1.0,
            "chip_reserve_values": {name: 0.0 for name in OptimizationEngine.CHIP_NAMES},
        }
    )
    plan = solve_private(
        engine,
        manager,
        players,
        {1: projections(players, 1, standout=20.0), 2: projections(players, 2, standout=0.0)},
        allow_chips=True,
        forced_chip="free_hit",
    )
    first, second = plan["gameweeks"]
    assert first["chip"] == "free_hit"
    assert first["free_hit_transfers_in"] == [16]
    assert set(first["persistent_squad"]) == set(range(1, 16))
    assert 16 not in second["persistent_squad"]
    assert first["next_free_transfers"] == 4
    assert second["free_transfers"] == 4


@pytest.mark.parametrize("forced_chip", ["bench_boost", "triple_captain"])
def test_chip_points_are_applied_natively(forced_chip):
    manager, players = synthetic_squad()
    engine = OptimizationEngine(
        {
            "terminal_ft_value": 0.0,
            "time_decay": 1.0,
            "chip_reserve_values": {name: 0.0 for name in OptimizationEngine.CHIP_NAMES},
        }
    )
    by_gw = {1: projections(players, 1)}
    plan = solve_private(
        engine,
        manager,
        players,
        by_gw,
        force_transfers_limit=0,
        allow_chips=True,
        forced_chip=forced_chip,
    )
    step = plan["gameweeks"][0]
    projection_map = by_gw[1]
    expected = sum(projection_map[pid].mean_xp for pid in step["starters"])
    expected += sum(projection_map[pid].mean_xp for pid in step["bench"])
    expected += projection_map[step["captain"]].mean_xp
    if forced_chip == "triple_captain":
        # The bench is not fully counted without Bench Boost.
        weights = engine.rules["bench_slot_weights"]
        expected -= sum(
            (1 - weights[slot]) * projection_map[pid].mean_xp
            for slot, pid in enumerate(step["bench"])
        )
        expected += projection_map[step["captain"]].mean_xp
    assert step["chip"] == forced_chip
    assert step["expected_points"] == pytest.approx(expected)


def test_connectors_degrade_safely_and_use_responses_api():
    connector = ExternalDataConnector(api_key="")
    assert connector.fetch_epl_probabilities() == {
        "configured": False,
        "events": [],
        "players": {},
        "teams": {},
    }
    event_snapshot = {
        "events": [{
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "clean_sheet_probability": {"arsenal": 0.42},
            "player_goal_probability": {"bukayosaka": 0.36},
            "player_assist_probability": {"bukayosaka": 0.27},
        }],
        "players": {},
        "teams": {},
    }
    assert connector.inputs_for_player(
        "Bukayo Saka", "Arsenal", event_snapshot, opponent_name="Chelsea"
    ) == {
        "clean_sheet_probability": 0.42,
        "goal_probability": 0.36,
        "assist_probability": 0.27,
    }
    assert connector.inputs_for_player(
        "Bukayo Saka", "Arsenal", event_snapshot, opponent_name="Liverpool"
    ) == {}

    fake_response = Mock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {"output_text": "Grounded answer"}
    with patch("core.integrations.ai_connectors.requests.post", return_value=fake_response) as post:
        advisor = FPLAdvisorAI(api_key="test-key")
        assert advisor.explain({"plan": "ROLL"}) == "Grounded answer"
        request = post.call_args
        assert request.args[0].endswith("/v1/responses")
        assert request.kwargs["json"]["model"] == "gpt-5.4-mini"
