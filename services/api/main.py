from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.data.models import (
    Player, Team, Fixture, Gameweek, ManagerState, DataStatus, LiveDataStatus, Projection
)
from core.data.repository import DataRepository
from core.data.validators import LiveDataValidator
from core.data.errors import (
    FplEdgeError, LiveDataUnavailableError, LiveDataInvalidError,
    InvalidTeamIdError, CurrentSquadInvalidError, StaleSnapshotError,
    OptimisationFailedError, RecommendationValidationFailedError
)
from core.availability.engine import AvailabilityEngine
from core.projections.engine import ProjectionEngine
from core.optimizer.solver import OptimizationEngine
from core.strategy.engine import StrategyEngine
from core.explanation.engine import GroundedExplainerEngine
from core.evaluation.engine import EvaluationEngine
from core.integrations.ai_connectors import ExternalDataConnector

app = FastAPI(
    title="FPL Edge API",
    description="Deterministic Decision-Support API for Fantasy Premier League",
    version="3.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dedicated Repositories for logical and physical snapshot isolation
_repositories: Dict[str, DataRepository] = {}
_decision_cache: Dict[tuple, Dict[str, Any]] = {}
_captaincy_cache: Dict[tuple, Dict[str, Any]] = {}

def get_repo(data_mode: str = "live") -> DataRepository:
    mode = "demo" if data_mode.lower() == "demo" else "live"
    if mode not in _repositories:
        _repositories[mode] = DataRepository(data_mode=mode)
    return _repositories[mode]

# Engines
availability_engine = AvailabilityEngine()
projection_engine = ProjectionEngine()
optimizer_engine = OptimizationEngine()
strategy_engine = StrategyEngine()
explainer_engine = GroundedExplainerEngine()
evaluation_engine = EvaluationEngine()
external_data_connector = ExternalDataConnector()


def _history_candidate_ids(players: List[Player], manager_state: Optional[ManagerState] = None) -> List[int]:
    """Bound official history calls to the realistic solver pool plus enablers."""
    selected = {sp.player_id for sp in manager_state.squad} if manager_state else set()
    limits = {"GKP": 10, "DEF": 35, "MID": 45, "FWD": 25}
    for position, limit in limits.items():
        eligible = [
            p for p in players
            if p.position.value == position and p.can_select and p.status not in {"i", "s", "u"}
        ]
        eligible.sort(
            key=lambda p: (p.ep_next * 3.0 + p.form + 0.025 * p.total_points + 0.02 * p.selected_by_pct),
            reverse=True,
        )
        selected.update(p.player_id for p in eligible[:limit])
        selected.update(p.player_id for p in sorted(eligible, key=lambda p: p.current_price)[:3])
    return sorted(selected)


def _ensure_projection_histories(repo: DataRepository, manager_state: Optional[ManagerState] = None) -> None:
    if repo.data_mode != "live":
        return
    players = repo.get_players()
    repo.enrich_recent_histories(_history_candidate_ids(players, manager_state))

# Global Structured Exception Handlers
@app.exception_handler(LiveDataUnavailableError)
async def live_data_unavailable_handler(request: Request, exc: LiveDataUnavailableError):
    return JSONResponse(status_code=503, content=exc.to_dict())

@app.exception_handler(InvalidTeamIdError)
async def invalid_team_id_handler(request: Request, exc: InvalidTeamIdError):
    return JSONResponse(status_code=404, content=exc.to_dict())

@app.exception_handler(CurrentSquadInvalidError)
async def current_squad_invalid_handler(request: Request, exc: CurrentSquadInvalidError):
    return JSONResponse(status_code=400, content=exc.to_dict())

@app.exception_handler(LiveDataInvalidError)
async def live_data_invalid_handler(request: Request, exc: LiveDataInvalidError):
    return JSONResponse(status_code=502, content=exc.to_dict())

@app.exception_handler(RecommendationValidationFailedError)
async def rec_validation_handler(request: Request, exc: RecommendationValidationFailedError):
    return JSONResponse(status_code=500, content=exc.to_dict())

@app.exception_handler(FplEdgeError)
async def generic_fpl_error_handler(request: Request, exc: FplEdgeError):
    return JSONResponse(status_code=400, content=exc.to_dict())


# Request Schemas
class OptimizeRequest(BaseModel):
    manager_id: int = 1
    data_mode: str = "live"
    horizon: int = 3
    risk_profile: str = "balanced"  # "safe", "balanced", "aggressive"
    locked_players: List[int] = []
    banned_players: List[int] = []
    custom_overrides: Dict[int, float] = {}
    free_transfers: Optional[int] = None
    confirm_free_transfers: bool = False

class AssistantRequest(BaseModel):
    question: str
    manager_id: int = 1
    data_mode: str = "live"
    plan_index: int = 0


# Helper to build projections for all players with DGW support
def _get_all_projections_for_gw(gw: int, data_mode: str = "live") -> Dict[int, Projection]:
    repo = get_repo(data_mode)
    players = repo.get_players()
    teams_dict = {t.team_id: t for t in repo.get_teams()}
    fixtures = [f for f in repo.get_fixtures() if f.gameweek == gw]
    
    # Map multiple fixtures per team (conceptually: team_fixture_map[team_id] = [fix_1, fix_2, ...])
    team_fixtures_map: Dict[int, List[tuple]] = {}
    for f in fixtures:
        if f.home_team_id in teams_dict and f.away_team_id in teams_dict:
            team_fixtures_map.setdefault(f.home_team_id, []).append((teams_dict[f.away_team_id], f, True))
            team_fixtures_map.setdefault(f.away_team_id, []).append((teams_dict[f.home_team_id], f, False))

    # Pre-calculate team level availability reconciliation
    players_by_team: Dict[int, List[Player]] = {}
    for p in players:
        players_by_team.setdefault(p.team_id, []).append(p)

    reconciled_mins_by_team: Dict[int, Dict[int, Dict[str, float]]] = {}
    for tid, t_players in players_by_team.items():
        p_team = teams_dict.get(tid)
        if p_team:
            reconciled_mins_by_team[tid] = availability_engine.reconcile_team_availability(t_players, p_team, is_home=True)

    as_of = repo.get_as_of_timestamp()
    snap_id = repo.get_snapshot_id()
    projections = {}
    odds_snapshot = external_data_connector.fetch_epl_probabilities() if external_data_connector.configured else None

    for p in players:
        p_team = teams_dict.get(p.team_id)
        if not p_team:
            continue
        p_fixtures = team_fixtures_map.get(p.team_id, [])
        p_rec_mins = reconciled_mins_by_team.get(p.team_id, {}).get(p.player_id)
        external_by_fixture: Dict[int, Dict[str, float]] = {}
        if odds_snapshot:
            for opponent, fixture, _ in p_fixtures:
                inputs = external_data_connector.inputs_for_player(
                    player_name=f"{p.first_name} {p.second_name}".strip() or p.web_name,
                    team_name=p_team.name,
                    opponent_name=opponent.name,
                    snapshot=odds_snapshot,
                )
                if not any(key in inputs for key in ("goal_probability", "assist_probability")):
                    inputs.update(
                        external_data_connector.inputs_for_player(
                            player_name=p.web_name,
                            team_name=p_team.name,
                            opponent_name=opponent.name,
                            snapshot=odds_snapshot,
                        )
                    )
                external_by_fixture[fixture.fixture_id] = inputs
        
        proj = projection_engine.calculate_gameweek_projection(
            player=p,
            player_team=p_team,
            fixtures_info=p_fixtures,
            gameweek=gw,
            reconciled_mins=p_rec_mins,
            external_inputs_by_fixture=external_by_fixture,
            use_official_ep_next=(gw == repo.get_current_gameweek()),
            as_of_timestamp=as_of,
            snapshot_id=snap_id
        )
        projections[p.player_id] = proj

    return projections


@app.get("/api/info")
def read_api_info():
    repo = get_repo("live")
    snap = repo.current_snapshot
    return {
        "name": "FPL Edge Decision-Support API",
        "version": "3.0.0",
        "status": "operational",
        "active_snapshot": snap.model_dump()
    }

@app.get("/api/data/status", response_model=LiveDataStatus)
def get_data_status(data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    return repo.get_live_status()

@app.post("/api/data/refresh", response_model=LiveDataStatus)
def refresh_data(data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    repo.refresh_snapshots()
    return repo.get_live_status()

@app.get("/api/gameweeks", response_model=List[Gameweek])
def get_gameweeks(data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    return repo.get_gameweeks()

@app.get("/api/fixtures", response_model=List[Fixture])
def get_fixtures(gw: Optional[int] = Query(None), data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    fixtures = repo.get_fixtures()
    if gw is not None:
        return [f for f in fixtures if f.gameweek == gw]
    return fixtures

@app.get("/api/teams", response_model=List[Team])
def get_teams(data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    return repo.get_teams()

@app.get("/api/players", response_model=List[Player])
def get_players(
    position: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    data_mode: str = Query("live")
):
    repo = get_repo(data_mode)
    players = repo.get_players()
    if position:
        players = [p for p in players if p.position.value == position.upper()]
    if max_price is not None:
        players = [p for p in players if p.current_price <= max_price]
    if search:
        s = search.lower()
        players = [p for p in players if s in p.web_name.lower() or s in p.first_name.lower() or s in p.second_name.lower()]
    return players

@app.get("/api/players/{player_id}")
def get_player_detail(player_id: int, data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    _ensure_projection_histories(repo)
    player = repo.get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found in active snapshot")
    
    current_gw = repo.get_current_gameweek()
    team = repo.get_team_by_id(player.team_id)
    
    # 5-GW Projections
    gw_projections = []
    for g in range(current_gw, current_gw + 5):
        all_projs = _get_all_projections_for_gw(g, data_mode=data_mode)
        proj = all_projs.get(player_id)
        if proj:
            gw_projections.append(proj)

    return {
        "player": player,
        "team": team,
        "projections": gw_projections
    }

@app.get("/api/team/{manager_id}", response_model=ManagerState)
def get_manager_team(manager_id: int, data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    return repo.get_manager_state(manager_id)

@app.get("/api/projections")
def get_projections(gw: Optional[int] = Query(None), data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    _ensure_projection_histories(repo)
    target_gw = gw or repo.get_current_gameweek()
    projs = _get_all_projections_for_gw(target_gw, data_mode=data_mode)
    return {
        "gameweek": target_gw,
        "snapshot_id": repo.get_snapshot_id(),
        "as_of_timestamp": repo.get_as_of_timestamp(),
        "projections": list(projs.values())
    }

@app.post("/api/optimise")
def run_optimization(req: OptimizeRequest):
    repo = get_repo(req.data_mode)
    manager_state = repo.get_manager_state(req.manager_id)
    
    # User Decision Q1: Confirm Free Transfers before running optimizer
    if req.data_mode == "live" and not req.confirm_free_transfers and req.free_transfers is None:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "code": "FREE_TRANSFERS_UNCONFIRMED",
                "message": f"Free transfers ({manager_state.free_transfers} FT) must be confirmed or adjusted before running optimization.",
                "estimated_free_transfers": manager_state.free_transfers
            }
        )

    _ensure_projection_histories(repo, manager_state)
    all_players = repo.get_players()
    teams = repo.get_teams()
    current_gw = repo.get_current_gameweek()

    target_gws = sorted({
        fixture.gameweek
        for fixture in repo.get_fixtures()
        if fixture.gameweek >= current_gw
    })[: req.horizon]
    if not target_gws:
        target_gws = [current_gw]
    projections_by_gw = {}
    for g in target_gws:
        projections_by_gw[g] = _get_all_projections_for_gw(g, data_mode=req.data_mode)

    opt_result = optimizer_engine.optimize_squad(
        manager_state=manager_state,
        all_players=all_players,
        teams=teams,
        projections_by_gw=projections_by_gw,
        horizon=len(target_gws),
        risk_profile=req.risk_profile,
        locked_player_ids=req.locked_players,
        banned_player_ids=req.banned_players,
        custom_mins_overrides=req.custom_overrides,
        free_transfers_override=req.free_transfers
    )

    # Post-Optimization Validation Gate
    players_dict = {p.player_id: p for p in all_players}
    initial_squad_pids = [sp.player_id for sp in manager_state.squad]
    
    validated_plans = []
    for plan in opt_result.get("plans", []):
        is_valid, errors = LiveDataValidator.validate_optimiser_plan(
            plan=plan,
            players_dict=players_dict,
            initial_squad_pids=initial_squad_pids,
            initial_bank=manager_state.bank
        )
        if is_valid:
            validated_plans.append(plan)
        else:
            print(f"Plan {plan.get('plan_code')} rejected by validation gate: {errors}")

    if not validated_plans:
        raise RecommendationValidationFailedError(
            "All generated optimizer plans failed post-solve validation checks.",
            details={"manager_id": req.manager_id}
        )

    opt_result["plans"] = validated_plans
    opt_result["snapshot_id"] = repo.get_snapshot_id()
    opt_result["as_of_timestamp"] = repo.get_as_of_timestamp()
    opt_result["model_version"] = "3.0.0"
    _decision_cache[(req.data_mode.lower(), req.manager_id)] = opt_result
    return opt_result

@app.post("/api/captaincy")
def get_captaincy_picks(manager_id: int = Query(1), data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    manager_state = repo.get_manager_state(manager_id)
    _ensure_projection_histories(repo, manager_state)
    current_gw = repo.get_current_gameweek()
    projections = _get_all_projections_for_gw(current_gw, data_mode=data_mode)
    players_dict = {p.player_id: p for p in repo.get_players()}

    starting_xi = [sp.player_id for sp in manager_state.squad if sp.starting]
    result = strategy_engine.get_captain_recommendations(
        starting_xi_pids=starting_xi,
        projections=projections,
        players_dict=players_dict
    )
    result["gameweek"] = current_gw
    result["snapshot_id"] = repo.get_snapshot_id()
    result["model_version"] = "3.0.0"
    _captaincy_cache[(data_mode.lower(), manager_id)] = result
    return result

@app.get("/api/mini-leagues")
def get_mini_leagues(manager_id: int = Query(...), data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    return {
        "manager_id": manager_id,
        "gameweek": repo.get_current_gameweek(),
        "leagues": repo.get_manager_leagues(manager_id),
    }

@app.get("/api/mini-leagues/{league_id}/analysis")
def get_mini_league_analysis(
    league_id: int,
    manager_id: int = Query(...),
    data_mode: str = Query("live"),
):
    repo = get_repo(data_mode)
    analysis = repo.get_mini_league_analysis(manager_id, league_id)
    _ensure_projection_histories(repo)
    projections = _get_all_projections_for_gw(repo.get_current_gameweek(), data_mode=data_mode)

    for exposure in analysis.get("exposures", []):
        projection = projections.get(exposure["player_id"])
        exposure["mean_xp"] = projection.mean_xp if projection else 0.0
        exposure["xmins"] = projection.xmins if projection else 0.0
        if exposure.get("you_own"):
            exposure["edge_score"] = round(
                (100.0 * exposure.get("your_multiplier", 0) - exposure.get("league_eo", 0.0))
                * exposure["mean_xp"] / 100.0,
                2,
            )
        else:
            exposure["threat_score"] = round(
                exposure.get("league_eo", 0.0) * exposure["mean_xp"] / 100.0,
                2,
            )

    analysis["differentials"] = sorted(
        [row for row in analysis.get("exposures", []) if row.get("you_own") and row.get("league_eo", 0) < 75],
        key=lambda row: row.get("edge_score", 0),
        reverse=True,
    )[:8]
    analysis["threats"] = sorted(
        [row for row in analysis.get("exposures", []) if not row.get("you_own") and row.get("league_eo", 0) >= 15],
        key=lambda row: row.get("threat_score", 0),
        reverse=True,
    )[:8]
    analysis["snapshot_id"] = repo.get_snapshot_id()
    return analysis

@app.post("/api/chips/analyse")
def analyze_chips(manager_id: int = Query(1), data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    manager_state = repo.get_manager_state(manager_id)
    _ensure_projection_histories(repo, manager_state)
    current_gw = repo.get_current_gameweek()
    
    target_gws = sorted({
        fixture.gameweek
        for fixture in repo.get_fixtures()
        if fixture.gameweek >= current_gw
    })[:5]
    if not target_gws:
        target_gws = [current_gw]
    projections_by_gw = {}
    for g in target_gws:
        projections_by_gw[g] = _get_all_projections_for_gw(g, data_mode=data_mode)

    optimization_result = optimizer_engine.optimize_squad(
        manager_state=manager_state,
        all_players=repo.get_players(),
        teams=repo.get_teams(),
        projections_by_gw=projections_by_gw,
        horizon=len(target_gws),
        top_n_plans=1,
        free_transfers_override=manager_state.free_transfers,
        allow_chips=True,
    )

    return strategy_engine.analyze_chips(
        manager_state=manager_state,
        projections_by_gw=projections_by_gw,
        fixtures_by_gw={},
        optimization_result=optimization_result,
    )

@app.post("/api/assistant")
def ask_assistant(req: AssistantRequest):
    repo = get_repo(req.data_mode)
    manager_state = repo.get_manager_state(req.manager_id)
    _ensure_projection_histories(repo, manager_state)
    all_players = repo.get_players()
    current_gw = repo.get_current_gameweek()

    cache_key = (req.data_mode.lower(), req.manager_id)
    opt_result = _decision_cache.get(cache_key)
    if not opt_result or opt_result.get("snapshot_id") != repo.get_snapshot_id():
        projections_by_gw = {current_gw: _get_all_projections_for_gw(current_gw, data_mode=req.data_mode)}
        opt_result = optimizer_engine.optimize_squad(
            manager_state=manager_state,
            all_players=all_players,
            teams=repo.get_teams(),
            projections_by_gw=projections_by_gw,
            horizon=1,
            top_n_plans=3,
            free_transfers_override=manager_state.free_transfers
        )
        opt_result["snapshot_id"] = repo.get_snapshot_id()
        opt_result["as_of_timestamp"] = repo.get_as_of_timestamp()
        opt_result["model_version"] = "3.0.0"
        _decision_cache[cache_key] = opt_result

    plans = opt_result.get("plans", [])
    rec_plan = plans[req.plan_index] if len(plans) > req.plan_index else (plans[0] if plans else {})
    alt_plans = [p for i, p in enumerate(plans) if i != req.plan_index]

    captaincy = _captaincy_cache.get(cache_key)
    if not captaincy or captaincy.get("snapshot_id") != repo.get_snapshot_id():
        projections = _get_all_projections_for_gw(current_gw, data_mode=req.data_mode)
        players_dict = {p.player_id: p for p in all_players}
        starting_xi = [sp.player_id for sp in manager_state.squad if sp.starting]
        captaincy = strategy_engine.get_captain_recommendations(starting_xi, projections, players_dict)
        captaincy["snapshot_id"] = repo.get_snapshot_id()
        _captaincy_cache[cache_key] = captaincy

    referenced_ids = {sp.player_id for sp in manager_state.squad}
    for plan in [rec_plan, *alt_plans]:
        for step in plan.get("gameweeks", []):
            referenced_ids.update(step.get("transfers_in", []))
            referenced_ids.update(step.get("transfers_out", []))
            referenced_ids.update([step.get("captain"), step.get("vice_captain")])
    for candidate in captaincy.get("ranked", []):
        referenced_ids.add(candidate.get("player_id"))
    referenced_ids.discard(None)
    player_lookup = {
        str(p.player_id): p.model_dump()
        for p in all_players
        if p.player_id in referenced_ids
    }

    # Build DECISION_CONTEXT
    decision_ctx = explainer_engine.build_decision_context(
        manager_state=manager_state.model_dump(),
        recommendation_plan=rec_plan,
        alternative_plans=alt_plans,
        player_lookup=player_lookup,
        as_of_timestamp=repo.get_as_of_timestamp(),
        model_version="3.0.0",
        captaincy=captaincy,
    )

    return explainer_engine.explain_decision(req.question, decision_ctx)

@app.get("/api/evaluation")
def get_evaluation():
    return evaluation_engine.get_latest_evaluation()

# Static Frontend SPA Serving (Single-service deployment)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "web", "dist"))

if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = os.path.join(dist_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))
