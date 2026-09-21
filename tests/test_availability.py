import pytest
from core.availability.engine import AvailabilityEngine
from data.demo.seed_data import DEMO_PLAYERS, DEMO_TEAMS

def test_availability_probabilities_bounds():
    engine = AvailabilityEngine()
    team = DEMO_TEAMS[0]
    for p in DEMO_PLAYERS:
        avail = engine.estimate_player_availability(p, team, is_home=True)
        assert 0.0 <= avail.chance_start <= 1.0
        assert 0.0 <= avail.chance_appearance <= 1.0

def test_team_level_reconciliation():
    engine = AvailabilityEngine()
    team = DEMO_TEAMS[0]
    ars_players = [p for p in DEMO_PLAYERS if p.team_id == team.team_id]
    
    reconciled = engine.reconcile_team_availability(ars_players, team, is_home=True)
    total_start_prob = sum(v["start_probability"] for v in reconciled.values())
    
    # Check that individual start probabilities are bounded between 0.0 and 1.0
    for pid, res in reconciled.items():
        assert 0.0 <= res["start_probability"] <= 1.0
        assert 0.0 <= res["expected_minutes"] <= 90.0

    assert total_start_prob > 0.0
