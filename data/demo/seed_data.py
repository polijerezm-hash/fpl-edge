from datetime import datetime
from typing import List, Dict, Any
from core.data.models import (
    Player, Team, Fixture, Gameweek, Position, ManagerState, SquadPlayer, Availability, Projection
)

DEMO_TEAMS: List[Team] = [
    Team(team_id=1, name="Arsenal", short_name="ARS", strength_attack_home=1.30, strength_attack_away=1.20, strength_defence_home=1.35, strength_defence_away=1.25),
    Team(team_id=2, name="Aston Villa", short_name="AVL", strength_attack_home=1.15, strength_attack_away=1.05, strength_defence_home=1.10, strength_defence_away=0.95),
    Team(team_id=3, name="Brentford", short_name="BRE", strength_attack_home=1.05, strength_attack_away=0.95, strength_defence_home=0.95, strength_defence_away=0.85),
    Team(team_id=4, name="Brighton", short_name="BHA", strength_attack_home=1.10, strength_attack_away=1.00, strength_defence_home=1.00, strength_defence_away=0.90),
    Team(team_id=5, name="Chelsea", short_name="CHE", strength_attack_home=1.20, strength_attack_away=1.10, strength_defence_home=1.10, strength_defence_away=1.00),
    Team(team_id=6, name="Crystal Palace", short_name="CRY", strength_attack_home=1.00, strength_attack_away=0.90, strength_defence_home=1.05, strength_defence_away=0.95),
    Team(team_id=7, name="Everton", short_name="EVE", strength_attack_home=0.90, strength_attack_away=0.85, strength_defence_home=1.05, strength_defence_away=0.95),
    Team(team_id=8, name="Fulham", short_name="FUL", strength_attack_home=1.05, strength_attack_away=0.90, strength_defence_home=1.00, strength_defence_away=0.90),
    Team(team_id=9, name="Liverpool", short_name="LIV", strength_attack_home=1.35, strength_attack_away=1.25, strength_defence_home=1.25, strength_defence_away=1.15),
    Team(team_id=10, name="Man City", short_name="MCI", strength_attack_home=1.40, strength_attack_away=1.30, strength_defence_home=1.30, strength_defence_away=1.20),
    Team(team_id=11, name="Man Utd", short_name="MUN", strength_attack_home=1.10, strength_attack_away=1.00, strength_defence_home=1.00, strength_defence_away=0.90),
    Team(team_id=12, name="Newcastle", short_name="NEW", strength_attack_home=1.20, strength_attack_away=1.05, strength_defence_home=1.15, strength_defence_away=1.00),
    Team(team_id=13, name="Nott'm Forest", short_name="NFO", strength_attack_home=0.95, strength_attack_away=0.85, strength_defence_home=1.05, strength_defence_away=0.95),
    Team(team_id=14, name="Spurs", short_name="TOT", strength_attack_home=1.20, strength_attack_away=1.10, strength_defence_home=1.00, strength_defence_away=0.90),
    Team(team_id=15, name="West Ham", short_name="WHU", strength_attack_home=1.05, strength_attack_away=0.95, strength_defence_home=0.95, strength_defence_away=0.85),
    Team(team_id=16, name="Wolves", short_name="WOL", strength_attack_home=0.95, strength_attack_away=0.85, strength_defence_home=0.90, strength_defence_away=0.80),
]

DEMO_PLAYERS: List[Player] = [
    # GKP
    Player(player_id=101, first_name="David", second_name="Raya", web_name="Raya", team_id=1, position=Position.GKP, current_price=5.5, selected_by_pct=32.4, status="a"),
    Player(player_id=102, first_name="Jordan", second_name="Pickford", web_name="Pickford", team_id=7, position=Position.GKP, current_price=4.8, selected_by_pct=14.2, status="a"),
    Player(player_id=103, first_name="Mark", second_name="Flekken", web_name="Flekken", team_id=3, position=Position.GKP, current_price=4.5, selected_by_pct=8.5, status="a"),
    
    # DEF
    Player(player_id=201, first_name="Gabriel", second_name="Magalhães", web_name="Gabriel", team_id=1, position=Position.DEF, current_price=6.1, selected_by_pct=38.9, status="a"),
    Player(player_id=202, first_name="William", second_name="Saliba", web_name="Saliba", team_id=1, position=Position.DEF, current_price=6.0, selected_by_pct=34.1, status="a"),
    Player(player_id=203, first_name="Trent", second_name="Alexander-Arnold", web_name="Alexander-Arnold", team_id=9, position=Position.DEF, current_price=7.0, selected_by_pct=28.5, status="a"),
    Player(player_id=204, first_name="Josko", second_name="Gvardiol", web_name="Gvardiol", team_id=10, position=Position.DEF, current_price=6.0, selected_by_pct=25.2, status="a"),
    Player(player_id=205, first_name="Pedro", second_name="Porro", web_name="Porro", team_id=14, position=Position.DEF, current_price=5.5, selected_by_pct=19.4, status="a"),
    Player(player_id=206, first_name="Ezri", second_name="Konsa", web_name="Konsa", team_id=2, position=Position.DEF, current_price=4.5, selected_by_pct=12.1, status="a"),
    Player(player_id=207, first_name="Antonee", second_name="Robinson", web_name="Robinson", team_id=8, position=Position.DEF, current_price=4.7, selected_by_pct=15.8, status="a"),
    Player(player_id=208, first_name="Nathan", second_name="Collins", web_name="Collins", team_id=3, position=Position.DEF, current_price=4.5, selected_by_pct=6.2, status="a"),
    Player(player_id=209, first_name="Ola", second_name="Aina", web_name="Aina", team_id=13, position=Position.DEF, current_price=4.5, selected_by_pct=7.9, status="a"),

    # MID
    Player(player_id=301, first_name="Mohamed", second_name="Salah", web_name="Salah", team_id=9, position=Position.MID, current_price=12.8, selected_by_pct=45.2, status="a"),
    Player(player_id=302, first_name="Bukayo", second_name="Saka", web_name="Saka", team_id=1, position=Position.MID, current_price=10.1, selected_by_pct=42.0, status="a"),
    Player(player_id=303, first_name="Cole", second_name="Palmer", web_name="Palmer", team_id=5, position=Position.MID, current_price=10.8, selected_by_pct=51.5, status="a"),
    Player(player_id=304, first_name="Bryan", second_name="Mbeumo", web_name="Mbeumo", team_id=3, position=Position.MID, current_price=7.8, selected_by_pct=36.4, status="a"),
    Player(player_id=305, first_name="Morgan", second_name="Rogers", web_name="Rogers", team_id=2, position=Position.MID, current_price=5.4, selected_by_pct=22.8, status="a"),
    Player(player_id=306, first_name="Antoine", second_name="Semenyo", web_name="Semenyo", team_id=4, position=Position.MID, current_price=5.7, selected_by_pct=18.1, status="a"),
    Player(player_id=307, first_name="Emile", second_name="Smith Rowe", web_name="Smith Rowe", team_id=8, position=Position.MID, current_price=5.7, selected_by_pct=24.6, status="a"),
    Player(player_id=308, first_name="Bruno", second_name="Fernandes", web_name="Fernandes", team_id=11, position=Position.MID, current_price=8.2, selected_by_pct=14.5, status="a"),
    Player(player_id=309, first_name="Heung-Min", second_name="Son", web_name="Son", team_id=14, position=Position.MID, current_price=9.8, selected_by_pct=16.3, status="a"),
    Player(player_id=310, first_name="Phil", second_name="Foden", web_name="Foden", team_id=10, position=Position.MID, current_price=9.3, selected_by_pct=11.2, status="d", chance_of_playing_next_round=75, news="Knock - 75% chance of playing"),

    # FWD
    Player(player_id=401, first_name="Erling", second_name="Haaland", web_name="Haaland", team_id=10, position=Position.FWD, current_price=15.2, selected_by_pct=68.4, status="a"),
    Player(player_id=402, first_name="Ollie", second_name="Watkins", web_name="Watkins", team_id=2, position=Position.FWD, current_price=9.0, selected_by_pct=31.2, status="a"),
    Player(player_id=403, first_name="Alexander", second_name="Isak", web_name="Isak", team_id=12, position=Position.FWD, current_price=8.5, selected_by_pct=29.8, status="a"),
    Player(player_id=404, first_name="Raúl", second_name="Jiménez", web_name="Jiménez", team_id=8, position=Position.FWD, current_price=5.8, selected_by_pct=10.4, status="a"),
    Player(player_id=405, first_name="Dominic", second_name="Solanke", web_name="Solanke", team_id=14, position=Position.FWD, current_price=7.5, selected_by_pct=15.0, status="a"),
    Player(player_id=406, first_name="Chris", second_name="Wood", web_name="Wood", team_id=13, position=Position.FWD, current_price=6.5, selected_by_pct=19.7, status="a"),
]

DEMO_GAMEWEEKS: List[Gameweek] = [
    Gameweek(gameweek=5, deadline_time="2026-09-20T11:00:00Z", finished=False, is_current=True, is_next=False),
    Gameweek(gameweek=6, deadline_time="2026-09-27T11:00:00Z", finished=False, is_current=False, is_next=True),
    Gameweek(gameweek=7, deadline_time="2026-10-04T11:00:00Z", finished=False, is_current=False, is_next=False),
    Gameweek(gameweek=8, deadline_time="2026-10-18T11:00:00Z", finished=False, is_current=False, is_next=False),
    Gameweek(gameweek=9, deadline_time="2026-10-25T11:00:00Z", finished=False, is_current=False, is_next=False),
]

DEMO_FIXTURES: List[Fixture] = [
    # GW 5
    Fixture(fixture_id=501, gameweek=5, home_team_id=1, away_team_id=10, kickoff_time="2026-09-21T15:30:00Z", difficulty_home=4, difficulty_away=4),
    Fixture(fixture_id=502, gameweek=5, home_team_id=9, away_team_id=2, kickoff_time="2026-09-21T12:30:00Z", difficulty_home=2, difficulty_away=4),
    Fixture(fixture_id=503, gameweek=5, home_team_id=5, away_team_id=8, kickoff_time="2026-09-21T15:00:00Z", difficulty_home=2, difficulty_away=4),
    Fixture(fixture_id=504, gameweek=5, home_team_id=12, away_team_id=14, kickoff_time="2026-09-21T17:30:00Z", difficulty_home=3, difficulty_away=3),
    Fixture(fixture_id=505, gameweek=5, home_team_id=3, away_team_id=7, kickoff_time="2026-09-22T14:00:00Z", difficulty_home=2, difficulty_away=3),
    
    # GW 6
    Fixture(fixture_id=601, gameweek=6, home_team_id=1, away_team_id=13, kickoff_time="2026-09-28T14:00:00Z", difficulty_home=1, difficulty_away=5),
    Fixture(fixture_id=602, gameweek=6, home_team_id=10, away_team_id=8, kickoff_time="2026-09-28T11:30:00Z", difficulty_home=1, difficulty_away=5),
    Fixture(fixture_id=603, gameweek=6, home_team_id=14, away_team_id=3, kickoff_time="2026-09-28T14:00:00Z", difficulty_home=2, difficulty_away=3),
    Fixture(fixture_id=604, gameweek=6, home_team_id=12, away_team_id=9, kickoff_time="2026-09-28T16:30:00Z", difficulty_home=4, difficulty_away=4),
    Fixture(fixture_id=605, gameweek=6, home_team_id=2, away_team_id=5, kickoff_time="2026-09-29T15:00:00Z", difficulty_home=3, difficulty_away=3),
    
    # GW 7
    Fixture(fixture_id=701, gameweek=7, home_team_id=9, away_team_id=6, kickoff_time="2026-10-05T14:00:00Z", difficulty_home=1, difficulty_away=4),
    Fixture(fixture_id=702, gameweek=7, home_team_id=1, away_team_id=15, kickoff_time="2026-10-05T14:00:00Z", difficulty_home=1, difficulty_away=4),
    Fixture(fixture_id=703, gameweek=7, home_team_id=10, away_team_id=8, kickoff_time="2026-10-05T14:00:00Z", difficulty_home=1, difficulty_away=5),

    # GW 8
    Fixture(fixture_id=801, gameweek=8, home_team_id=1, away_team_id=2, kickoff_time="2026-10-19T14:00:00Z", difficulty_home=2, difficulty_away=4),
    Fixture(fixture_id=802, gameweek=8, home_team_id=9, away_team_id=5, kickoff_time="2026-10-19T16:30:00Z", difficulty_home=3, difficulty_away=4),

    # GW 9
    Fixture(fixture_id=901, gameweek=9, home_team_id=1, away_team_id=9, kickoff_time="2026-10-26T16:30:00Z", difficulty_home=4, difficulty_away=4),
    Fixture(fixture_id=902, gameweek=9, home_team_id=10, away_team_id=14, kickoff_time="2026-10-26T14:00:00Z", difficulty_home=2, difficulty_away=4),
]

DEMO_MANAGER_SQUAD: ManagerState = ManagerState(
    manager_id=99999,
    manager_name="Demo Manager",
    team_name="FPL Edge Demo XI",
    gameweek=5,
    bank=0.8,
    free_transfers=2,
    overall_points=268,
    overall_rank=42150,
    squad=[
        # Starting 11 (1 GKP, 3 DEF, 5 MID, 2 FWD)
        SquadPlayer(player_id=101, position=Position.GKP, purchase_price=5.5, selling_price=5.5, starting=True, multiplier=1),
        SquadPlayer(player_id=201, position=Position.DEF, purchase_price=6.0, selling_price=6.1, starting=True, multiplier=1),
        SquadPlayer(player_id=203, position=Position.DEF, purchase_price=7.0, selling_price=7.0, starting=True, multiplier=1),
        SquadPlayer(player_id=204, position=Position.DEF, purchase_price=6.0, selling_price=6.0, starting=True, multiplier=1),
        SquadPlayer(player_id=301, position=Position.MID, purchase_price=12.5, selling_price=12.7, starting=True, captain=True, multiplier=2), # Salah Captain
        SquadPlayer(player_id=302, position=Position.MID, purchase_price=10.0, selling_price=10.1, starting=True, vice_captain=True, multiplier=1), # Saka VC
        SquadPlayer(player_id=303, position=Position.MID, purchase_price=10.5, selling_price=10.7, starting=True, multiplier=1),
        SquadPlayer(player_id=304, position=Position.MID, purchase_price=7.5, selling_price=7.7, starting=True, multiplier=1),
        SquadPlayer(player_id=305, position=Position.MID, purchase_price=5.0, selling_price=5.2, starting=True, multiplier=1),
        SquadPlayer(player_id=401, position=Position.FWD, purchase_price=15.0, selling_price=15.1, starting=True, multiplier=1), # Haaland
        SquadPlayer(player_id=402, position=Position.FWD, purchase_price=9.0, selling_price=9.0, starting=True, multiplier=1), # Watkins
        
        # Bench (1 GKP, 2 DEF, 1 FWD)
        SquadPlayer(player_id=102, position=Position.GKP, purchase_price=4.8, selling_price=4.8, starting=False, multiplier=0), # Pickford
        SquadPlayer(player_id=206, position=Position.DEF, purchase_price=4.5, selling_price=4.5, starting=False, multiplier=0), # Konsa
        SquadPlayer(player_id=207, position=Position.DEF, purchase_price=4.6, selling_price=4.7, starting=False, multiplier=0), # Robinson
        SquadPlayer(player_id=404, position=Position.FWD, purchase_price=5.7, selling_price=5.8, starting=False, multiplier=0), # Jiménez
    ]
)
