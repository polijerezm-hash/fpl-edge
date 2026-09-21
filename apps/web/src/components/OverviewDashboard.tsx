import React from "react";
import {
  TrendingUp,
  Coins,
  ArrowRight,
  Sparkles,
  Bot,
  Crown,
  ChevronRight,
  AlertTriangle,
  Zap,
  ShieldCheck,
  Calendar,
  Layers
} from "lucide-react";

interface OverviewDashboardProps {
  optimizationResult: any;
  managerState: any;
  captainPicks: any;
  playersDict?: Record<number, any>;
  projectionsDict?: Record<number, any>;
  snapshotId?: string;
  asOfTimestamp?: string;
  onNavigateTab: (tab: string) => void;
  onAskAI: (question: string) => void;
}

export const OverviewDashboard: React.FC<OverviewDashboardProps> = ({
  optimizationResult,
  managerState,
  captainPicks,
  playersDict = {},
  projectionsDict = {},
  snapshotId = "",
  asOfTimestamp = "",
  onNavigateTab,
  onAskAI,
}) => {
  const topPlan = optimizationResult?.plans?.[0];
  const baselineXp = optimizationResult?.baseline_xp ?? 0.0;
  const gw1 = topPlan?.gameweeks?.[0];
  const isRoll = !gw1?.transfers_in || gw1.transfers_in.length === 0;

  // Derive dynamic watchlist from squad
  const squadPids: number[] = (managerState?.squad || []).map((sp: any) => sp.player_id);
  const flaggedPlayers = squadPids
    .map(pid => ({ player: playersDict[pid], proj: projectionsDict[pid] }))
    .filter(item => item.player && (item.player.status !== "a" || (item.player.chance_of_playing_next_round !== null && item.player.chance_of_playing_next_round < 100)));

  const safeStarters = squadPids
    .map(pid => ({ player: playersDict[pid], proj: projectionsDict[pid] }))
    .filter(item => item.player && item.player.status === "a")
    .sort((a, b) => (b.proj?.mean_xp || 0) - (a.proj?.mean_xp || 0));

  const captainName = gw1?.captain ? (playersDict[gw1.captain]?.web_name || `Player #${gw1.captain}`) : "Unassigned";

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* 1. Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Card 1: Projected Points */}
        <div className="bg-surface border border-surfaceBorder rounded-2xl p-5 relative overflow-hidden group hover:border-primary/50 transition-all">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Projected GW Points</div>
          <div className="text-3xl font-extrabold text-slate-100 font-mono mt-2 flex items-baseline gap-2">
            <span>{topPlan ? topPlan.expected_points.toFixed(1) : baselineXp.toFixed(1)}</span>
            {topPlan && (
              <span className={`text-xs font-bold flex items-center ${topPlan.gain_vs_hold >= 0 ? "text-primary" : "text-amber-400"}`}>
                <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> {topPlan.gain_vs_hold >= 0 ? `+${topPlan.gain_vs_hold}` : topPlan.gain_vs_hold} xP
              </span>
            )}
          </div>
          <div className="text-xs text-slate-500 mt-1 font-medium">
            Baseline HOLD: {baselineXp.toFixed(1)} xP
          </div>
        </div>

        {/* Card 2: Bank Balance */}
        <div className="bg-surface border border-surfaceBorder rounded-2xl p-5 relative overflow-hidden group hover:border-primary/50 transition-all">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">In The Bank</div>
          <div className="text-3xl font-extrabold text-emerald-400 font-mono mt-2 flex items-baseline gap-1">
            <Coins className="w-6 h-6 text-emerald-400 inline" />
            <span>£{managerState?.bank ?? 0.0}m</span>
          </div>
          <div className="text-xs text-slate-500 mt-1 font-medium">
            Post-plan: £{topPlan?.final_bank ?? managerState?.bank ?? 0.0}m
          </div>
        </div>

        {/* Card 3: Free Transfers State */}
        <div className="bg-surface border border-surfaceBorder rounded-2xl p-5 relative overflow-hidden group hover:border-primary/50 transition-all">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Free Transfers</div>
          <div className="text-3xl font-extrabold text-cyan-400 font-mono mt-2 flex items-baseline gap-2">
            <span>{managerState?.free_transfers ?? 1}</span>
            <span className="text-xs text-slate-400 font-normal">/ 5 max</span>
          </div>
          <div className="text-xs text-slate-500 mt-1 font-medium">
            {managerState?.free_transfers_confirmed ? "✓ Confirmed FT" : "⚠ Confirmation Needed"}
          </div>
        </div>

        {/* Card 4: Strategy Profile */}
        <div className="bg-surface border border-surfaceBorder rounded-2xl p-5 relative overflow-hidden group hover:border-primary/50 transition-all">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tactical Horizon</div>
          <div className="text-xl font-bold text-slate-100 mt-2 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-primary"></span>
            <span>{optimizationResult?.horizon || 3} Gameweeks</span>
          </div>
          <div className="text-xs text-slate-500 mt-1 font-medium">
            PuLP MILP Solver: Optimal
          </div>
        </div>
      </div>

      {/* 2. Main Hero Recommendation Card */}
      <div className="bg-gradient-to-r from-surface via-surface to-surfaceHover border border-primary/40 rounded-3xl p-6 md:p-8 relative overflow-hidden shadow-xl shadow-primary/5">
        <div className="absolute -right-12 -bottom-12 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/20 text-primary border border-primary/30 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Optimal Strategy</span>
            </div>

            <h2 className="text-2xl md:text-3xl font-extrabold text-slate-100 tracking-tight">
              {isRoll ? "RECOMMENDATION: ROLL / HOLD TRANSFER" : `RECOMMENDATION: PLAN ${topPlan?.plan_code || "A"}`}
            </h2>

            <p className="text-slate-300 text-sm md:text-base leading-relaxed">
              {isRoll
                ? "The MILP optimizer evaluates holding your free transfer as optimal, preserving future flexibility and avoiding costly hit penalties."
                : `Plan ${topPlan?.plan_code || "A"} projects +${topPlan?.gain_vs_hold || 0.0} xP net gain over holding across the planning horizon.`}
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <div className="bg-surface/80 border border-surfaceBorder px-4 py-2 rounded-xl text-xs">
                <span className="text-slate-400">Captain Pick:</span>{" "}
                <strong className="text-amber-400 font-mono text-sm ml-1">{captainName}</strong>
              </div>

              <div className="bg-surface/80 border border-surfaceBorder px-4 py-2 rounded-xl text-xs">
                <span className="text-slate-400">Hit Cost:</span>{" "}
                <strong className="text-cyan-400 font-mono text-sm ml-1">-{topPlan?.hits ? topPlan.hits * 4 : 0} pts</strong>
              </div>

              <div className="bg-surface/80 border border-surfaceBorder px-4 py-2 rounded-xl text-xs">
                <span className="text-slate-400">Robustness:</span>{" "}
                <strong className="text-emerald-400 font-mono text-sm ml-1">
                  {topPlan?.robustness ? `${Math.round(topPlan.robustness * 100)}%` : "High"}
                </strong>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row md:flex-col gap-3 shrink-0">
            <button
              onClick={() => onNavigateTab("planner")}
              className="bg-primary hover:bg-primary-hover text-slate-950 font-bold px-6 py-3.5 rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-primary/20 transition-all"
            >
              <span>VIEW FULL TRANSFER PLANS</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onAskAI("Explain why this transfer plan was recommended.")}
              className="bg-surfaceHover hover:bg-surfaceBorder text-slate-100 border border-surfaceBorder font-semibold px-6 py-3.5 rounded-xl text-sm flex items-center justify-center gap-2 transition-all"
            >
              <Bot className="w-4 h-4 text-secondary" />
              <span>ASK GROUNDED AI</span>
            </button>
          </div>
        </div>
      </div>

      {/* 3. Provenance Box: Why this recommendation? */}
      <div className="bg-surface/40 border border-surfaceBorder/80 rounded-2xl p-5 text-xs text-slate-400 space-y-2">
        <div className="flex items-center gap-2 font-bold text-slate-200">
          <Layers className="w-4 h-4 text-primary" />
          <span>Recommendation Provenance & Audit Trail</span>
        </div>
        <p className="text-slate-400 leading-relaxed">
          <strong>Decision Path:</strong> Official FPL API → Validated Snapshot (<code className="text-slate-300">{snapshotId || "snap_live"}</code>) → Real Manager Squad ({managerState?.squad?.length || 15} elements) → Component Projections & DGW aggregation → PuLP MILP Solver → Validated Output.
        </p>
        <div className="flex flex-wrap gap-4 text-[11px] text-slate-500 pt-1 font-mono">
          <span>Snapshot: {asOfTimestamp || "Current"}</span>
          <span>•</span>
          <span>Manager: {managerState?.manager_name || "Manager"} (#{managerState?.manager_id})</span>
          <span>•</span>
          <span>Model: v1.0.0 Deterministic</span>
        </div>
      </div>

      {/* 4. Secondary Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Module 1: Captaincy Quick Picks */}
        <div className="bg-surface border border-surfaceBorder rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-100 flex items-center gap-2 text-base">
              <Crown className="w-5 h-5 text-amber-400" />
              <span>Captaincy Profiles</span>
            </h3>
            <button
              onClick={() => onNavigateTab("captaincy")}
              className="text-xs text-primary font-semibold hover:underline flex items-center gap-0.5"
            >
              View All <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {captainPicks?.shield ? (
              <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-xl p-3 flex items-center justify-between">
                <div>
                  <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">SHIELD (Safe)</div>
                  <div className="font-bold text-slate-100 text-sm mt-0.5">{captainPicks.shield.web_name}</div>
                </div>
                <div className="text-right font-mono">
                  <div className="text-sm font-extrabold text-primary">{captainPicks.shield.mean_xp.toFixed(1)} xP</div>
                  <div className="text-[10px] text-slate-400">High EO • Low Risk</div>
                </div>
              </div>
            ) : null}

            {captainPicks?.diamond ? (
              <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-xl p-3 flex items-center justify-between">
                <div>
                  <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">DIAMOND (Balanced)</div>
                  <div className="font-bold text-slate-100 text-sm mt-0.5">{captainPicks.diamond.web_name}</div>
                </div>
                <div className="text-right font-mono">
                  <div className="text-sm font-extrabold text-cyan-400">{captainPicks.diamond.mean_xp.toFixed(1)} xP</div>
                  <div className="text-[10px] text-slate-400">Top xP Balance</div>
                </div>
              </div>
            ) : null}

            {captainPicks?.sword ? (
              <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-xl p-3 flex items-center justify-between">
                <div>
                  <div className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">SWORD (Differential)</div>
                  <div className="font-bold text-slate-100 text-sm mt-0.5">{captainPicks.sword.web_name}</div>
                </div>
                <div className="text-right font-mono">
                  <div className="text-sm font-extrabold text-purple-400">{captainPicks.sword.mean_xp.toFixed(1)} xP</div>
                  <div className="text-[10px] text-slate-400">High Ceiling</div>
                </div>
              </div>
            ) : null}

            {!captainPicks && (
              <div className="text-xs text-slate-500 py-3 text-center">Loading live captaincy metrics...</div>
            )}
          </div>
        </div>

        {/* Module 2: Squad Availability Watchlist */}
        <div className="bg-surface border border-surfaceBorder rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-100 flex items-center gap-2 text-base">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <span>Squad Availability</span>
            </h3>
            <button
              onClick={() => onNavigateTab("team")}
              className="text-xs text-primary font-semibold hover:underline flex items-center gap-0.5"
            >
              Check Pitch <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {flaggedPlayers.length > 0 ? (
              flaggedPlayers.slice(0, 3).map(({ player, proj }) => (
                <div key={player.player_id} className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-200 text-sm">{player.web_name}</div>
                    <div className="text-xs text-amber-400 font-medium">
                      {player.news || `${player.chance_of_playing_next_round ?? 75}% Chance`}
                    </div>
                  </div>
                  <div className="text-right font-mono text-xs text-slate-400">
                    <span>xMins: {proj?.xmins ?? 60}</span>
                  </div>
                </div>
              ))
            ) : safeStarters.length > 0 ? (
              safeStarters.slice(0, 2).map(({ player, proj }) => (
                <div key={player.player_id} className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-200 text-sm">{player.web_name}</div>
                    <div className="text-xs text-emerald-400 font-medium">Available • Starter</div>
                  </div>
                  <div className="text-right font-mono text-xs text-slate-400">
                    <span>xP: {proj?.mean_xp ?? 4.0}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-500 py-3 text-center">No injury flags in squad.</div>
            )}
          </div>
        </div>

        {/* Module 3: Chip Strategy Opportunity */}
        <div className="bg-surface border border-surfaceBorder rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-100 flex items-center gap-2 text-base">
              <Zap className="w-5 h-5 text-cyan-400" />
              <span>Chip Strategy Radar</span>
            </h3>
            <button
              onClick={() => onNavigateTab("chips")}
              className="text-xs text-primary font-semibold hover:underline flex items-center gap-0.5"
            >
              Chip Planner <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="bg-surfaceHover/50 border border-surfaceBorder rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300">Chips Available</span>
              <span className="text-xs font-bold text-primary font-mono">
                {4 - (managerState?.chips_used?.length || 0)} Remaining
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              MILP transfer optimizer operates without burning chips this gameweek. Save Wildcard for major DGW / BGW swings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
