import pytest
from core.projections.engine import ProjectionEngine
from data.demo.seed_data import DEMO_PLAYERS, DEMO_TEAMS, DEMO_FIXTURES

def test_component_projection_calculation():
    engine = ProjectionEngine()
    player = DEMO_PLAYERS[0] # Raya GKP
    p_team = DEMO_TEAMS[0] # ARS
    opp_team = DEMO_TEAMS[9] # MCI
    fixture = DEMO_FIXTURES[0] # GW5

    proj = engine.calculate_projection(player, p_team, opp_team, fixture, is_home=True)
    assert proj.mean_xp >= 0.0
    assert 0.0 <= proj.xmins <= 90.0
    assert 0.0 <= proj.start_probability <= 1.0
    assert proj.p10_xp <= proj.p50_xp <= proj.p90_xp
