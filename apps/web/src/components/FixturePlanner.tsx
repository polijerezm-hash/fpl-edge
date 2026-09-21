
import React, { useState } from "react";
import { Calendar, TrendingUp, ShieldAlert, ArrowRight } from "lucide-react";

interface FixturePlannerProps {
  teams: any[];
  fixtures: any[];
  gameweeks: any[];
}

export const FixturePlanner: React.FC<FixturePlannerProps> = ({
  teams,
  fixtures,
  gameweeks,
}) => {
  const [filterMode, setFilterMode] = useState<"overall" | "attack" | "defence">("overall");

  const gws = [5, 6, 7, 8, 9];
  const teamsList = teams || [];

  // Map fixture per team & GW
  const fixtureMatrix: Record<number, Record<number, any>> = {};
  teamsList.forEach((t) => {
    fixtureMatrix[t.team_id] = {};
  });

  (fixtures || []).forEach((f: any) => {
    if (gws.includes(f.gameweek)) {
      if (fixtureMatrix[f.home_team_id]) {
        fixtureMatrix[f.home_team_id][f.gameweek] = {
          opp_id: f.away_team_id,
          is_home: true,
          difficulty: f.difficulty_home
        };
      }
      if (fixtureMatrix[f.away_team_id]) {
        fixtureMatrix[f.away_team_id][f.gameweek] = {
          opp_id: f.home_team_id,
          is_home: false,
          difficulty: f.difficulty_away
        };
      }
    }
  });

  const teamsMap = teamsList.reduce((acc: any, t: any) => {
    acc[t.team_id] = t.short_name;
    return acc;
  }, {});

  const getDifficultyColor = (diff: number) => {
    if (diff <= 2) return "bg-emerald-500/20 text-emerald-400 border-emerald-500/40";
    if (diff === 3) return "bg-slate-700/50 text-slate-300 border-slate-600";
    if (diff === 4) return "bg-amber-500/20 text-amber-400 border-amber-500/40";
    return "bg-rose-500/20 text-rose-400 border-rose-500/40";
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Controls */}
      <div className="bg-surface border border-surfaceBorder rounded-2xl p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
              <Calendar className="w-6 h-6 text-primary" />
              <span>Fixture Difficulty Matrix & Run Heatmap</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Analyze fixture difficulty swings over the next 5 gameweeks to target upcoming opponent runs.
            </p>
          </div>

          <div className="flex items-center gap-1 bg-background p-1 rounded-xl border border-surfaceBorder">
            {(["overall", "attack", "defence"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setFilterMode(m)}
                className={`px-3 py-1.5 text-xs font-bold capitalize rounded-lg transition-all ${
                  filterMode === m
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

      {/* Target Teams Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-4 flex items-center gap-3">
          <TrendingUp className="w-6 h-6 text-emerald-400 shrink-0" />
          <div>
            <div className="font-bold text-slate-100 text-sm">Teams to Target (Best Run)</div>
            <div className="text-xs text-emerald-300 font-medium mt-0.5">
              Arsenal (NFO, WHU, BRE) & Man City (FUL, SOU, BOU) have prime attack fixture runs.
            </div>
          </div>
        </div>

        <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-4 flex items-center gap-3">
          <ShieldAlert className="w-6 h-6 text-rose-400 shrink-0" />
          <div>
            <div className="font-bold text-slate-100 text-sm">Teams to Avoid (Tough Run)</div>
            <div className="text-xs text-rose-300 font-medium mt-0.5">
              Aston Villa & Newcastle face tough opponent defensive blocks over GW6–8.
            </div>
          </div>
        </div>
      </div>

      {/* Fixture Matrix Table */}
      <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-surfaceBorder text-slate-400 text-xs uppercase tracking-wider">
                <th className="py-3 px-4 font-semibold">CLUB</th>
                {gws.map((gw) => (
                  <th key={gw} className="py-3 px-4 font-semibold text-center">
                    GW{gw}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-surfaceBorder">
              {teamsList.map((t: any) => (
                <tr key={t.team_id} className="hover:bg-surfaceHover/50 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-100 font-sans">{t.name}</td>
                  {gws.map((gw) => {
                    const fix = fixtureMatrix[t.team_id]?.[gw];
                    if (!fix) {
                      return (
                        <td key={gw} className="py-3 px-4 text-center text-xs text-slate-500 font-mono">
                          BLANK
                        </td>
                      );
                    }
                    const oppName = teamsMap[fix.opp_id] || "OPP";
                    const loc = fix.is_home ? "(H)" : "(A)";
                    return (
                      <td key={gw} className="py-2.5 px-3 text-center">
                        <div
                          className={`inline-block px-3 py-1.5 rounded-xl border text-xs font-mono font-bold ${getDifficultyColor(
                            fix.difficulty
                          )}`}
                        >
                          {oppName} {loc}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
