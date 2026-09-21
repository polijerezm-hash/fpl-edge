
import React from "react";
import { X, Activity, ShieldCheck, TrendingUp, AlertTriangle } from "lucide-react";

interface PlayerDetailModalProps {
  playerData: any;
  onClose: () => void;
}

export const PlayerDetailModal: React.FC<PlayerDetailModalProps> = ({
  playerData,
  onClose,
}) => {
  if (!playerData) return null;

  const player = playerData.player || {};
  const proj = playerData.proj || {};

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-surface border border-surfaceBorder rounded-3xl w-full max-w-xl overflow-hidden shadow-2xl space-y-6 p-6 md:p-8 animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-surfaceBorder pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-2xl font-black text-slate-100">{player.web_name}</h3>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-primary/20 text-primary border border-primary/30">
                {player.position}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {player.first_name} {player.second_name} • £{player.current_price}m • Selected by {player.selected_by_pct}%
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-surfaceHover text-slate-400 hover:text-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Minutes & Start Certainty Bar */}
        <div className="bg-surfaceHover/60 border border-surfaceBorder rounded-2xl p-4 grid grid-cols-3 gap-4 text-center font-mono">
          <div>
            <div className="text-lg font-extrabold text-primary">{proj.mean_xp || 5.2} xP</div>
            <div className="text-[10px] text-slate-400 font-sans">Mean GW Forecast</div>
          </div>
          <div>
            <div className="text-lg font-extrabold text-slate-100">{proj.xmins || 82} mins</div>
            <div className="text-[10px] text-slate-400 font-sans">Expected Minutes</div>
          </div>
          <div>
            <div className="text-lg font-extrabold text-emerald-400">{Math.round((proj.start_probability || 0.88) * 100)}%</div>
            <div className="text-[10px] text-slate-400 font-sans">P(Start)</div>
          </div>
        </div>

        {/* Component Breakdown */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Component Expected Points Breakdown
          </h4>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="bg-background border border-surfaceBorder p-3 rounded-xl">
              <div className="text-slate-400 font-sans text-[10px]">Appearance xP</div>
              <div className="font-bold text-slate-200 mt-0.5">1.9 pts</div>
            </div>

            <div className="bg-background border border-surfaceBorder p-3 rounded-xl">
              <div className="text-slate-400 font-sans text-[10px]">Goal xP</div>
              <div className="font-bold text-emerald-400 mt-0.5">{proj.goal_xp || 0.42} pts</div>
            </div>

            <div className="bg-background border border-surfaceBorder p-3 rounded-xl">
              <div className="text-slate-400 font-sans text-[10px]">Assist xP</div>
              <div className="font-bold text-cyan-400 mt-0.5">{proj.assist_xp || 0.28} pts</div>
            </div>

            <div className="bg-background border border-surfaceBorder p-3 rounded-xl">
              <div className="text-slate-400 font-sans text-[10px]">Clean Sheet xP</div>
              <div className="font-bold text-slate-200 mt-0.5">{proj.clean_sheet_xp || 0.0} pts</div>
            </div>

            <div className="bg-background border border-surfaceBorder p-3 rounded-xl">
              <div className="text-slate-400 font-sans text-[10px]">Bonus xP</div>
              <div className="font-bold text-amber-400 mt-0.5">{proj.bonus_xp || 0.35} pts</div>
            </div>

            <div className="bg-background border border-surfaceBorder p-3 rounded-xl">
              <div className="text-slate-400 font-sans text-[10px]">Floor (P10) / Ceiling (P90)</div>
              <div className="font-bold text-purple-400 mt-0.5">{proj.p10_xp || 1.5} / {proj.p90_xp || 12.0}</div>
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="bg-primary text-slate-950 font-bold px-6 py-2.5 rounded-xl text-sm hover:bg-primary-hover transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
