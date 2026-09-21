import pytest
from core.data.models import Position, ManagerState, SquadPlayer, Player
from data.demo.seed_data import DEMO_MANAGER_SQUAD, DEMO_PLAYERS

def test_demo_squad_composition():
    squad = DEMO_MANAGER_SQUAD.squad
    assert len(squad) == 15

    gkps = [sp for sp in squad if sp.position == Position.GKP]
    defs = [sp for sp in squad if sp.position == Position.DEF]
    mids = [sp for sp in squad if sp.position == Position.MID]
    fwds = [sp for sp in squad if sp.position == Position.FWD]

    assert len(gkps) == 2
    assert len(defs) == 5
    assert len(mids) == 5
    assert len(fwds) == 3

def test_demo_starting_xi_formation():
    squad = DEMO_MANAGER_SQUAD.squad
    starters = [sp for sp in squad if sp.starting]
    assert len(starters) == 11

    gkp = [sp for sp in starters if sp.position == Position.GKP]
    defs = [sp for sp in starters if sp.position == Position.DEF]
    mids = [sp for sp in starters if sp.position == Position.MID]
    fwds = [sp for sp in starters if sp.position == Position.FWD]

    assert len(gkp) == 1
    assert 3 <= len(defs) <= 5
    assert 2 <= len(mids) <= 5
    assert 1 <= len(fwds) <= 3

def test_captaincy_assignment():
    squad = DEMO_MANAGER_SQUAD.squad
    captains = [sp for sp in squad if sp.captain]
    vcaptains = [sp for sp in squad if sp.vice_captain]

    assert len(captains) == 1
    assert len(vcaptains) == 1
    assert captains[0].player_id != vcaptains[0].player_id
    assert captains[0].starting is True
    assert vcaptains[0].starting is True
