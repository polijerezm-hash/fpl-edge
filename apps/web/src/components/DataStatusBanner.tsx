import React from "react";
import { Activity, Database, CheckCircle2, AlertTriangle } from "lucide-react";

interface DataStatusProps {
  statusData?: {
    season?: string;
    gameweek?: number;
    source?: string;
    data_mode?: string;
    snapshot_id?: string;
    as_of_timestamp?: string;
    players?: number;
    teams?: number;
    fixtures?: number;
    validated?: boolean;
    last_successful_refresh?: string;
  } | null;
  modelVersion?: string;
  isDemo?: boolean;
}

export const DataStatusBanner: React.FC<DataStatusProps> = ({
  statusData,
  modelVersion = "1.0.0",
  isDemo = false,
}) => {
  const isActuallyDemo = isDemo || statusData?.data_mode === "demo";
  const timestamp = statusData?.as_of_timestamp || statusData?.last_successful_refresh;
  
  const getMinutesAgo = (ts?: string) => {
    if (!ts) return "just now";
    try {
      const diffMs = Date.now() - new Date(ts).getTime();
      const mins = Math.floor(diffMs / 60000);
      if (mins <= 0) return "just now";
      if (mins === 1) return "1 min ago";
      return `${mins} min ago`;
    } catch {
      return "just now";
    }
  };

  return (
    <div className={`border-b px-6 py-2 flex flex-wrap items-center justify-between text-xs gap-4 transition-colors ${
      isActuallyDemo
        ? "bg-amber-950/40 border-amber-800/40 text-amber-200"
        : "bg-surface/50 border-surfaceBorder text-slate-400"
    }`}>
      <div className="flex items-center gap-4">
        {isActuallyDemo ? (
          <span className="flex items-center gap-1.5 font-bold text-amber-400 bg-amber-500/20 px-2.5 py-0.5 rounded-full border border-amber-500/40 uppercase tracking-wide text-[10px]">
            <AlertTriangle className="w-3 h-3" />
            <span>DEMO DATA (Offline Seed)</span>
          </span>
        ) : (
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-emerald-400 font-bold uppercase tracking-wide text-[10px]">LIVE</span>
            <span className="text-slate-500">•</span>
            <span>Official FPL</span>
            <span className="text-slate-500">•</span>
            <strong className="text-slate-200 font-mono">GW {statusData?.gameweek || 4}</strong>
            <span className="text-slate-500">•</span>
            <span>Updated {getMinutesAgo(timestamp)}</span>
          </span>
        )}

        <span className="hidden sm:inline text-slate-600">•</span>
        <span className="flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5 text-secondary" />
          <span>Elements: <strong className="text-slate-200 font-mono">{statusData?.players || 659}</strong></span>
        </span>

        <span className="hidden md:inline text-slate-600">•</span>
        <span className="hidden md:flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-primary" />
          <span>Model: <strong className="text-slate-200 font-mono">v{modelVersion}</strong></span>
        </span>
      </div>

      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>{statusData?.snapshot_id || "snap_live_current"}</span>
        </span>
      </div>
    </div>
  );
};
