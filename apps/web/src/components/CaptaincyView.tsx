
import React from "react";
import { Crown, Shield, Zap, Sparkles, TrendingUp } from "lucide-react";

interface CaptaincyViewProps {
  captainData: any;
  playersDict: Record<number, any>;
}

export const CaptaincyView: React.FC<CaptaincyViewProps> = ({
  captainData,
  playersDict,
}) => {
  const shield = captainData?.shield;
  const diamond = captainData?.diamond;
  const sword = captainData?.sword;
  const ranked = captainData?.ranked || [];

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
          <Crown className="w-6 h-6 text-amber-400" />
          <span>Captaincy Decision Engine — GW5</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Multi-profile captain recommendations balancing expected points, floor, ceiling, and effective ownership.
        </p>
      </div>

      {/* 3 Strategy Profile Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* SHIELD */}
        <div className="bg-surface border border-emerald-500/30 rounded-3xl p-6 relative overflow-hidden shadow-xl shadow-emerald-500/5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold uppercase tracking-wider">
              <Shield className="w-3.5 h-3.5" /> SHIELD PROFILE
            </span>
            <span className="text-[10px] text-slate-400 font-mono">Rank Protection</span>
          </div>

          <div>
            <h3 className="text-2xl font-black text-slate-100">{shield?.web_name || "Salah"}</h3>
            <div className="text-xs text-slate-400 font-medium">High Ownership • High Minutes Security</div>
          </div>

          <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-2xl p-4 flex items-baseline justify-between font-mono">
            <div>
              <div className="text-2xl font-extrabold text-emerald-400">{shield?.mean_xp || 7.8} xP</div>
              <div className="text-[10px] text-slate-400 font-sans">Mean Forecast</div>
            </div>
            <div className="text-right text-xs text-slate-300 font-sans">
              <div>Floor (P10): <strong>{shield?.p10_xp || 3.2} xP</strong></div>
              <div>Ceiling (P90): <strong>{shield?.p90_xp || 12.8} xP</strong></div>
            </div>
          </div>
        </div>

        {/* DIAMOND */}
        <div className="bg-surface border border-cyan-500/30 rounded-3xl p-6 relative overflow-hidden shadow-xl shadow-cyan-500/5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-400 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" /> DIAMOND PROFILE
            </span>
            <span className="text-[10px] text-slate-400 font-mono">Top xP Balance</span>
          </div>

          <div>
            <h3 className="text-2xl font-black text-slate-100">{diamond?.web_name || "Haaland"}</h3>
            <div className="text-xs text-slate-400 font-medium">Strongest Overall Expected Score</div>
          </div>

          <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-2xl p-4 flex items-baseline justify-between font-mono">
            <div>
              <div className="text-2xl font-extrabold text-cyan-400">{diamond?.mean_xp || 8.2} xP</div>
              <div className="text-[10px] text-slate-400 font-sans">Mean Forecast</div>
            </div>
            <div className="text-right text-xs text-slate-300 font-sans">
              <div>Floor (P10): <strong>{diamond?.p10_xp || 3.8} xP</strong></div>
              <div>Ceiling (P90): <strong>{diamond?.p90_xp || 14.5} xP</strong></div>
            </div>
          </div>
        </div>

        {/* SWORD */}
        <div className="bg-surface border border-purple-500/30 rounded-3xl p-6 relative overflow-hidden shadow-xl shadow-purple-500/5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 text-xs font-bold uppercase tracking-wider">
              <Zap className="w-3.5 h-3.5" /> SWORD PROFILE
            </span>
            <span className="text-[10px] text-slate-400 font-mono">Chasing / Differential</span>
          </div>

          <div>
            <h3 className="text-2xl font-black text-slate-100">{sword?.web_name || "Palmer"}</h3>
            <div className="text-xs text-slate-400 font-medium">Low Ownership • Explosive Ceiling</div>
          </div>

          <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-2xl p-4 flex items-baseline justify-between font-mono">
            <div>
              <div className="text-2xl font-extrabold text-purple-400">{sword?.mean_xp || 7.5} xP</div>
              <div className="text-[10px] text-slate-400 font-sans">Mean Forecast</div>
            </div>
            <div className="text-right text-xs text-slate-300 font-sans">
              <div>Floor (P10): <strong>{sword?.p10_xp || 2.5} xP</strong></div>
              <div>Ceiling (P90): <strong>{sword?.p90_xp || 15.2} xP</strong></div>
            </div>
          </div>
        </div>
      </div>

      {/* Ranked Captain Table */}
      <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
          Ranked Captain Candidate Matrix
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-surfaceBorder text-slate-400 text-xs uppercase tracking-wider">
                <th className="py-3 px-4 font-semibold">RANK</th>
                <th className="py-3 px-4 font-semibold">PLAYER</th>
                <th className="py-3 px-4 font-semibold">MEAN xP</th>
                <th className="py-3 px-4 font-semibold">P10 FLOOR</th>
                <th className="py-3 px-4 font-semibold">P90 CEILING</th>
                <th className="py-3 px-4 font-semibold">EXPECTED MINS</th>
                <th className="py-3 px-4 font-semibold">P(START)</th>
                <th className="py-3 px-4 font-semibold">SELECTED BY %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surfaceBorder text-slate-200 font-mono">
              {ranked.map((c: any, idx: number) => (
                <tr key={c.player_id} className="hover:bg-surfaceHover/50 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-400">#{idx + 1}</td>
                  <td className="py-3.5 px-4 font-sans font-bold text-slate-100">{c.web_name}</td>
                  <td className="py-3.5 px-4 font-extrabold text-primary">{c.mean_xp} xP</td>
                  <td className="py-3.5 px-4 text-slate-400">{c.p10_xp} xP</td>
                  <td className="py-3.5 px-4 text-purple-400 font-bold">{c.p90_xp} xP</td>
                  <td className="py-3.5 px-4 text-slate-300">{c.xmins} mins</td>
                  <td className="py-3.5 px-4 text-emerald-400">{Math.round(c.start_prob * 100)}%</td>
                  <td className="py-3.5 px-4 text-slate-400">{c.selected_by_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
