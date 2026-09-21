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
from core.projections.engine import ProjectionEngine
from core.optimizer.solver import OptimizationEngine
from core.strategy.engine import StrategyEngine
from core.explanation.engine import GroundedExplainerEngine
from core.evaluation.engine import EvaluationEngine

app = FastAPI(
    title="FPL Edge API",
    description="Deterministic Decision-Support API for Fantasy Premier League",
    version="1.0.0"
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

def get_repo(data_mode: str = "live") -> DataRepository:
    mode = "demo" if data_mode.lower() == "demo" else "live"
    if mode not in _repositories:
        _repositories[mode] = DataRepository(data_mode=mode)
    return _repositories[mode]

# Engines
projection_engine = ProjectionEngine()
optimizer_engine = OptimizationEngine()
strategy_engine = StrategyEngine()
explainer_engine = GroundedExplainerEngine()
evaluation_engine = EvaluationEngine()

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

    as_of = repo.get_as_of_timestamp()
    snap_id = repo.get_snapshot_id()
    projections = {}

    for p in players:
        p_team = teams_dict.get(p.team_id)
        if not p_team:
            continue
        p_fixtures = team_fixtures_map.get(p.team_id, [])
        proj = projection_engine.calculate_gameweek_projection(
            player=p,
            player_team=p_team,
            fixtures_info=p_fixtures,
            gameweek=gw,
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
        "version": "1.0.0",
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

    all_players = repo.get_players()
    teams = repo.get_teams()
    current_gw = repo.get_current_gameweek()

    target_gws = list(range(current_gw, current_gw + req.horizon))
    projections_by_gw = {}
    for g in target_gws:
        projections_by_gw[g] = _get_all_projections_for_gw(g, data_mode=req.data_mode)

    opt_result = optimizer_engine.optimize_squad(
        manager_state=manager_state,
        all_players=all_players,
        teams=teams,
        projections_by_gw=projections_by_gw,
        horizon=req.horizon,
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
    opt_result["model_version"] = "1.0.0"
    return opt_result

@app.post("/api/captaincy")
def get_captaincy_picks(manager_id: int = Query(1), data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    manager_state = repo.get_manager_state(manager_id)
    current_gw = repo.get_current_gameweek()
    projections = _get_all_projections_for_gw(current_gw, data_mode=data_mode)
    players_dict = {p.player_id: p for p in repo.get_players()}

    starting_xi = [sp.player_id for sp in manager_state.squad if sp.starting]
    return strategy_engine.get_captain_recommendations(
        starting_xi_pids=starting_xi,
        projections=projections,
        players_dict=players_dict
    )

@app.post("/api/chips/analyse")
def analyze_chips(manager_id: int = Query(1), data_mode: str = Query("live")):
    repo = get_repo(data_mode)
    manager_state = repo.get_manager_state(manager_id)
    current_gw = repo.get_current_gameweek()
    
    projections_by_gw = {}
    for g in range(current_gw, current_gw + 5):
        projections_by_gw[g] = _get_all_projections_for_gw(g, data_mode=data_mode)

    return strategy_engine.analyze_chips(
        manager_state=manager_state,
        projections_by_gw=projections_by_gw,
        fixtures_by_gw={}
    )

@app.post("/api/assistant")
def ask_assistant(req: AssistantRequest):
    repo = get_repo(req.data_mode)
    manager_state = repo.get_manager_state(req.manager_id)
    all_players = repo.get_players()
    teams = repo.get_teams()
    current_gw = repo.get_current_gameweek()

    projections_by_gw = {current_gw: _get_all_projections_for_gw(current_gw, data_mode=req.data_mode)}
    
    opt_result = optimizer_engine.optimize_squad(
        manager_state=manager_state,
        all_players=all_players,
        teams=teams,
        projections_by_gw=projections_by_gw,
        horizon=1,
        top_n_plans=3,
        free_transfers_override=manager_state.free_transfers
    )

    plans = opt_result.get("plans", [])
    rec_plan = plans[req.plan_index] if len(plans) > req.plan_index else (plans[0] if plans else {})
    alt_plans = [p for i, p in enumerate(plans) if i != req.plan_index]

    player_lookup = {str(p.player_id): p.model_dump() for p in all_players}

    # Build DECISION_CONTEXT
    decision_ctx = explainer_engine.build_decision_context(
        manager_state=manager_state.model_dump(),
        recommendation_plan=rec_plan,
        alternative_plans=alt_plans,
        player_lookup=player_lookup,
        as_of_timestamp=repo.get_as_of_timestamp()
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

