import React from "react";
import { motion } from "framer-motion";
import { BarChart3, CalendarRange, ChevronDown, CircleDollarSign, Command, HelpCircle, PanelRightClose, PanelRightOpen, RefreshCw, Sparkles, Target, Trophy } from "lucide-react";
import { BrandMark } from "@/components/BrandMark";

type WorkspaceTab = "pitch" | "horizon" | "analytics";

interface WorkstationShellProps {
  managerState: any; liveStatus: any; managerId: number; currentGw: number;
  activeTab: WorkspaceTab; setActiveTab: (tab: WorkspaceTab) => void;
  dockOpen: boolean; setDockOpen: (open: boolean) => void;
  isRefreshing?: boolean; onRefresh: () => void; onExit: () => void; children: React.ReactNode;
}

const compact = new Intl.NumberFormat("en-GB", { notation: "compact", maximumFractionDigits: 1 });

export function WorkstationShell({ managerState, liveStatus, managerId, currentGw, activeTab, setActiveTab, dockOpen, setDockOpen, isRefreshing, onRefresh, onExit, children }: WorkstationShellProps) {
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
        {dockOpen && <AnalyticsPreview liveStatus={liveStatus} managerState={managerState} />}
      </div>
    </motion.main>
  );
}

function Metric({ label, value, delta, tone, suffix }: { label: string; value: string; delta?: number; tone?: "indigo" | "emerald"; suffix?: string }) {
  return <div className="flex h-full min-w-max items-center gap-2 px-3"><span className="hidden text-[9px] font-bold uppercase tracking-[.13em] text-slate-400 lg:block">{label}</span><span className={`font-mono text-xs font-semibold tabular-nums ${tone === "indigo" ? "text-indigo-600" : tone === "emerald" ? "text-emerald-600" : "text-slate-800"}`}>{value}<span className="text-[9px] text-slate-400">{suffix}</span></span>{typeof delta === "number" && <span className={`font-mono text-[9px] tabular-nums ${delta >= 0 ? "text-emerald-600" : "text-rose-600"}`}>{delta >= 0 ? "▲" : "▼"}{compact.format(Math.abs(delta))}</span>}</div>;
}

function AnalyticsPreview({ liveStatus, managerState }: { liveStatus: any; managerState: any }) {
  return <aside className="border-l border-slate-200 bg-white p-5">
    <div className="flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.16em] text-slate-400">Analytics dock</p><h2 className="mt-1 text-sm font-semibold text-slate-900">Decision context</h2></div><span className={`h-2 w-2 rounded-full ${liveStatus ? "bg-emerald-500" : "bg-amber-400"}`} /></div>
    <div className="mt-6 border-y border-slate-200 py-5"><div className="flex items-start gap-3"><div className="border border-indigo-100 bg-indigo-50 p-2 text-indigo-600"><Sparkles className="h-4 w-4" /></div><div><p className="text-xs font-semibold text-slate-900">Planner is calibrating</p><p className="mt-1 text-xs leading-5 text-slate-500">Your tactical recommendation will include minutes risk, five-week value and alternative paths.</p></div></div></div>
    <div className="grid grid-cols-2 border-b border-slate-200"><DockMetric icon={CircleDollarSign} label="Squad value" value={`£${Number(managerState?.team_value ?? 100).toFixed(1)}m`} /><DockMetric icon={Trophy} label="Overall points" value={String(managerState?.overall_points ?? "—")} /></div>
    <div className="mt-5"><p className="text-[10px] font-bold uppercase tracking-[.16em] text-slate-400">Next deadline</p><p className="mt-2 font-mono text-sm font-semibold tabular-nums text-slate-800">{liveStatus?.current_deadline ? new Date(liveStatus.current_deadline).toLocaleString("en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit" }) : "Awaiting live data"}</p></div>
    <button className="mt-6 flex w-full items-center justify-center gap-2 border border-slate-200 px-3 py-2.5 text-xs font-semibold text-slate-600 transition hover:border-indigo-300 hover:text-indigo-600 active:scale-[.98]"><HelpCircle className="h-3.5 w-3.5" /> Explain this plan</button>
  </aside>;
}

function DockMetric({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return <div className="py-4 first:border-r first:border-slate-200 first:pr-4 last:pl-4"><Icon className="h-3.5 w-3.5 text-slate-400" /><p className="mt-3 text-[9px] font-bold uppercase tracking-[.13em] text-slate-400">{label}</p><p className="mt-1 font-mono text-sm font-semibold tabular-nums text-slate-800">{value}</p></div>;
}
