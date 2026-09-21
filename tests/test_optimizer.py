import pytest
from core.optimizer.solver import OptimizationEngine
from core.data.repository import DataRepository
from services.api.main import _get_all_projections_for_gw

def test_milp_optimizer_top_plans():
    repo = DataRepository(data_mode="demo")
    manager_state = repo.get_manager_state(99999)
    all_players = repo.get_players()
    teams = repo.get_teams()
    
    projections_by_gw = {
        5: _get_all_projections_for_gw(5, data_mode="demo"),
        6: _get_all_projections_for_gw(6, data_mode="demo"),
        7: _get_all_projections_for_gw(7, data_mode="demo")
    }

    opt_engine = OptimizationEngine()
    result = opt_engine.optimize_squad(
        manager_state=manager_state,
        all_players=all_players,
        teams=teams,
        projections_by_gw=projections_by_gw,
        horizon=3,
        top_n_plans=5
    )

    plans = result["plans"]
    assert len(plans) == 5
    assert result["baseline_xp"] > 0.0

    for plan in plans:
        assert plan["expected_points"] >= result["baseline_xp"] - 1.0
        assert plan["final_bank"] >= 0.0
        assert len(plan["gameweeks"]) == 3
