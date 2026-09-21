import pytest
from unittest.mock import patch, MagicMock
import requests

from core.data.providers import FplOfficialProvider, DemoProvider
from core.data.repository import DataRepository
from core.data.errors import (
    LiveDataUnavailableError, InvalidTeamIdError, CurrentSquadInvalidError
)
from core.data.models import SquadPlayer, Position

def test_live_provider_has_no_demo_data_fallback():
    """Verify FplOfficialProvider raises LiveDataUnavailableError when request fails instead of returning demo data."""
    provider = FplOfficialProvider()
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Network down")
        
        with pytest.raises(LiveDataUnavailableError) as exc_info:
            provider.get_players()
        assert exc_info.value.code == "LIVE_DATA_UNAVAILABLE"

        with pytest.raises(LiveDataUnavailableError):
            provider.get_teams()

        with pytest.raises(LiveDataUnavailableError):
            provider.get_gameweeks()

        with pytest.raises(LiveDataUnavailableError):
            provider.get_fixtures()

def test_live_provider_rejects_demo_manager_sentinel():
    """In live mode, manager_id 99999 must raise InvalidTeamIdError."""
    provider = FplOfficialProvider()
    with pytest.raises(InvalidTeamIdError) as exc_info:
        provider.get_manager_state(99999)
    assert "reserved for Demo Mode" in str(exc_info.value)

def test_demo_and_live_repositories_are_isolated():
    """Live and Demo repositories must be completely independent."""
    demo_repo = DataRepository(data_mode="demo")
    assert demo_repo.data_mode == "demo"
    assert demo_repo.current_snapshot.data_mode == "demo"
    assert demo_repo.current_snapshot.source == "demo_seed"

    # Alexander-Arnold (id=203) exists ONLY in demo seed
    p_demo = demo_repo.get_player_by_id(203)
    assert p_demo is not None
    assert "Alexander-Arnold" in p_demo.web_name

def test_squad_validation_rejects_obsolete_player_ids():
    """A squad with players not present in active snapshot is rejected."""
    repo = DataRepository(data_mode="demo")
    players_dict = {p.player_id: p for p in repo.get_players()}
    
    # Take a valid squad and corrupt one player ID to 999999 (obsolete ID)
    mgr = repo.get_manager_state(99999)
    corrupted_squad = [sp.model_copy() for sp in mgr.squad]
    corrupted_squad[0].player_id = 999999

    from core.data.validators import LiveDataValidator
    is_valid, errors = LiveDataValidator.validate_squad_against_snapshot(
        corrupted_squad, players_dict, data_mode="demo"
    )
    assert not is_valid
    assert any("999999" in err for err in errors)
