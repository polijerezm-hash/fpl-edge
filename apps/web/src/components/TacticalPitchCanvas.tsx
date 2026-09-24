import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Crown, ChevronDown, ChevronUp, Info, ZapOff } from "lucide-react";

interface SquadPlayer {
  player_id: number;
  position: string;
  purchase_price: number;
  selling_price: number;
  starting: boolean;
  captain: boolean;
  vice_captain: boolean;
  multiplier: number;
}

interface PlayerData {
  player_id: number;
  web_name: string;
  team_id: number;
  position: string;
  current_price: number;
  status: string;
  news?: string;
  chance_of_playing_next_round?: number;
  minutes?: number;
  starts?: number;
  form?: number;
}

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

interface TacticalPitchProps {
  managerState: any;
  playersDict: Record<number, PlayerData>;
  projectionsDict: Record<number, Projection>;
  teamsDict: Record<number, Team>;
  fixtures: Fixture[];
  currentGw: number;
  onSelectPlayer: (info: { player: PlayerData; squadPlayer: SquadPlayer; proj: Projection }) => void;
}

// FDR colour mapping
const fdrColor = (d: number) => {
  if (d <= 2) return "bg-emerald-100 text-emerald-800";
  if (d === 3) return "bg-amber-100 text-amber-800";
  return "bg-rose-100 text-rose-800";
};

// xMins ring colour
function xMinsRingColor(prob: number): string {
  if (prob >= 0.85) return "#10b981"; // emerald
  if (prob >= 0.60) return "#f59e0b"; // amber
  return "#f43f5e"; // rose
}

function xMinsStrokeDasharray(prob: number) {
  const pct = Math.min(1, Math.max(0, prob));
  const C = 2 * Math.PI * 18; // radius 18
  return `${pct * C} ${C}`;
}

const statusBadge = (status: string, cop?: number) => {
  if (status === "i") return { label: "INJ", cls: "bg-rose-100 text-rose-700" };
  if (status === "s") return { label: "SUS", cls: "bg-amber-100 text-amber-700" };
  if (status === "u") return { label: "N/A", cls: "bg-slate-200 text-slate-500" };
  if (status === "d") return { label: `${cop ?? 75}%`, cls: "bg-amber-100 text-amber-700" };
  return null;
};

function PlayerNode({
  squadPlayer,
  player,
  proj,
  upcomingFixtures,
  onClick,
}: {
  squadPlayer: SquadPlayer;
  player: PlayerData;
  proj: Projection;
  upcomingFixtures: Array<{ opponentShort: string; isHome: boolean; fdr: number }>;
  onClick: () => void;
}) {
  const prob = proj.start_probability;
  const xp = proj.mean_xp;
  const badge = statusBadge(player.status, player.chance_of_playing_next_round);
  const ringColor = xMinsRingColor(prob);
  const dash = xMinsStrokeDasharray(prob);

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ y: -3, scale: 1.02 }}
      whileTap={{ scale: 0.97 }}
      transition={{ type: "spring", stiffness: 400, damping: 28 }}
      className="relative flex flex-col items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
    >
      {/* Captain / Vice-Captain badges */}
      {squadPlayer.captain && (
        <span className="absolute -top-2.5 -right-2.5 z-10 flex h-5 w-5 items-center justify-center rounded-full border-2 border-white bg-amber-400 text-[9px] font-black text-slate-950 shadow-md">
          C
        </span>
      )}
      {squadPlayer.vice_captain && !squadPlayer.captain && (
        <span className="absolute -top-2.5 -right-2.5 z-10 flex h-5 w-5 items-center justify-center rounded-full border-2 border-white bg-slate-400 text-[9px] font-black text-slate-950 shadow-md">
          V
        </span>
      )}

      {/* xMins ring + avatar */}
      <div className="relative">
        <svg width="44" height="44" className="-rotate-90">
          <circle cx="22" cy="22" r="18" fill="none" stroke="#e2e8f0" strokeWidth="3.5" />
          <circle
            cx="22" cy="22" r="18"
            fill="none"
            stroke={ringColor}
            strokeWidth="3.5"
            strokeDasharray={dash}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white shadow-sm border border-slate-200">
            <span className="font-mono text-[10px] font-bold tabular-nums text-indigo-700">
              {xp > 0 ? xp.toFixed(1) : "—"}
            </span>
          </div>
        </div>
      </div>

      {/* Name pill */}
      <div className="max-w-[80px] rounded-sm border border-slate-200 bg-white/95 px-1.5 py-0.5 shadow-sm text-center">
        <p className="truncate text-[10px] font-semibold leading-none text-slate-900">
          {player.web_name}
        </p>
        <p className="mt-0.5 font-mono text-[9px] tabular-nums text-slate-500">
          £{player.current_price.toFixed(1)}m
        </p>
      </div>

      {/* Status badge */}
      {badge && (
        <span className={`rounded px-1.5 py-0.5 text-[8px] font-bold ${badge.cls}`}>
          {badge.label}
        </span>
      )}

      {/* FDR strip */}
      {upcomingFixtures.length > 0 && (
        <div className="flex items-center gap-0.5">
          {upcomingFixtures.slice(0, 3).map((f, i) => (
            <span
              key={i}
              className={`rounded px-1 py-0.5 text-[8px] font-bold leading-none ${fdrColor(f.fdr)}`}
            >
              {f.opponentShort}{f.isHome ? "" : "(A)"}
            </span>
          ))}
        </div>
      )}
    </motion.button>
  );
}

function PlayerRow({
  picks,
  managerState,
  playersDict,
  projectionsDict,
  teamsDict,
  fixtures,
  currentGw,
  onSelectPlayer,
}: {
  picks: SquadPlayer[];
  managerState: any;
  playersDict: Record<number, PlayerData>;
  projectionsDict: Record<number, Projection>;
  teamsDict: Record<number, Team>;
  fixtures: Fixture[];
  currentGw: number;
  onSelectPlayer: TacticalPitchProps["onSelectPlayer"];
}) {
  return (
    <div className={`flex flex-wrap items-start justify-center gap-4`}>
      {picks.map((sp) => {
        const player = playersDict[sp.player_id] ?? {
          player_id: sp.player_id,
          web_name: `#${sp.player_id}`,
          team_id: 0,
          position: sp.position,
          current_price: sp.purchase_price,
          status: "a",
        };
        const proj = projectionsDict[sp.player_id] ?? {
          player_id: sp.player_id,
          mean_xp: 4.2,
          xmins: 80,
          start_probability: 0.85,
        };

        // Build upcoming fixtures for this player's team
        const upcomingFixtures = fixtures
          .filter(
            (f) =>
              !f.finished &&
              f.gameweek >= currentGw &&
              (f.home_team_id === player.team_id || f.away_team_id === player.team_id)
          )
          .sort((a, b) => a.gameweek - b.gameweek)
          .slice(0, 3)
          .map((f) => {
            const isHome = f.home_team_id === player.team_id;
            const oppId = isHome ? f.away_team_id : f.home_team_id;
            const opp = teamsDict[oppId];
            return {
              opponentShort: opp?.short_name ?? "?",
              isHome,
              fdr: isHome ? f.difficulty_home : f.difficulty_away,
            };
          });

        return (
          <PlayerNode
            key={sp.player_id}
            squadPlayer={sp}
            player={player as PlayerData}
            proj={proj}
            upcomingFixtures={upcomingFixtures}
            onClick={() => onSelectPlayer({ player: player as PlayerData, squadPlayer: sp, proj })}
          />
        );
      })}
    </div>
  );
}

export const TacticalPitchCanvas: React.FC<TacticalPitchProps> = ({
  managerState,
  playersDict,
  projectionsDict,
  teamsDict,
  fixtures,
  currentGw,
  onSelectPlayer,
}) => {
  const [showBench, setShowBench] = useState(true);
  const squad: SquadPlayer[] = managerState?.squad ?? [];

  const starters = squad.filter((s) => s.starting);
  const bench = squad.filter((s) => !s.starting);

  const gkp = starters.filter((s) => s.position === "GKP");
  const def = starters.filter((s) => s.position === "DEF");
  const mid = starters.filter((s) => s.position === "MID");
  const fwd = starters.filter((s) => s.position === "FWD");

  const rowProps = { managerState, playersDict, projectionsDict, teamsDict, fixtures, currentGw, onSelectPlayer };

  const totalXp = starters.reduce((sum, sp) => {
    const proj = projectionsDict[sp.player_id];
    const base = proj?.mean_xp ?? 0;
    const mult = sp.captain ? 2 : 1;
    return sum + base * mult;
  }, 0);

  if (!squad.length) {
    return (
      <div className="flex min-h-[480px] items-center justify-center border border-slate-200 bg-white">
        <div className="text-center">
          <ZapOff className="mx-auto h-8 w-8 text-slate-300" />
          <p className="mt-3 text-sm font-medium text-slate-500">Squad data loading…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Canvas header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-[10px] font-semibold text-slate-500">85%+ starts</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
            <span className="text-[10px] font-semibold text-slate-500">60–84%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full bg-rose-500" />
            <span className="text-[10px] font-semibold text-slate-500">&lt;60%</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold text-slate-500">Formation</span>
          <span className="font-mono text-[10px] font-bold tabular-nums text-indigo-600">
            {def.length}-{mid.length}-{fwd.length}
          </span>
          <span className="mx-2 h-4 w-px bg-slate-200" />
          <span className="text-[10px] font-semibold text-slate-500">Total XI xP</span>
          <span className="font-mono text-[10px] font-bold tabular-nums text-slate-900">
            {totalXp.toFixed(1)}
          </span>
        </div>
      </div>

      {/* Pitch */}
      <div className="relative overflow-hidden border border-slate-200 bg-[#e9f7ef] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.5)]">
        {/* Pitch markings */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute inset-4 border border-emerald-700/20" />
          <div className="absolute left-1/2 top-4 h-[calc(100%-2rem)] border-l border-emerald-700/15" />
          <div className="absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full border border-emerald-700/15" />
          <div className="absolute left-1/4 right-1/4 top-4 h-12 border border-t-0 border-emerald-700/15" />
          <div className="absolute bottom-4 left-1/4 right-1/4 h-12 border border-b-0 border-emerald-700/15" />
        </div>

        <div className="relative z-10 space-y-8 px-6 py-10">
          <PlayerRow picks={gkp} {...rowProps} />
          <PlayerRow picks={def} {...rowProps} />
          <PlayerRow picks={mid} {...rowProps} />
          <PlayerRow picks={fwd} {...rowProps} />
        </div>
      </div>

      {/* Bench toggle */}
      <button
        onClick={() => setShowBench(!showBench)}
        className="flex w-full items-center justify-between border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700 active:scale-[.99]"
      >
        <div className="flex items-center gap-2">
          <Info className="h-3.5 w-3.5 text-slate-400" />
          Substitutes bench · {bench.length} players
        </div>
        {showBench ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      <AnimatePresence>
        {showBench && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 35 }}
            className="overflow-hidden"
          >
            <div className="border border-t-0 border-slate-200 bg-slate-50 px-6 py-6">
              <div className="flex flex-wrap items-start justify-center gap-6">
                {bench.map((sp) => {
                  const player = playersDict[sp.player_id] ?? {
                    player_id: sp.player_id,
                    web_name: `#${sp.player_id}`,
                    team_id: 0,
                    position: sp.position,
                    current_price: sp.purchase_price,
                    status: "a",
                  };
                  const proj = projectionsDict[sp.player_id] ?? {
                    player_id: sp.player_id,
                    mean_xp: 2.5,
                    xmins: 40,
                    start_probability: 0.35,
                  };
                  const upcomingFixtures = fixtures
                    .filter((f) => !f.finished && f.gameweek >= currentGw && (f.home_team_id === player.team_id || f.away_team_id === player.team_id))
                    .sort((a, b) => a.gameweek - b.gameweek)
                    .slice(0, 3)
                    .map((f) => {
                      const isHome = f.home_team_id === player.team_id;
                      const oppId = isHome ? f.away_team_id : f.home_team_id;
                      const opp = teamsDict[oppId];
                      return { opponentShort: opp?.short_name ?? "?", isHome, fdr: isHome ? f.difficulty_home : f.difficulty_away };
                    });
                  return (
                    <PlayerNode
                      key={sp.player_id}
                      squadPlayer={sp}
                      player={player as PlayerData}
                      proj={proj}
                      upcomingFixtures={upcomingFixtures}
                      onClick={() => onSelectPlayer({ player: player as PlayerData, squadPlayer: sp, proj })}
                    />
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
