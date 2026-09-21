#!/usr/bin/env python3
"""
FPL Edge — Live Data Smoke Test Script
Executes an end-to-end verification of the live official FPL data pipeline:
Provider -> Repository -> Validation Gate -> Manager Squad Import -> Projections -> MILP Optimiser -> Recommendation Validation.

Usage:
    python scripts/live_smoke_test.py --team-id <TEAM_ID>
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import Dict, Any

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.data.repository import DataRepository
from core.data.validators import LiveDataValidator
from core.projections.engine import ProjectionEngine
from core.optimizer.solver import OptimizationEngine
from core.explanation.engine import GroundedExplainerEngine
from core.data.errors import FplEdgeError

def run_live_smoke_test(team_id: int):
    print("================================================================")
    print("         FPL EDGE — LIVE PRODUCTION SMOKE TEST                  ")
    print("================================================================")
    print(f"Target Team ID: {team_id}")
    print("Data Mode:      LIVE (Strict Official FPL API)")
    print("----------------------------------------------------------------\n")

    t_start = time.time()

    # 1. Ingestion & Snapshot Governance
    print("[1/6] Ingesting Live Data Snapshot from Official FPL...")
    repo = DataRepository(data_mode="live")
    snapshot = repo.current_snapshot

    print(f"  ✓ Snapshot ID:        {snapshot.snapshot_id}")
    print(f"  ✓ Season:             {snapshot.season}")
    print(f"  ✓ Active Gameweek:    GW {snapshot.gameweek}")
    print(f"  ✓ Source:             {snapshot.source}")
    print(f"  ✓ Timestamp:          {snapshot.as_of_timestamp}")
    print(f"  ✓ Player Count:       {snapshot.players} elements")
    print(f"  ✓ Team Count:         {snapshot.teams} clubs")
    print(f"  ✓ Fixture Count:      {snapshot.fixtures} matches")
    print(f"  ✓ Deadline:           {snapshot.current_deadline}")

    if snapshot.players < 400 or snapshot.teams != 20 or snapshot.fixtures == 0:
        print("❌ FAIL: Live snapshot counts failed integrity thresholds!")
        sys.exit(1)

    # 2. Manager Squad Import
    print(f"\n[2/6] Importing Manager State for Team ID {team_id}...")
    try:
        mgr = repo.get_manager_state(team_id)
    except Exception as e:
        print(f"❌ FAIL: Manager import failed: {e}")
        sys.exit(1)

    print(f"  ✓ Manager Name:       {mgr.manager_name}")
    print(f"  ✓ Team Name:          {mgr.team_name}")
    print(f"  ✓ Bank:               £{mgr.bank}m")
    print(f"  ✓ Free Transfers:     {mgr.free_transfers} FT (Confirmed: {mgr.free_transfers_confirmed})")
    print(f"  ✓ Overall Points:     {mgr.overall_points}")
    print(f"  ✓ Overall Rank:       {mgr.overall_rank:,}")
    print(f"  ✓ Squad Size:         {len(mgr.squad)} players")

    players_dict = {p.player_id: p for p in repo.get_players()}
    teams_dict = {t.team_id: t for t in repo.get_teams()}

    print("\n  --- Imported Squad Roster ---")
    for sp in mgr.squad:
        p = players_dict[sp.player_id]
        t = teams_dict[p.team_id]
        role = "STARTER" if sp.starting else "BENCH"
        cap = " [C]" if sp.captain else (" [VC]" if sp.vice_captain else "")
        print(f"   • [{role:7}] {p.web_name:18} | {t.short_name:3} | {p.position.value:3} | £{p.current_price:.1f}m{cap}")

    # Validate imported squad
    is_valid, errors = LiveDataValidator.validate_squad_against_snapshot(mgr.squad, players_dict, "live")
    if not is_valid:
        print(f"❌ FAIL: Squad validation failed: {errors}")
        sys.exit(1)
    print("  ✓ Squad Integrity:    VALID (All 15 players belong to active official snapshot)")

    # 3. Component Projections & DGW Multi-Fixture Support
    print(f"\n[3/6] Computing Gameweek {snapshot.gameweek} Projections (with DGW aggregation)...")
    proj_engine = ProjectionEngine()
    fixtures = [f for f in repo.get_fixtures() if f.gameweek == snapshot.gameweek]
    
    team_fixtures: Dict[int, list] = {}
    for f in fixtures:
        if f.home_team_id in teams_dict and f.away_team_id in teams_dict:
            team_fixtures.setdefault(f.home_team_id, []).append((teams_dict[f.away_team_id], f, True))
            team_fixtures.setdefault(f.away_team_id, []).append((teams_dict[f.home_team_id], f, False))

    projections = {}
    for p in repo.get_players():
        p_team = teams_dict[p.team_id]
        p_fixes = team_fixtures.get(p.team_id, [])
        projections[p.player_id] = proj_engine.calculate_gameweek_projection(
            player=p,
            player_team=p_team,
            fixtures_info=p_fixes,
            gameweek=snapshot.gameweek,
            as_of_timestamp=snapshot.as_of_timestamp,
            snapshot_id=snapshot.snapshot_id
        )

    print(f"  ✓ Projections generated for {len(projections)} active players.")

    # Show top 3 starters xP
    starter_pids = [sp.player_id for sp in mgr.squad if sp.starting]
    starter_pids.sort(key=lambda pid: projections[pid].mean_xp, reverse=True)
    print("  ✓ Top Starter Projections:")
    for pid in starter_pids[:3]:
        p = players_dict[pid]
        proj = projections[pid]
        print(f"     - {p.web_name} ({p.position.value}): {proj.mean_xp:.2f} xP (xMins: {proj.xmins:.1f}, Matches: {proj.fixtures_count})")

    # 4. PuLP MILP Optimization (1-GW and 3-GW)
    print(f"\n[4/6] Running PuLP MILP Transfer Optimizer...")
    opt_engine = OptimizationEngine()
    
    # Run 1-GW horizon
    opt_res_1gw = opt_engine.optimize_squad(
        manager_state=mgr,
        all_players=repo.get_players(),
        teams=repo.get_teams(),
        projections_by_gw={snapshot.gameweek: projections},
        horizon=1,
        top_n_plans=3,
        free_transfers_override=mgr.free_transfers
    )

    print(f"  ✓ 1-GW Optimization:  Success! ({len(opt_res_1gw['plans'])} plans generated)")
    print(f"  ✓ Baseline HOLD xP:   {opt_res_1gw['baseline_xp']:.2f} xP")

    for plan in opt_res_1gw["plans"]:
        gw1 = plan["gameweeks"][0]
        tin_names = [players_dict[pid].web_name for pid in gw1["transfers_in"]]
        tout_names = [players_dict[pid].web_name for pid in gw1["transfers_out"]]
        move_str = f"Move: {', '.join(tout_names)} → {', '.join(tin_names)}" if tin_names else "Action: ROLL / HOLD TRANSFER"
        cap_name = players_dict[gw1["captain"]].web_name
        print(f"     • Plan {plan.get('plan_code', '?')}: {plan['expected_points']:.2f} xP (Gain vs HOLD: +{plan['gain_vs_hold']:.2f} xP) | {move_str} | Captain: {cap_name}")

    # 5. Post-Optimization Validation Gate
    print("\n[5/6] Validating Optimizer Plans Post-Solve...")
    for plan in opt_res_1gw["plans"]:
        is_plan_valid, plan_errs = LiveDataValidator.validate_optimiser_plan(
            plan=plan,
            players_dict=players_dict,
            initial_squad_pids=[sp.player_id for sp in mgr.squad],
            initial_bank=mgr.bank
        )
        if not is_plan_valid:
            print(f"❌ FAIL: Plan {plan.get('plan_code')} violated validation rules: {plan_errs}")
            sys.exit(1)
        
        # Verify no stale players
        gw1 = plan["gameweeks"][0]
        for pid in gw1["transfers_in"]:
            assert pid in players_dict, f"Transfer in player {pid} does not exist in snapshot!"
        print(f"  ✓ Plan {plan.get('plan_code')} passed all post-solve integrity checks.")

    # 6. Grounded Explanation Verification
    print("\n[6/6] Verifying Grounded Explanation Context...")
    explainer = GroundedExplainerEngine()
    rec_plan = opt_res_1gw["plans"][0]
    decision_ctx = explainer.build_decision_context(
        manager_state=mgr.model_dump(),
        recommendation_plan=rec_plan,
        alternative_plans=opt_res_1gw["plans"][1:],
        player_lookup={str(p.player_id): p.model_dump() for p in repo.get_players()},
        as_of_timestamp=snapshot.as_of_timestamp
    )
    explanation = explainer.explain_decision("Why is this the recommended transfer plan?", decision_ctx)
    print("  ✓ Grounded Explanation Mode:", explanation.get("mode"))
    print("  ✓ Sample Explanation Answer Summary:")
    answer_preview = "\n".join(explanation.get("answer", "").split("\n")[:4])
    print(f"     {answer_preview}")

    elapsed = round(time.time() - t_start, 2)
    print("\n================================================================")
    print(f" ✅ ALL CHECKS PASSED — LIVE PRODUCTION PIPELINE HEALTHY ({elapsed}s)")
    print("================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FPL Edge live smoke test.")
    parser.add_argument("--team-id", type=int, default=1, help="Official FPL Team/Entry ID")
    args = parser.parse_args()
    run_live_smoke_test(args.team_id)
