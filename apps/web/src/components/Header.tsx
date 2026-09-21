import React, { useState } from "react";
import { Clock, RefreshCw, Search, ShieldCheck, AlertTriangle, CheckCircle2 } from "lucide-react";

interface HeaderProps {
  managerId: number;
  onImportTeam: (id: number) => void;
  onSwitchToDemo: () => void;
  teamName: string;
  managerName: string;
  overallRank: number;
  totalPoints: number;
  currentGameweek: number;
  deadlineTime: string;
  dataMode: "live" | "demo";
  confirmedFT: number | null;
  ftConfirmed: boolean;
  onConfirmFT: (ft: number) => void;
  onRefreshData: () => void;
  managerError?: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  managerId,
  onImportTeam,
  onSwitchToDemo,
  teamName,
  managerName,
  overallRank,
  totalPoints,
  currentGameweek,
  deadlineTime,
  dataMode,
  confirmedFT,
  ftConfirmed,
  onConfirmFT,
  onRefreshData,
  managerError,
}) => {
  const [inputVal, setInputVal] = useState("");
  const [ftInput, setFtInput] = useState<string>(confirmedFT !== null ? String(confirmedFT) : "1");

  const handleImport = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(inputVal.trim(), 10);
    if (!isNaN(parsed) && parsed > 0) {
      onImportTeam(parsed);
    }
  };

  const handleConfirmFT = () => {
    const parsed = parseInt(ftInput, 10);
    if (!isNaN(parsed) && parsed >= 1 && parsed <= 5) {
      onConfirmFT(parsed);
    }
  };

  const formattedDeadline = deadlineTime
    ? new Date(deadlineTime).toLocaleDateString([], { weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
    : "—";

  return (
    <header className="bg-surface/80 backdrop-blur-md border-b border-surfaceBorder sticky top-0 z-20 px-6 py-4">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Gameweek & Manager Overview */}
        <div className="flex items-center gap-6">
          {/* Gameweek Badge */}
          <div className="bg-surfaceHover px-4 py-2 rounded-xl border border-surfaceBorder shrink-0">
            <div className="text-xs text-slate-400 font-medium">GAMEWEEK {currentGameweek}</div>
            <div className="flex items-center gap-1.5 text-primary text-sm font-semibold mt-0.5">
              <Clock className="w-4 h-4" />
              <span>{formattedDeadline}</span>
            </div>
          </div>

          {/* Manager Info */}
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100">{teamName}</h2>
              {dataMode === "demo" ? (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  DEMO
                </span>
              ) : managerId > 0 ? (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> OFFICIAL FPL
                </span>
              ) : null}
            </div>
            {managerId > 0 && (
              <div className="flex items-center gap-4 text-xs text-slate-400 font-medium mt-1">
                <span>Manager: <strong className="text-slate-200">{managerName}</strong></span>
                {overallRank > 0 && (
                  <span>Rank: <strong className="text-primary font-mono">#{overallRank.toLocaleString()}</strong></span>
                )}
                {totalPoints > 0 && (
                  <span>Pts: <strong className="text-slate-200 font-mono">{totalPoints}</strong></span>
                )}
              </div>
            )}
            {!managerId && dataMode === "live" && (
              <div className="text-xs text-slate-500 mt-1">Enter your FPL Team ID to import your squad</div>
            )}
            {managerError && (
              <div className="text-xs text-red-400 mt-1 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> {managerError}
              </div>
            )}
          </div>
        </div>

        {/* Right: Controls */}
        <div className="flex flex-wrap items-center gap-3">

          {/* FT Confirmation (only when manager loaded, live mode, and FT not yet confirmed) */}
          {managerId > 0 && dataMode === "live" && !ftConfirmed && (
            <div className="flex items-center gap-2 bg-amber-950/40 border border-amber-600/40 rounded-xl px-3 py-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="text-xs text-amber-300">Free Transfers:</span>
              <input
                type="number"
                min={1}
                max={5}
                value={ftInput}
                onChange={e => setFtInput(e.target.value)}
                className="bg-background w-12 text-center text-sm text-amber-200 border border-amber-600/50 rounded-lg px-1 py-1 font-mono"
              />
              <button
                onClick={handleConfirmFT}
                className="bg-amber-500 hover:bg-amber-400 text-slate-900 px-3 py-1 rounded-lg text-xs font-bold transition-colors flex items-center gap-1"
              >
                <CheckCircle2 className="w-3.5 h-3.5" /> Confirm
              </button>
            </div>
          )}

          {/* FT confirmed badge */}
          {managerId > 0 && ftConfirmed && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-900/30 border border-emerald-600/30 rounded-xl px-3 py-2">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{confirmedFT} FT Confirmed</span>
            </div>
          )}

          {/* Team import form */}
          <form onSubmit={handleImport} className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Enter FPL Team ID..."
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                className="bg-background text-sm text-slate-200 pl-9 pr-3 py-2 rounded-xl border border-surfaceBorder focus:outline-none focus:border-primary w-48"
              />
            </div>
            <button
              type="submit"
              className="bg-primary hover:bg-primary-hover text-slate-950 px-4 py-2 rounded-xl text-sm font-semibold transition-colors"
            >
              Import Team
            </button>
          </form>

          {/* Demo toggle */}
          <button
            onClick={onSwitchToDemo}
            className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${
              dataMode === "demo"
                ? "bg-amber-500/20 text-amber-400 border-amber-500/40"
                : "bg-surfaceHover text-slate-300 border-surfaceBorder hover:border-slate-500"
            }`}
          >
            {dataMode === "demo" ? "▶ In Demo Mode" : "Try Demo Squad"}
          </button>

          {/* Refresh button */}
          <button
            onClick={onRefreshData}
            title="Refresh Live Snapshot"
            className="p-2.5 rounded-xl bg-surfaceHover text-slate-400 hover:text-slate-100 hover:bg-surfaceBorder border border-surfaceBorder transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
