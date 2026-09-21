
import React, { useState } from "react";
import { Trophy, Shield, Flame, Users, ArrowUpRight } from "lucide-react";

interface MiniLeagueViewProps {
  managerState: any;
}

export const MiniLeagueView: React.FC<MiniLeagueViewProps> = ({ managerState }) => {
  const [strategyMode, setStrategyMode] = useState<"protect" | "balanced" | "chase">("balanced");

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-surface border border-surfaceBorder rounded-2xl p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
              <Trophy className="w-6 h-6 text-amber-400" />
              <span>Mini-League Exposure & Rival Tracking</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Analyze league Effective Ownership (EO), main rival threats, and differential exposure.
            </p>
          </div>

          <div className="flex items-center gap-1 bg-background p-1 rounded-xl border border-surfaceBorder">
            {(["protect", "balanced", "chase"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setStrategyMode(m)}
                className={`px-4 py-1.5 text-xs font-bold capitalize rounded-lg transition-all ${
                  strategyMode === m
                    ? "bg-primary text-slate-950"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-surface border border-surfaceBorder rounded-2xl p-5">
          <div className="text-xs font-semibold text-slate-400 uppercase">League Position</div>
          <div className="text-3xl font-extrabold text-slate-100 font-mono mt-1">2nd</div>
          <div className="text-xs text-slate-500 mt-1">12 Managers in League</div>
        </div>

        <div className="bg-surface border border-surfaceBorder rounded-2xl p-5">
          <div className="text-xs font-semibold text-slate-400 uppercase">Gap to Leader</div>
          <div className="text-3xl font-extrabold text-rose-400 font-mono mt-1">-18 pts</div>
          <div className="text-xs text-slate-500 mt-1">Catchable within 2 GWs</div>
        </div>

        <div className="bg-surface border border-surfaceBorder rounded-2xl p-5">
          <div className="text-xs font-semibold text-slate-400 uppercase">Gap to 3rd Place</div>
          <div className="text-3xl font-extrabold text-emerald-400 font-mono mt-1">+24 pts</div>
          <div className="text-xs text-slate-500 mt-1 font-medium">Safe Cushion</div>
        </div>

        <div className="bg-surface border border-surfaceBorder rounded-2xl p-5">
          <div className="text-xs font-semibold text-slate-400 uppercase">Strategy Mode</div>
          <div className="text-xl font-bold text-primary capitalize mt-2 flex items-center gap-1.5">
            <Flame className="w-4 h-4 text-primary" /> {strategyMode}
          </div>
          <div className="text-xs text-slate-500 mt-1">Utility Risk Adjusted</div>
        </div>
      </div>

      {/* League EO & Differentials */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* League EO */}
        <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4">
          <h3 className="font-bold text-slate-100 text-base">League Effective Ownership (EO)</h3>
          <div className="space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between p-3 bg-surfaceHover/50 rounded-xl border border-surfaceBorder">
              <span className="font-sans font-bold text-slate-200">Erling Haaland</span>
              <div className="flex items-center gap-4">
                <span className="text-slate-400">EO: 142%</span>
                <span className="text-emerald-400 font-bold">You Own (C)</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-surfaceHover/50 rounded-xl border border-surfaceBorder">
              <span className="font-sans font-bold text-slate-200">Mohamed Salah</span>
              <div className="flex items-center gap-4">
                <span className="text-slate-400">EO: 98%</span>
                <span className="text-emerald-400 font-bold">You Own</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-surfaceHover/50 rounded-xl border border-surfaceBorder">
              <span className="font-sans font-bold text-slate-200">Cole Palmer</span>
              <div className="flex items-center gap-4">
                <span className="text-slate-400">EO: 85%</span>
                <span className="text-rose-400 font-bold">Not Owned (Threat)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Your Differentials */}
        <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4">
          <h3 className="font-bold text-slate-100 text-base">Your League Differentials</h3>
          <div className="space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between p-3 bg-surfaceHover/50 rounded-xl border border-surfaceBorder">
              <span className="font-sans font-bold text-slate-200">Bryan Mbeumo</span>
              <div className="flex items-center gap-4">
                <span className="text-slate-400">League EO: 25%</span>
                <span className="text-cyan-400 font-bold">+75% Exposure Gain</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-surfaceHover/50 rounded-xl border border-surfaceBorder">
              <span className="font-sans font-bold text-slate-200">Morgan Rogers</span>
              <div className="flex items-center gap-4">
                <span className="text-slate-400">League EO: 18%</span>
                <span className="text-cyan-400 font-bold">+82% Exposure Gain</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
