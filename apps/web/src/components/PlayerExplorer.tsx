
import React, { useState } from "react";
import { Search, Filter, ArrowUpDown, ChevronRight } from "lucide-react";

interface PlayerExplorerProps {
  players: any[];
  teams: any[];
  projectionsDict: Record<number, any>;
  onSelectPlayer: (player: any) => void;
}

export const PlayerExplorer: React.FC<PlayerExplorerProps> = ({
  players,
  teams,
  projectionsDict,
  onSelectPlayer,
}) => {
  const [search, setSearch] = useState("");
  const [positionFilter, setPositionFilter] = useState("ALL");
  const [maxPrice, setMaxPrice] = useState<number>(15.5);

  const teamsMap = (teams || []).reduce((acc: any, t: any) => {
    acc[t.team_id] = t.short_name;
    return acc;
  }, {});

  const filteredPlayers = (players || []).filter((p: any) => {
    if (positionFilter !== "ALL" && p.position !== positionFilter) return false;
    if (p.current_price > maxPrice) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        p.web_name.toLowerCase().includes(q) ||
        p.first_name.toLowerCase().includes(q) ||
        p.second_name.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Controls */}
      <div className="bg-surface border border-surfaceBorder rounded-2xl p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
              <Search className="w-6 h-6 text-primary" />
              <span>Player Forecast Explorer</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Search and filter Premier League players by component xP, expected minutes, floor/ceiling percentiles, and prices.
            </p>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="flex flex-wrap items-center gap-4 pt-2">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search player name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-background text-sm text-slate-200 pl-9 pr-3 py-2 rounded-xl border border-surfaceBorder focus:outline-none focus:border-primary"
            />
          </div>

          {/* Position Selector */}
          <div className="flex items-center gap-1 bg-background p-1 rounded-xl border border-surfaceBorder">
            {["ALL", "GKP", "DEF", "MID", "FWD"].map((pos) => (
              <button
                key={pos}
                onClick={() => setPositionFilter(pos)}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                  positionFilter === pos
                    ? "bg-primary text-slate-950"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {pos}
              </button>
            ))}
          </div>

          {/* Max Price Slider */}
          <div className="flex items-center gap-2 bg-background px-3 py-1.5 rounded-xl border border-surfaceBorder text-xs text-slate-300">
            <span>Max Price:</span>
            <strong className="font-mono text-primary">£{maxPrice}m</strong>
            <input
              type="range"
              min="4.0"
              max="15.5"
              step="0.5"
              value={maxPrice}
              onChange={(e) => setMaxPrice(parseFloat(e.target.value))}
              className="w-24 accent-primary"
            />
          </div>
        </div>
      </div>

      {/* Players Table */}
      <div className="bg-surface border border-surfaceBorder rounded-3xl p-6 space-y-4">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Showing <strong className="text-slate-200">{filteredPlayers.length}</strong> players</span>
          <span>Click player row to open component forecast details</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-surfaceBorder text-slate-400 text-xs uppercase tracking-wider">
                <th className="py-3 px-4 font-semibold">PLAYER</th>
                <th className="py-3 px-4 font-semibold">POS</th>
                <th className="py-3 px-4 font-semibold">CLUB</th>
                <th className="py-3 px-4 font-semibold">PRICE</th>
                <th className="py-3 px-4 font-semibold">GW5 xP</th>
                <th className="py-3 px-4 font-semibold">EXPECTED MINS</th>
                <th className="py-3 px-4 font-semibold">P(START)</th>
                <th className="py-3 px-4 font-semibold">P10 FLOOR</th>
                <th className="py-3 px-4 font-semibold">P90 CEILING</th>
                <th className="py-3 px-4 font-semibold">SELECTED %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surfaceBorder text-slate-200 font-mono">
              {filteredPlayers.map((p: any) => {
                const proj = projectionsDict[p.player_id] || {
                  mean_xp: 4.2,
                  xmins: 82,
                  start_probability: 0.88,
                  p10_xp: 1.5,
                  p90_xp: 9.8
                };
                return (
                  <tr
                    key={p.player_id}
                    onClick={() => onSelectPlayer({ player: p, proj })}
                    className="hover:bg-surfaceHover/60 cursor-pointer transition-colors"
                  >
                    <td className="py-3.5 px-4 font-sans font-bold text-slate-100 flex items-center justify-between">
                      <span>{p.web_name}</span>
                      <ChevronRight className="w-4 h-4 text-slate-500" />
                    </td>
                    <td className="py-3.5 px-4 font-sans font-semibold text-xs text-slate-400">{p.position}</td>
                    <td className="py-3.5 px-4 font-sans font-bold text-slate-300">{teamsMap[p.team_id] || "CLUB"}</td>
                    <td className="py-3.5 px-4 text-emerald-400 font-bold">£{p.current_price}m</td>
                    <td className="py-3.5 px-4 font-extrabold text-primary">{proj.mean_xp} xP</td>
                    <td className="py-3.5 px-4 text-slate-300">{proj.xmins} mins</td>
                    <td className="py-3.5 px-4 text-emerald-400">{Math.round(proj.start_probability * 100)}%</td>
                    <td className="py-3.5 px-4 text-slate-400">{proj.p10_xp} xP</td>
                    <td className="py-3.5 px-4 text-purple-400 font-bold">{proj.p90_xp} xP</td>
                    <td className="py-3.5 px-4 text-slate-400">{p.selected_by_pct}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
