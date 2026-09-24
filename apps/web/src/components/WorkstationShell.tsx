import React from "react";
import { motion } from "framer-motion";
import { BarChart3, CalendarRange, ChevronDown, Command, PanelRightClose, PanelRightOpen, RefreshCw, Target } from "lucide-react";
import { BrandMark } from "@/components/BrandMark";

type WorkspaceTab = "pitch" | "horizon" | "analytics";

interface WorkstationShellProps {
  managerState: any;
  liveStatus: any;
  managerId: number;
  currentGw: number;
  activeTab: WorkspaceTab;
  setActiveTab: (tab: WorkspaceTab) => void;
  dockOpen: boolean;
  setDockOpen: (open: boolean) => void;
  isRefreshing?: boolean;
  onRefresh: () => void;
  onExit: () => void;
  children: React.ReactNode;
  optimizationResult?: any;
  playersDict?: Record<number, any>;
  projectionsDict?: Record<number, any>;
}

const compact = new Intl.NumberFormat("en-GB", { notation: "compact", maximumFractionDigits: 1 });

export function WorkstationShell({
  managerState,
  liveStatus,
  managerId,
  currentGw,
  activeTab,
  setActiveTab,
  dockOpen,
  setDockOpen,
  isRefreshing,
  onRefresh,
  onExit,
  children,
  optimizationResult,
  playersDict,
  projectionsDict,
}: WorkstationShellProps) {
  const score = managerState?.team_score ?? 82;
  const bank = Number(managerState?.bank ?? 0);
  const freeTransfers = managerState?.free_transfers ?? 1;
  const rank = managerState?.overall_rank ?? 0;

  return (
    <motion.main initial={{ opacity: 0, scale: 0.99 }} animate={{ opacity: 1, scale: 1 }} transition={{ type: "spring", stiffness: 400, damping: 30 }} className="min-h-screen bg-slate-50 text-slate-950">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur-xl">
        <div className="flex h-14 items-center gap-3 px-4 lg:px-6">
          <button onClick={onExit} className="flex shrink-0 items-center gap-2.5 pr-3 text-left transition active:scale-[.98]"><BrandMark className="h-7 w-7" /><span className="hidden text-sm font-semibold tracking-tight sm:block">FPL Edge</span></button>
          <div className="hidden h-5 w-px bg-slate-200 sm:block" />
          <button className="hidden items-center gap-2 text-xs font-medium text-slate-600 sm:flex">{managerState?.team_name || `Manager ${managerId}`} <ChevronDown className="h-3.5 w-3.5" /></button>
          <div className="ml-auto flex h-full items-center divide-x divide-slate-200 overflow-x-auto">
            <Metric label="Live GW" value={String(currentGw)} tone="indigo" />
            <Metric label="Rank" value={rank ? compact.format(rank) : "—"} delta={managerState?.rank_delta} />
            <Metric label="Bank" value={`£${bank.toFixed(1)}m`} />
            <Metric label="Free transfers" value={String(Math.min(5, freeTransfers))} />
            <Metric label="Team score" value={String(score)} tone="emerald" suffix="/100" />
          </div>
          <button onClick={onRefresh} aria-label="Refresh live data" className="ml-2 grid h-8 w-8 shrink-0 place-items-center border border-slate-200 text-slate-500 transition hover:border-indigo-300 hover:text-indigo-600 active:scale-[.98]"><RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} /></button>
        </div>
      </header>

      <div className="border-b border-slate-200 bg-white px-4 lg:px-6"><div className="flex h-12 items-center gap-1">
        {([["pitch", "Squad", Target], ["horizon", "5-GW horizon", CalendarRange], ["analytics", "Analytics", BarChart3]] as const).map(([id, label, Icon]) => (
          <button key={id} onClick={() => setActiveTab(id)} className={`relative flex h-full items-center gap-2 px-3 text-xs font-semibold transition active:scale-[.98] ${activeTab === id ? "text-indigo-700" : "text-slate-500 hover:text-slate-900"}`}><Icon className="h-3.5 w-3.5" /> {label}{activeTab === id && <motion.span layoutId="workstation-tab" className="absolute inset-x-2 bottom-0 h-0.5 bg-indigo-600" />}</button>
        ))}
        <div className="ml-auto flex items-center gap-1">
          <button className="hidden items-center gap-2 px-3 py-2 text-xs font-medium text-slate-500 hover:text-indigo-600 md:flex"><Command className="h-3.5 w-3.5" /> Search <kbd className="border border-slate-200 bg-slate-50 px-1.5 font-mono text-[10px]">⌘K</kbd></button>
          <button onClick={() => setDockOpen(!dockOpen)} className="grid h-8 w-8 place-items-center text-slate-500 transition hover:text-indigo-600 active:scale-[.98]" aria-label={dockOpen ? "Hide analytics dock" : "Show analytics dock"}>{dockOpen ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}</button>
        </div>
      </div></div>

      <div className={`grid min-h-[calc(100vh-6.5rem)] ${dockOpen ? "xl:grid-cols-[minmax(0,7fr)_minmax(290px,3fr)]" : "grid-cols-1"}`}>
        <section className="min-w-0 p-4 lg:p-6">{children}</section>
        {dockOpen && <AnalyticsPreview liveStatus={liveStatus} managerState={managerState} optimizationResult={optimizationResult} playersDict={playersDict} projectionsDict={projectionsDict} />}
      </div>
    </motion.main>
  );
}

function Metric({ label, value, delta, tone, suffix }: { label: string; value: string; delta?: number; tone?: "indigo" | "emerald"; suffix?: string }) {
  return <div className="flex h-full min-w-max items-center gap-2 px-3"><span className="hidden text-[9px] font-bold uppercase tracking-[.13em] text-slate-400 lg:block">{label}</span><span className={`font-mono text-xs font-semibold tabular-nums ${tone === "indigo" ? "text-indigo-600" : tone === "emerald" ? "text-emerald-600" : "text-slate-800"}`}>{value}<span className="text-[9px] text-slate-400">{suffix}</span></span>{typeof delta === "number" && <span className={`font-mono text-[9px] tabular-nums ${delta >= 0 ? "text-emerald-600" : "text-rose-600"}`}>{delta >= 0 ? "▲" : "▼"}{compact.format(Math.abs(delta))}</span>}</div>;
}

function AnalyticsPreview({ liveStatus, managerState, optimizationResult, playersDict, projectionsDict }: {
  liveStatus: any; managerState: any; optimizationResult: any;
  playersDict?: Record<number, any>; projectionsDict?: Record<number, any>;
}) {
  const topPlan = optimizationResult?.plans?.[0];
  const gw1 = topPlan?.gameweeks?.[0];
  const captainId = gw1?.captain;
  const capPlayer = captainId && playersDict ? playersDict[captainId] : null;
  const capProj = captainId && projectionsDict ? projectionsDict[captainId] : null;
  const transferIn = gw1?.transfers_in?.[0];
  const transferOut = gw1?.transfers_out?.[0];
  const inPlayer = transferIn && playersDict ? playersDict[transferIn] : null;
  const outPlayer = transferOut && playersDict ? playersDict[transferOut] : null;

  const bank = Number(managerState?.bank ?? 0);
  const ft = managerState?.free_transfers ?? 1;
  const rank = managerState?.overall_rank ?? 0;
  const points = managerState?.overall_points ?? 0;

  const deadline = liveStatus?.current_deadline ? new Date(liveStatus.current_deadline) : null;
  const deadlineStr = deadline
    ? deadline.toLocaleString("en-GB", { weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
    : null;

  const compact = new Intl.NumberFormat("en-GB", { notation: "compact", maximumFractionDigits: 1 });

  return (
    <aside className="border-l border-slate-200 bg-white">
      {/* Status dot + header */}
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[.16em] text-slate-400">Decision dock</p>
          <h2 className="mt-1 text-sm font-semibold text-slate-900">Live context</h2>
        </div>
        <div className={`flex items-center gap-1.5`}>
          <span className={`h-2 w-2 rounded-full ${liveStatus ? "bg-emerald-500" : "bg-amber-400"}`} />
          <span className="text-[10px] font-medium text-slate-400">{liveStatus ? "Live" : "Connecting"}</span>
        </div>
      </div>

      {/* Captain recommendation */}
      {capPlayer && capProj && (
        <div className="border-b border-slate-200 p-4">
          <p className="text-[9px] font-bold uppercase tracking-[.15em] text-slate-400">Captain pick</p>
          <div className="mt-3 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">{capPlayer.web_name}</p>
              <p className="mt-0.5 text-[10px] text-slate-500">{capPlayer.position} · {teamsLabel(capPlayer)}</p>
            </div>
            <div className="text-right">
              <p className="font-mono text-base font-semibold tabular-nums text-amber-600">{(capProj.mean_xp * 2).toFixed(1)}</p>
              <p className="text-[9px] text-slate-400">cap xP</p>
            </div>
          </div>
        </div>
      )}

      {/* Top transfer */}
      {inPlayer && outPlayer && (
        <div className="border-b border-slate-200 p-4">
          <p className="text-[9px] font-bold uppercase tracking-[.15em] text-slate-400">Top transfer</p>
          <div className="mt-3 space-y-1.5">
            <div className="flex items-center gap-2 rounded border border-rose-200 bg-rose-50 px-3 py-1.5">
              <span className="text-[9px] font-bold text-rose-500">OUT</span>
              <span className="text-xs font-semibold text-rose-700">{outPlayer.web_name}</span>
            </div>
            <div className="flex items-center gap-2 rounded border border-emerald-200 bg-emerald-50 px-3 py-1.5">
              <span className="text-[9px] font-bold text-emerald-600">IN</span>
              <span className="text-xs font-semibold text-emerald-700">{inPlayer.web_name}</span>
            </div>
          </div>
          {topPlan?.gain_vs_hold !== undefined && (
            <p className="mt-2 font-mono text-[10px] tabular-nums text-slate-500">
              +{Number(topPlan.gain_vs_hold).toFixed(1)} xP vs hold
            </p>
          )}
        </div>
      )}

      {/* Key squad metrics */}
      <div className="grid grid-cols-2 divide-x divide-y divide-slate-200 border-b border-slate-200">
        <DockMetric label="Bank" value={`£${bank.toFixed(1)}m`} />
        <DockMetric label="Free transfers" value={`${Math.min(5, ft)}/5`} />
        <DockMetric label="Overall pts" value={points ? String(points) : "—"} />
        <DockMetric label="Overall rank" value={rank ? compact.format(rank) : "—"} />
      </div>

      {/* Deadline */}
      {deadlineStr && (
        <div className="border-b border-slate-200 p-4">
          <p className="text-[9px] font-bold uppercase tracking-[.15em] text-slate-400">Next deadline</p>
          <p className="mt-2 font-mono text-sm font-semibold tabular-nums text-slate-900">{deadlineStr}</p>
        </div>
      )}

      {/* Optimization xP */}
      {topPlan && (
        <div className="p-4">
          <p className="text-[9px] font-bold uppercase tracking-[.15em] text-slate-400">Projected GW score</p>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="font-mono text-2xl font-semibold tabular-nums text-indigo-600">
              {Number(topPlan.expected_points).toFixed(1)}
            </span>
            <span className="text-[10px] font-medium text-slate-400">xP</span>
          </div>
          <p className="mt-1 font-mono text-[10px] tabular-nums text-emerald-600">
            +{Number(topPlan.gain_vs_hold).toFixed(1)} above baseline
          </p>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-indigo-500"
              style={{ width: `${Math.min(100, (Number(topPlan.expected_points) / Math.max(1, Number(topPlan.expected_points) * 1.25)) * 100)}%` }}
            />
          </div>
        </div>
      )}
    </aside>
  );
}

function teamsLabel(player: any) {
  return player?.team_id ? `Team ${player.team_id}` : "Unknown";
}

function DockMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-4">
      <p className="text-[9px] font-bold uppercase tracking-[.13em] text-slate-400">{label}</p>
      <p className="mt-1.5 font-mono text-sm font-semibold tabular-nums text-slate-800">{value}</p>
    </div>
  );
}

