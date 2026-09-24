
import React, { useState } from "react";
import {
  Shuffle,
  Sparkles,
  Lock,
  Ban,
  Sliders,
  CheckCircle2,
  HelpCircle,
  TrendingUp,
  ArrowRightLeft,
  Crown
} from "lucide-react";

interface TransferPlannerProps {
  optimizationResult: any;
  playersDict: Record<number, any>;
  onRunOptimize: (params: any) => void;
  onOpenCompare: (planA: any, planB: any) => void;
  onAskAI: (question: string) => void;
}

export const TransferPlanner: React.FC<TransferPlannerProps> = ({
  optimizationResult,
  playersDict,
  onRunOptimize,
  onOpenCompare,
  onAskAI,
}) => {
  const [horizon, setHorizon] = useState<number>(3);
  const [riskProfile, setRiskProfile] = useState<string>("balanced");
  const [selectedPlanIndex, setSelectedPlanIndex] = useState<number>(0);

  const plans = optimizationResult?.plans || [];
  const activePlan = plans[selectedPlanIndex] || plans[0];
  const baselineXp = optimizationResult?.baseline_xp || 160.0;

  const handleOptimizeClick = () => {
    onRunOptimize({ horizon, risk_profile: riskProfile });
  };

  const getPlayerName = (pid: number) => {
    return playersDict[pid]?.web_name || `Player #${pid}`;
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Control Bar */}
      <div className="bg-surface border border-surfaceBorder rounded-2xl p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
              <Shuffle className="w-6 h-6 text-primary" />
              <span>Transfer Planner & Squad Optimizer</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
            Compare transfer paths over 1–5 gameweeks, including the value of simply rolling.
            </p>
          </div>

          <button
            onClick={handleOptimizeClick}
            className="bg-primary hover:bg-primary-hover text-slate-950 font-bold px-6 py-3.5 rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-primary/20 transition-all shrink-0"
          >
            <Sparkles className="w-4 h-4" />
            <span>OPTIMISE MY TEAM</span>
          </button>
        </div>

        {/* Solver Parameters Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-surfaceBorder">
          {/* Horizon Selector */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5">Planning Horizon</label>
            <div className="flex items-center gap-1 bg-background p-1 rounded-xl border border-surfaceBorder">
              {[1, 3, 5].map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                    horizon === h
                      ? "bg-primary text-slate-950"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {h} GW
                </button>
              ))}
            </div>
          </div>

          {/* Risk Profile Selector */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5">Strategy Risk Profile</label>
            <div className="flex items-center gap-1 bg-background p-1 rounded-xl border border-surfaceBorder">
              {["safe", "balanced", "aggressive"].map((r) => (
                <button
                  key={r}
                  onClick={() => setRiskProfile(r)}
                  className={`flex-1 py-1.5 text-xs font-bold rounded-lg capitalize transition-all ${
                    riskProfile === r
                      ? "bg-secondary text-slate-950"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Lock / Ban Player */}
          <div className="flex items-end gap-2">
            <button
              onClick={() => alert("Select a player from squad to lock in solver.")}
              className="flex-1 py-2 px-3 bg-surfaceHover border border-surfaceBorder hover:border-slate-500 rounded-xl text-xs font-semibold text-slate-300 flex items-center justify-center gap-1.5"
            >
              <Lock className="w-3.5 h-3.5 text-emerald-400" />
              <span>Lock Player</span>
            </button>

            <button
              onClick={() => alert("Select a target player to ban from solver.")}
              className="flex-1 py-2 px-3 bg-surfaceHover border border-surfaceBorder hover:border-slate-500 rounded-xl text-xs font-semibold text-slate-300 flex items-center justify-center gap-1.5"
            >
              <Ban className="w-3.5 h-3.5 text-amber-400" />
              <span>Ban Player</span>
            </button>
          </div>

          {/* Advanced Settings */}
          <div className="flex items-end">
            <button
              onClick={() => alert("Advanced MILP Settings: Future GW discount = 5%, Bank coefficient = 0.2, FT value = 1.4")}
              className="w-full py-2 px-3 bg-surfaceHover border border-surfaceBorder hover:border-slate-500 rounded-xl text-xs font-semibold text-slate-300 flex items-center justify-center gap-1.5"
            >
              <Sliders className="w-3.5 h-3.5 text-slate-400" />
              <span>Advanced Solver Settings</span>
            </button>
          </div>
        </div>
      </div>

      {/* Top 5 Feasible Plans Tabs */}
      {plans.length > 0 && (
        <div className="space-y-6">
          {/* Plan Tabs Bar */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {plans.map((plan: any, idx: number) => {
              const isSelected = selectedPlanIndex === idx;
              return (
                <button
                  key={idx}
                  onClick={() => setSelectedPlanIndex(idx)}
                  className={`px-5 py-3 rounded-2xl border text-sm font-bold transition-all shrink-0 flex items-center gap-3 ${
                    isSelected
                      ? "bg-primary/10 border-primary text-slate-100 shadow-lg shadow-primary/10"
                      : "bg-surface border-surfaceBorder text-slate-400 hover:bg-surfaceHover hover:text-slate-200"
                  }`}
                >
                  <span className={`w-6 h-6 rounded-full text-xs flex items-center justify-center font-extrabold ${
                    isSelected ? "bg-primary text-slate-950" : "bg-surfaceBorder text-slate-300"
                  }`}>
                    {plan.plan_code || String.fromCharCode(65 + idx)}
                  </span>

                  <div>
                    <div className="text-left font-mono font-extrabold text-sm">{plan.expected_points} xP</div>
                    <div className="text-[10px] text-slate-400 font-medium">
                      {plan.gain_vs_hold >= 0 ? `+${plan.gain_vs_hold}` : plan.gain_vs_hold} xP vs HOLD
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Active Plan Detail View */}
          {activePlan && (
            <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 md:p-8 space-y-6">
              {/* Top Plan Metrics Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-surfaceBorder">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="text-xl font-extrabold text-slate-100">
                      PLAN {activePlan.plan_code}
                    </span>
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-primary/20 text-primary border border-primary/30">
                      {activePlan.gain_vs_hold >= 0 ? `+${activePlan.gain_vs_hold} xP GAIN VS HOLD` : "ROLL OPTION"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    {horizon}-Gameweek Horizon Total: <strong className="text-slate-200 font-mono">{activePlan.expected_points} xP</strong>
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right text-xs bg-surfaceHover px-3 py-2 rounded-xl border border-surfaceBorder">
                    <div className="text-slate-400">Hits Cost:</div>
                    <div className="font-bold text-amber-400 font-mono">{activePlan.hits * 4} pts ({activePlan.hits} hits)</div>
                  </div>

                  <div className="text-right text-xs bg-surfaceHover px-3 py-2 rounded-xl border border-surfaceBorder">
                    <div className="text-slate-400">Final Bank:</div>
                    <div className="font-bold text-emerald-400 font-mono">£{activePlan.final_bank}m</div>
                  </div>

                  {plans.length > 1 && (
                    <button
                      onClick={() => onOpenCompare(plans[0], plans[1])}
                      className="bg-surfaceHover hover:bg-surfaceBorder text-slate-200 border border-surfaceBorder px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
                    >
                      <ArrowRightLeft className="w-4 h-4 text-secondary" />
                      <span>Compare Plans</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Horizontal Gameweek Timeline */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
                  Transfer Sequence & Gameweek Timeline
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {activePlan.gameweeks?.map((gwData: any, idx: number) => {
                    const tinNames = gwData.transfers_in.map(getPlayerName);
                    const toutNames = gwData.transfers_out.map(getPlayerName);
                    const capName = getPlayerName(gwData.captain);

                    return (
                      <div
                        key={idx}
                        className="bg-surfaceHover/50 border border-surfaceBorder rounded-2xl p-5 space-y-3 relative"
                      >
                        <div className="flex items-center justify-between border-b border-surfaceBorder pb-2">
                          <span className="font-extrabold text-slate-100 text-sm">
                            GAMEWEEK {gwData.gw}
                          </span>
                          <span className="text-xs font-mono font-semibold text-slate-400">
                            Bank: £{gwData.bank}m
                          </span>
                        </div>

                        {/* Transfers Move */}
                        {tinNames.length === 0 ? (
                          <div className="py-3 text-center text-xs font-bold text-emerald-400 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                            ROLL / HOLD TRANSFER (+1 FT)
                          </div>
                        ) : (
                          <div className="space-y-1.5 text-xs">
                            <div className="flex items-center justify-between text-rose-400 bg-rose-500/10 px-2.5 py-1.5 rounded-lg border border-rose-500/20">
                              <span className="font-semibold">OUT:</span>
                              <span className="font-mono">{toutNames.join(", ")}</span>
                            </div>
                            <div className="flex items-center justify-between text-emerald-400 bg-emerald-500/10 px-2.5 py-1.5 rounded-lg border border-emerald-500/20">
                              <span className="font-semibold">IN:</span>
                              <span className="font-mono">{tinNames.join(", ")}</span>
                            </div>
                          </div>
                        )}

                        {/* Captain */}
                        <div className="flex items-center justify-between text-xs pt-1">
                          <span className="text-slate-400 flex items-center gap-1">
                            <Crown className="w-3.5 h-3.5 text-amber-400" /> Captain:
                          </span>
                          <strong className="text-slate-200">{capName}</strong>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Plan explanation */}
              <div className="bg-surfaceHover/80 border border-surfaceBorder rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h4 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary" />
                    <span>Why Plan {activePlan.plan_code}?</span>
                  </h4>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed max-w-3xl">
                    This plan optimizes starting XI expected score while preserving FT availability.
                    Net expected gain vs HOLD is +{activePlan.gain_vs_hold} xP over {horizon} gameweeks.
                  </p>
                </div>

                <button
                  onClick={() => onAskAI(`Why does Plan ${activePlan.plan_code} beat other transfer options?`)}
                  className="bg-secondary/10 hover:bg-secondary/20 text-secondary border border-secondary/30 px-4 py-2.5 rounded-xl text-xs font-bold transition-colors shrink-0 flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Explain this plan</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
