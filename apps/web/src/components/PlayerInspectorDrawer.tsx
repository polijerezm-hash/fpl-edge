import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Crown, AlertCircle, Activity, Target, TrendingUp, BarChart2, Calendar } from "lucide-react";

interface Projection {
  player_id: number;
  mean_xp: number;
  xmins: number;
  start_probability: number;
  goal_xp?: number;
  assist_xp?: number;
  clean_sheet_xp?: number;
  save_xp?: number;
  bonus_xp?: number;
  p10_xp?: number;
  p90_xp?: number;
}

interface PlayerData {
  player_id: number;
  web_name: string;
  first_name?: string;
  second_name?: string;
  team_id: number;
  position: string;
  current_price: number;
  status: string;
  news?: string;
  chance_of_playing_next_round?: number;
  minutes?: number;
  starts?: number;
  form?: number;
  selected_by_pct?: number;
  total_points?: number;
  points_per_game?: number;
}

interface Team {
  team_id: number;
  short_name: string;
  name: string;
}

interface Fixture {
  fixture_id: number;
  gameweek: number;
  home_team_id: number;
  away_team_id: number;
  difficulty_home: number;
  difficulty_away: number;
  finished: boolean;
}

interface SquadPlayer {
  player_id: number;
  position: string;
  purchase_price: number;
  selling_price: number;
  starting: boolean;
  captain: boolean;
  vice_captain: boolean;
}

interface PlayerInspectorDrawerProps {
  playerInfo: { player: PlayerData; squadPlayer: SquadPlayer; proj: Projection } | null;
  teamsDict: Record<number, Team>;
  fixtures: Fixture[];
  currentGw: number;
  onClose: () => void;
}

const fdrColor = (d: number) => {
  if (d <= 2) return "bg-emerald-100 text-emerald-800 border-emerald-200";
  if (d === 3) return "bg-amber-100 text-amber-800 border-amber-200";
  return "bg-rose-100 text-rose-800 border-rose-200";
};

const positionColors: Record<string, string> = {
  GKP: "bg-amber-100 text-amber-800 border-amber-200",
  DEF: "bg-emerald-100 text-emerald-800 border-emerald-200",
  MID: "bg-indigo-100 text-indigo-800 border-indigo-200",
  FWD: "bg-rose-100 text-rose-800 border-rose-200",
};

function XpBar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? Math.min(100, (value / total) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-slate-600">{label}</span>
        <span className="font-mono text-[11px] font-semibold tabular-nums text-slate-800">{value.toFixed(2)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ delay: 0.1, type: "spring", stiffness: 300, damping: 30 }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  );
}

export const PlayerInspectorDrawer: React.FC<PlayerInspectorDrawerProps> = ({
  playerInfo,
  teamsDict,
  fixtures,
  currentGw,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<"xp" | "fixtures" | "stats">("xp");

  const isOpen = !!playerInfo;

  return (
    <AnimatePresence>
      {isOpen && playerInfo && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-slate-950/20 backdrop-blur-[2px]"
          />

          {/* Drawer */}
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 380, damping: 38 }}
            className="fixed bottom-0 right-0 top-0 z-50 flex w-full max-w-[400px] flex-col border-l border-slate-200 bg-white shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-start justify-between border-b border-slate-200 p-5">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className={`rounded border px-2 py-0.5 text-[10px] font-bold ${positionColors[playerInfo.player.position] ?? "bg-slate-100 text-slate-600 border-slate-200"}`}>
                    {playerInfo.player.position}
                  </span>
                  {playerInfo.squadPlayer.captain && (
                    <span className="flex items-center gap-1 rounded border border-amber-200 bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                      <Crown className="h-3 w-3" /> Captain
                    </span>
                  )}
                  {playerInfo.squadPlayer.vice_captain && !playerInfo.squadPlayer.captain && (
                    <span className="rounded border border-slate-300 bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600">
                      Vice-Captain
                    </span>
                  )}
                </div>
                <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-900">
                  {playerInfo.player.web_name}
                </h2>
                <p className="mt-0.5 text-sm text-slate-500">
                  {teamsDict[playerInfo.player.team_id]?.name ?? "Unknown Club"} ·{" "}
                  <span className="font-mono">£{playerInfo.player.current_price.toFixed(1)}m</span>
                </p>
              </div>
              <button
                onClick={onClose}
                className="ml-3 grid h-8 w-8 shrink-0 place-items-center rounded-full border border-slate-200 text-slate-500 transition hover:border-rose-300 hover:text-rose-600 active:scale-[.97]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Status / news banner */}
            {(playerInfo.player.status !== "a" || playerInfo.player.news) && (
              <div className="flex items-start gap-2 border-b border-amber-200 bg-amber-50 px-5 py-3">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                <div>
                  {playerInfo.player.status !== "a" && (
                    <p className="text-[11px] font-bold uppercase tracking-wide text-amber-700">
                      {playerInfo.player.status === "d" ? `Doubtful · ${playerInfo.player.chance_of_playing_next_round ?? 75}% chance` :
                       playerInfo.player.status === "i" ? "Injured" :
                       playerInfo.player.status === "s" ? "Suspended" : "Unavailable"}
                    </p>
                  )}
                  {playerInfo.player.news && (
                    <p className="mt-0.5 text-[11px] leading-5 text-amber-800">{playerInfo.player.news}</p>
                  )}
                </div>
              </div>
            )}

            {/* Key metrics strip */}
            <div className="grid grid-cols-4 divide-x divide-slate-200 border-b border-slate-200">
              {[
                { label: "xP", value: playerInfo.proj.mean_xp.toFixed(1), tone: "indigo" },
                { label: "xMins", value: Math.round(playerInfo.proj.xmins).toString(), tone: "default" },
                { label: "Start%", value: `${Math.round(playerInfo.proj.start_probability * 100)}%`, tone: "default" },
                { label: "P90", value: playerInfo.proj.p90_xp?.toFixed(1) ?? "—", tone: "emerald" },
              ].map(({ label, value, tone }) => (
                <div key={label} className="flex flex-col items-center py-4">
                  <span className="text-[9px] font-bold uppercase tracking-[.14em] text-slate-400">{label}</span>
                  <span className={`mt-1 font-mono text-base font-semibold tabular-nums ${tone === "indigo" ? "text-indigo-600" : tone === "emerald" ? "text-emerald-600" : "text-slate-800"}`}>
                    {value}
                  </span>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-200">
              {(["xp", "fixtures", "stats"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`relative flex h-10 flex-1 items-center justify-center gap-1.5 text-xs font-semibold transition ${activeTab === tab ? "text-indigo-700" : "text-slate-500 hover:text-slate-900"}`}
                >
                  {tab === "xp" && <BarChart2 className="h-3.5 w-3.5" />}
                  {tab === "fixtures" && <Calendar className="h-3.5 w-3.5" />}
                  {tab === "stats" && <Activity className="h-3.5 w-3.5" />}
                  {tab === "xp" ? "xP Breakdown" : tab === "fixtures" ? "Fixtures" : "Season Stats"}
                  {activeTab === tab && (
                    <motion.span layoutId="inspector-tab" className="absolute inset-x-3 bottom-0 h-0.5 bg-indigo-600" />
                  )}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto p-5">
              <AnimatePresence mode="wait">
                {activeTab === "xp" && (
                  <motion.div key="xp" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-5">
                    {/* P10 → P90 range bar */}
                    <div className="space-y-2">
                      <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">Expected Points Range</p>
                      <div className="relative h-3 rounded-full bg-slate-100">
                        <div
                          className="absolute h-3 rounded-full bg-gradient-to-r from-indigo-200 via-indigo-400 to-indigo-600"
                          style={{
                            left: `${Math.max(0, ((playerInfo.proj.p10_xp ?? 0) / Math.max(1, (playerInfo.proj.p90_xp ?? 12))) * 100)}%`,
                            right: 0,
                          }}
                        />
                      </div>
                      <div className="flex justify-between font-mono text-[10px] tabular-nums text-slate-500">
                        <span>Floor {playerInfo.proj.p10_xp?.toFixed(1) ?? "—"}</span>
                        <span className="font-semibold text-indigo-600">{playerInfo.proj.mean_xp.toFixed(1)} mean</span>
                        <span>Ceiling {playerInfo.proj.p90_xp?.toFixed(1) ?? "—"}</span>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">Component Breakdown</p>
                      <XpBar label="Goal contribution" value={playerInfo.proj.goal_xp ?? 0} total={playerInfo.proj.mean_xp} color="bg-indigo-500" />
                      <XpBar label="Assist contribution" value={playerInfo.proj.assist_xp ?? 0} total={playerInfo.proj.mean_xp} color="bg-violet-400" />
                      <XpBar label="Clean sheet" value={playerInfo.proj.clean_sheet_xp ?? 0} total={playerInfo.proj.mean_xp} color="bg-emerald-500" />
                      <XpBar label="Save points" value={playerInfo.proj.save_xp ?? 0} total={playerInfo.proj.mean_xp} color="bg-sky-400" />
                      <XpBar label="Bonus points" value={playerInfo.proj.bonus_xp ?? 0} total={playerInfo.proj.mean_xp} color="bg-amber-400" />
                    </div>

                    <div className="rounded border border-slate-200 bg-slate-50 p-3">
                      <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">Pricing</p>
                      <div className="mt-2 flex items-center justify-between text-xs">
                        <span className="text-slate-600">Purchase price</span>
                        <span className="font-mono font-semibold tabular-nums text-slate-800">£{playerInfo.squadPlayer.purchase_price.toFixed(1)}m</span>
                      </div>
                      <div className="mt-1 flex items-center justify-between text-xs">
                        <span className="text-slate-600">Selling price</span>
                        <span className="font-mono font-semibold tabular-nums text-slate-800">£{playerInfo.squadPlayer.selling_price.toFixed(1)}m</span>
                      </div>
                      <div className="mt-1 flex items-center justify-between text-xs">
                        <span className="text-slate-600">Current value</span>
                        <span className="font-mono font-semibold tabular-nums text-indigo-600">£{playerInfo.player.current_price.toFixed(1)}m</span>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === "fixtures" && (
                  <motion.div key="fixtures" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-2">
                    <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">Upcoming Fixtures</p>
                    {fixtures
                      .filter(f => !f.finished && (f.home_team_id === playerInfo.player.team_id || f.away_team_id === playerInfo.player.team_id))
                      .sort((a, b) => a.gameweek - b.gameweek)
                      .slice(0, 8)
                      .map(f => {
                        const isHome = f.home_team_id === playerInfo.player.team_id;
                        const oppId = isHome ? f.away_team_id : f.home_team_id;
                        const opp = teamsDict[oppId];
                        const fdr = isHome ? f.difficulty_home : f.difficulty_away;
                        return (
                          <div key={f.fixture_id} className="flex items-center justify-between rounded border border-slate-100 bg-slate-50 px-3 py-2.5">
                            <div className="flex items-center gap-3">
                              <span className="w-8 font-mono text-[10px] font-bold tabular-nums text-slate-400">GW{f.gameweek}</span>
                              <span className="text-xs font-semibold text-slate-800">
                                {opp?.name ?? `Team ${oppId}`}
                              </span>
                              <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold ${isHome ? "bg-slate-100 text-slate-600" : "bg-white text-slate-500 border border-slate-200"}`}>
                                {isHome ? "H" : "A"}
                              </span>
                            </div>
                            <span className={`rounded border px-2 py-0.5 text-[10px] font-bold ${fdrColor(fdr)}`}>
                              {fdr}
                            </span>
                          </div>
                        );
                      })}
                  </motion.div>
                )}

                {activeTab === "stats" && (
                  <motion.div key="stats" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-3">
                    <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">2024/25 Season</p>
                    {[
                      { label: "Minutes played", value: playerInfo.player.minutes ?? "—" },
                      { label: "Starts", value: playerInfo.player.starts ?? "—" },
                      { label: "Total FPL points", value: playerInfo.player.total_points ?? "—" },
                      { label: "Points per game", value: playerInfo.player.points_per_game?.toFixed(1) ?? "—" },
                      { label: "Form (last 5 GW)", value: playerInfo.player.form?.toFixed(1) ?? "—" },
                      { label: "Selected by", value: playerInfo.player.selected_by_pct ? `${playerInfo.player.selected_by_pct.toFixed(1)}%` : "—" },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                        <span className="text-xs text-slate-600">{label}</span>
                        <span className="font-mono text-xs font-semibold tabular-nums text-slate-800">{String(value)}</span>
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
};
