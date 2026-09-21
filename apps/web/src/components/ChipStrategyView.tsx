
import React from "react";
import { Zap, Calendar, Sparkles, TrendingUp, CheckCircle2 } from "lucide-react";

interface ChipStrategyViewProps {
  chipData: any;
}

export const ChipStrategyView: React.FC<ChipStrategyViewProps> = ({ chipData }) => {
  const wildcard = chipData?.wildcard || { recommended_gw: 8, projected_incremental_benefit: 16.5, confidence: "High", reasoning: "Optimal fixture swings for Arsenal & Man City." };
  const freeHit = chipData?.free_hit || { recommended_gw: 12, projected_incremental_benefit: 12.0, confidence: "Moderate", reasoning: "Blank / double gameweek navigation." };
  const benchBoost = chipData?.bench_boost || { recommended_gw: 12, projected_incremental_benefit: 14.0, confidence: "Moderate", reasoning: "Peak 15-man active squad expected points." };
  const tripleCaptain = chipData?.triple_captain || { recommended_gw: 8, projected_incremental_benefit: 8.5, confidence: "High", reasoning: "Single-player peak expected score window." };

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
          <Zap className="w-6 h-6 text-cyan-400" />
          <span>Chip Strategy Analyzer & Season Timeline</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Evaluates candidate gameweeks for Wildcard, Free Hit, Bench Boost, and Triple Captain based on projected squad gain.
        </p>
      </div>

      {/* 4 Chip Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* WILDCARD */}
        <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4 relative overflow-hidden shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              WILDCARD
            </span>
            <span className="text-xs font-mono font-bold text-slate-400">{wildcard.confidence}</span>
          </div>

          <div>
            <div className="text-3xl font-black text-slate-100 font-mono">GW{wildcard.recommended_gw}</div>
            <div className="text-xs text-slate-400 mt-0.5">Target Candidate Window</div>
          </div>

          <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-2xl p-3 text-xs font-mono">
            <div className="text-emerald-400 font-extrabold text-sm">+{wildcard.projected_incremental_benefit} xP</div>
            <div className="text-slate-400 font-sans text-[10px]">Projected Incremental Gain</div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            {wildcard.reasoning}
          </p>
        </div>

        {/* FREE HIT */}
        <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4 relative overflow-hidden shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              FREE HIT
            </span>
            <span className="text-xs font-mono font-bold text-slate-400">{freeHit.confidence}</span>
          </div>

          <div>
            <div className="text-3xl font-black text-slate-100 font-mono">GW{freeHit.recommended_gw}</div>
            <div className="text-xs text-slate-400 mt-0.5">Target Candidate Window</div>
          </div>

          <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-2xl p-3 text-xs font-mono">
            <div className="text-cyan-400 font-extrabold text-sm">+{freeHit.projected_incremental_benefit} xP</div>
            <div className="text-slate-400 font-sans text-[10px]">1-GW Upside Gain</div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            {freeHit.reasoning}
          </p>
        </div>

        {/* BENCH BOOST */}
        <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4 relative overflow-hidden shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">
              BENCH BOOST
            </span>
            <span className="text-xs font-mono font-bold text-slate-400">{benchBoost.confidence}</span>
          </div>

          <div>
            <div className="text-3xl font-black text-slate-100 font-mono">GW{benchBoost.recommended_gw}</div>
            <div className="text-xs text-slate-400 mt-0.5">Target Candidate Window</div>
          </div>

          <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-2xl p-3 text-xs font-mono">
            <div className="text-purple-400 font-extrabold text-sm">+{benchBoost.projected_incremental_benefit} xP</div>
            <div className="text-slate-400 font-sans text-[10px]">Bench Points Expected</div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            {benchBoost.reasoning}
          </p>
        </div>

        {/* TRIPLE CAPTAIN */}
        <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4 relative overflow-hidden shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
              TRIPLE CAPTAIN
            </span>
            <span className="text-xs font-mono font-bold text-slate-400">{tripleCaptain.confidence}</span>
          </div>

          <div>
            <div className="text-3xl font-black text-slate-100 font-mono">GW{tripleCaptain.recommended_gw}</div>
            <div className="text-xs text-slate-400 mt-0.5">Target Candidate Window</div>
          </div>

          <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-2xl p-3 text-xs font-mono">
            <div className="text-amber-400 font-extrabold text-sm">+{tripleCaptain.projected_incremental_benefit} xP</div>
            <div className="text-slate-400 font-sans text-[10px]">Captain Additional pts</div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            {tripleCaptain.reasoning}
          </p>
        </div>
      </div>
    </div>
  );
};
