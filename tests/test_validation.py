import pytest
from core.data.validators import LiveDataValidator
from core.data.repository import DataRepository
from core.data.models import Position, SquadPlayer

def test_validate_snapshot_integrity_demo():
    repo = DataRepository(data_mode="demo")
    is_valid, errors = LiveDataValidator.validate_snapshot_integrity(
        repo.get_players(),
        repo.get_teams(),
        repo.get_fixtures(),
        repo.get_gameweeks(),
        data_mode="demo"
    )
    assert is_valid
    assert len(errors) == 0

def test_validate_squad_composition_checks():
    repo = DataRepository(data_mode="demo")
    players_dict = {p.player_id: p for p in repo.get_players()}
    mgr = repo.get_manager_state(99999)

    # Valid squad
    is_valid, errors = LiveDataValidator.validate_squad_against_snapshot(mgr.squad, players_dict, "demo")
    assert is_valid

    # Corrupt: 14 players
    is_valid, errors = LiveDataValidator.validate_squad_against_snapshot(mgr.squad[:14], players_dict, "demo")
    assert not is_valid
    assert any("15 players" in err for err in errors)

    # Corrupt: No captain
    corrupted = [sp.model_copy() for sp in mgr.squad]
    for sp in corrupted:
        sp.captain = False
    is_valid, errors = LiveDataValidator.validate_squad_against_snapshot(corrupted, players_dict, "demo")
    assert not is_valid
    assert any("1 captain" in err for err in errors)

def test_validate_optimiser_plan_checks():
    repo = DataRepository(data_mode="demo")
    players_dict = {p.player_id: p for p in repo.get_players()}
    mgr = repo.get_manager_state(99999)
    squad_pids = [sp.player_id for sp in mgr.squad]

    starters = squad_pids[:11]
    bench = squad_pids[11:]

    valid_plan = {
        "gameweeks": [{
            "gw": 5,
            "transfers_in": [],
            "transfers_out": [],
            "starters": starters,
            "bench": bench,
            "captain": starters[0],
            "vice_captain": starters[1],
            "bank": 0.8
        }]
    }

    is_valid, errors = LiveDataValidator.validate_optimiser_plan(
        valid_plan, players_dict, squad_pids, initial_bank=0.8
    )
    assert is_valid

    # Invalid plan: transfer in player that does not exist
    invalid_plan = {
        "gameweeks": [{
            "gw": 5,
            "transfers_in": [888888],
            "transfers_out": [squad_pids[0]],
            "starters": [888888] + starters[1:],
            "bench": bench,
            "captain": starters[1],
            "vice_captain": starters[2],
            "bank": 0.5
        }]
    }
    is_valid, errors = LiveDataValidator.validate_optimiser_plan(
        invalid_plan, players_dict, squad_pids, initial_bank=0.8
    )
    assert not is_valid
    assert any("888888" in err for err in errors)
