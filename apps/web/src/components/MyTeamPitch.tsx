
import React from "react";
import { Crown, AlertCircle, Info } from "lucide-react";

interface MyTeamPitchProps {
  managerState: any;
  playersDict: Record<number, any>;
  projectionsDict: Record<number, any>;
  onSelectPlayer: (player: any) => void;
}

export const MyTeamPitch: React.FC<MyTeamPitchProps> = ({
  managerState,
  playersDict,
  projectionsDict,
  onSelectPlayer,
}) => {
  const squad = managerState?.squad || [];

  // Separate starters and bench
  const starters = squad.filter((s: any) => s.starting);
  const bench = squad.filter((s: any) => !s.starting);

  // Group starters by position
  const gkp = starters.filter((s: any) => s.position === "GKP");
  const def = starters.filter((s: any) => s.position === "DEF");
  const mid = starters.filter((s: any) => s.position === "MID");
  const fwd = starters.filter((s: any) => s.position === "FWD");

  const renderPlayerCard = (squadPlayer: any) => {
    const player = playersDict[squadPlayer.player_id] || {
      web_name: `Player #${squadPlayer.player_id}`,
      current_price: squadPlayer.purchase_price,
      position: squadPlayer.position,
      status: "a"
    };
    const proj = projectionsDict[squadPlayer.player_id] || { mean_xp: 4.5, xmins: 80, start_probability: 0.85 };

    const isCaptain = squadPlayer.captain;
    const isVice = squadPlayer.vice_captain;

    // Color code xP strength
    let xpBadgeColor = "bg-primary/20 text-primary border-primary/30";
    if (proj.mean_xp >= 7.0) {
      xpBadgeColor = "bg-emerald-500/30 text-emerald-300 border-emerald-500/50 shadow-lg shadow-emerald-500/20";
    } else if (proj.mean_xp < 4.0) {
      xpBadgeColor = "bg-amber-500/20 text-amber-300 border-amber-500/30";
    }

    return (
      <div
        key={squadPlayer.player_id}
        onClick={() => onSelectPlayer({ player, squadPlayer, proj })}
        className="group relative bg-surface/90 backdrop-blur-md border border-surfaceBorder hover:border-primary/60 rounded-xl p-2.5 w-28 md:w-32 text-center cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-primary/10"
      >
        {/* Badges: Captain / Vice Captain */}
        {isCaptain && (
          <span className="absolute -top-2.5 -right-2.5 bg-amber-400 text-slate-950 font-black text-xs w-6 h-6 rounded-full flex items-center justify-center border-2 border-slate-900 shadow-md">
            C
          </span>
        )}
        {isVice && (
          <span className="absolute -top-2.5 -right-2.5 bg-slate-400 text-slate-950 font-black text-xs w-6 h-6 rounded-full flex items-center justify-center border-2 border-slate-900 shadow-md">
            VC
          </span>
        )}

        {/* Player Name */}
        <div className="font-bold text-slate-100 text-xs md:text-sm truncate">
          {player.web_name}
        </div>

        {/* Price & Position */}
        <div className="text-[10px] text-slate-400 font-medium">
          £{player.current_price}m • {player.position}
        </div>

        {/* xP & xMins */}
        <div className={`mt-1.5 px-2 py-0.5 rounded-lg border text-xs font-mono font-extrabold ${xpBadgeColor}`}>
          {proj.mean_xp} xP
        </div>

        <div className="text-[9px] text-slate-400 mt-1 flex items-center justify-center gap-1">
          <span>{proj.xmins} mins</span>
          <span>•</span>
          <span>{Math.round(proj.start_probability * 100)}% start</span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto p-4 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100">Tactical Pitch View</h2>
          <p className="text-xs text-slate-400">
            Formation: <strong className="text-primary font-mono">{def.length}-{mid.length}-{fwd.length}</strong>
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span> High xP (&gt;7.0)
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span> Low / Doubtful
          </span>
        </div>
      </div>

      {/* Visual Pitch */}
      <div className="relative bg-gradient-to-b from-pitch-grass/90 via-pitch-grass to-slate-900 border-2 border-surfaceBorder rounded-3xl p-6 overflow-hidden shadow-2xl">
        {/* Pitch Lines */}
        <div className="absolute inset-0 pointer-events-none opacity-20">
          <div className="w-full h-full border-2 border-white rounded-2xl m-2"></div>
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 rounded-full border-2 border-white"></div>
        </div>

        {/* Pitch Player Rows */}
        <div className="relative z-10 space-y-8 md:space-y-12">
          {/* Goalkeeper Row */}
          <div className="flex justify-center gap-4">
            {gkp.map(renderPlayerCard)}
          </div>

          {/* Defenders Row */}
          <div className="flex justify-center flex-wrap gap-3 md:gap-6">
            {def.map(renderPlayerCard)}
          </div>

          {/* Midfielders Row */}
          <div className="flex justify-center flex-wrap gap-3 md:gap-6">
            {mid.map(renderPlayerCard)}
          </div>

          {/* Forwards Row */}
          <div className="flex justify-center flex-wrap gap-3 md:gap-6">
            {fwd.map(renderPlayerCard)}
          </div>
        </div>
      </div>

      {/* Bench Section */}
      <div className="bg-surface border border-surfaceBorder rounded-2xl p-5 space-y-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <Info className="w-4 h-4 text-slate-400" />
          <span>Substitutes Bench</span>
        </h3>

        <div className="flex justify-center flex-wrap gap-4 pt-1">
          {bench.map(renderPlayerCard)}
        </div>
      </div>
    </div>
  );
};
