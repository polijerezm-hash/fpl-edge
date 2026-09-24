import React, { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, ArrowRight, LoaderCircle, Sparkles } from "lucide-react";
import { LandingExperience } from "@/components/LandingExperience";
import { WorkstationShell } from "@/components/WorkstationShell";

type DataMode = "live" | "demo";
type WorkspaceTab = "pitch" | "horizon" | "analytics";
const getInitialDataMode = (): DataMode => typeof window !== "undefined" && new URLSearchParams(window.location.search).get("mode") === "demo" ? "demo" : "live";

export default function HomePage() {
  const [view, setView] = useState<"landing" | "workstation">("landing");
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("pitch");
  const [dockOpen, setDockOpen] = useState(true);
  const [managerId, setManagerId] = useState(0);
  const [dataMode, setDataMode] = useState<DataMode>(getInitialDataMode);
  const [liveStatus, setLiveStatus] = useState<any>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [managerState, setManagerState] = useState<any>(null);
  const [managerError, setManagerError] = useState<string | null>(null);
  const [players, setPlayers] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [fixtures, setFixtures] = useState<any[]>([]);
  const [gameweeks, setGameweeks] = useState<any[]>([]);
  const [projectionsDict, setProjectionsDict] = useState<Record<number, any>>({});
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [confirmedFT, setConfirmedFT] = useState<number | null>(null);
  const [ftConfirmed, setFtConfirmed] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/data/status?data_mode=${dataMode}`);
      if (!response.ok) throw new Error("Live FPL data is temporarily unavailable");
      setLiveStatus(await response.json()); setStatusError(null);
    } catch (error: any) { setStatusError(error.message || "Cannot reach the FPL Edge data service"); }
  }, [dataMode]);

  const fetchCoreData = useCallback(async (gameweek?: number) => {
    const targetGw = gameweek || liveStatus?.gameweek || 4;
    const responses = await Promise.all([
      fetch(`/api/players?data_mode=${dataMode}`), fetch(`/api/teams?data_mode=${dataMode}`), fetch(`/api/fixtures?data_mode=${dataMode}`),
      fetch(`/api/gameweeks?data_mode=${dataMode}`), fetch(`/api/projections?gw=${targetGw}&data_mode=${dataMode}`),
    ]);
    if (responses[0].ok) setPlayers(await responses[0].json());
    if (responses[1].ok) setTeams(await responses[1].json());
    if (responses[2].ok) setFixtures(await responses[2].json());
    if (responses[3].ok) setGameweeks(await responses[3].json());
    if (responses[4].ok) { const payload = await responses[4].json(); setProjectionsDict(Object.fromEntries((payload.projections || []).map((projection: any) => [projection.player_id, projection]))); }
  }, [dataMode, liveStatus?.gameweek]);

  const fetchManager = useCallback(async (id: number, mode: DataMode) => {
    setManagerError(null);
    try {
      const response = await fetch(`/api/team/${id}?data_mode=${mode}`);
      if (!response.ok) { const problem = await response.json().catch(() => ({})); throw new Error(problem?.message || `We could not import manager ${id}`); }
      const payload = await response.json();
      setManagerState(payload); setConfirmedFT(payload.free_transfers ?? 1); setFtConfirmed(mode === "demo" || payload.free_transfers_confirmed === true);
      return payload;
    } catch (error: any) { setManagerState(null); setManagerError(error.message || "Could not import this team"); throw error; }
  }, []);

  const fetchOptimization = useCallback(async (state: any, mode: DataMode) => {
    if (!state) return;
    try {
      const response = await fetch("/api/optimise", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
        manager_id: state.manager_id, data_mode: mode, horizon: 5, risk_profile: "balanced", confirm_free_transfers: mode === "demo" || ftConfirmed, free_transfers: confirmedFT ?? state.free_transfers ?? 1,
      }) });
      if (response.ok) setOptimizationResult(await response.json());
    } catch { /* The workspace remains available while recommendations retry. */ }
  }, [confirmedFT, ftConfirmed]);

  useEffect(() => { fetchStatus(); fetchCoreData(); }, [dataMode]);
  useEffect(() => { if (liveStatus?.gameweek) fetchCoreData(liveStatus.gameweek); }, [liveStatus?.gameweek]);

  const launch = async (id: number, mode: DataMode) => {
    setManagerId(id); setDataMode(mode); setView("workstation"); setManagerState(null); setOptimizationResult(null);
    try { const state = await fetchManager(id, mode); await fetchOptimization(state, mode); } catch { setView("landing"); }
  };

  const refresh = async () => {
    setIsRefreshing(true);
    try { await fetch(`/api/data/refresh?data_mode=${dataMode}`, { method: "POST" }); await Promise.all([fetchStatus(), fetchCoreData(liveStatus?.gameweek)]); if (managerId) await fetchManager(managerId, dataMode); }
    finally { setIsRefreshing(false); }
  };

  const playersDict = useMemo(() => Object.fromEntries(players.map((player: any) => [player.player_id, player])), [players]);
  const currentGw = liveStatus?.gameweek || managerState?.gameweek || 1;

  return <AnimatePresence mode="wait">{view === "landing" ? (
    <LandingExperience key="landing" initialManagerId={managerId} isLaunching={managerId > 0 && !managerState} error={managerError || statusError} onLaunch={(id) => launch(id, "live")} onDemo={() => launch(99999, "demo")} />
  ) : (
    <WorkstationShell key="workstation" managerState={managerState} liveStatus={liveStatus} managerId={managerId} currentGw={currentGw} activeTab={activeTab} setActiveTab={setActiveTab} dockOpen={dockOpen} setDockOpen={setDockOpen} isRefreshing={isRefreshing} onRefresh={refresh} onExit={() => setView("landing")}>
      {managerError ? <StatePanel icon={AlertTriangle} title="Team import needs attention" copy={managerError} /> : !managerState ? <StatePanel icon={LoaderCircle} spinning title="Building your tactical workspace" copy="Importing your squad, refreshing projections and calculating a five-gameweek baseline." /> : (
        <WorkspaceOverview activeTab={activeTab} managerState={managerState} playersDict={playersDict} projections={projectionsDict} optimization={optimizationResult} currentGw={currentGw} />
      )}
    </WorkstationShell>
  )}</AnimatePresence>;
}

function StatePanel({ icon: Icon, title, copy, spinning }: { icon: React.ElementType; title: string; copy: string; spinning?: boolean }) {
  return <div className="grid min-h-[65vh] place-items-center border border-slate-200 bg-white p-8 text-center"><div className="max-w-md"><Icon className={`mx-auto h-7 w-7 text-indigo-600 ${spinning ? "animate-spin" : ""}`} /><h1 className="mt-5 text-xl font-semibold tracking-tight text-slate-900">{title}</h1><p className="mt-2 text-sm leading-6 text-slate-500">{copy}</p></div></div>;
}

function WorkspaceOverview({ activeTab, managerState, playersDict, projections, optimization, currentGw }: any) {
  const squad = managerState?.squad || managerState?.picks || [];
  const headline = activeTab === "pitch" ? "Squad workspace" : activeTab === "horizon" ? "Five-gameweek plan" : "Performance analytics";
  const names = squad.slice(0, 11).map((pick: any) => playersDict[pick.player_id || pick.element]?.web_name || pick.web_name || "Player");
  return <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ type: "spring", stiffness: 400, damping: 30 }}>
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-[.17em] text-indigo-600">GW{currentGw} · Live model</p><h1 className="mt-1 text-2xl font-semibold tracking-[-.025em] text-slate-950">{headline}</h1><p className="mt-1 text-sm text-slate-500">{managerState.team_name || "Your squad"} · balanced risk profile</p></div><button className="inline-flex items-center gap-2 bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-indigo-700 active:scale-[.98]">Review recommendation <ArrowRight className="h-3.5 w-3.5" /></button></div>
    <div className="relative min-h-[610px] overflow-hidden border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3"><span className="text-xs font-semibold text-slate-700">Tactical canvas</span><span className="font-mono text-[10px] tabular-nums text-slate-400">{names.length || 11} starters · 5 GW projection</span></div>
      <div className="absolute inset-x-7 bottom-7 top-14 overflow-hidden bg-[#e9f7ef]"><div className="absolute inset-5 border border-emerald-700/25" /><div className="absolute left-1/2 top-5 h-[calc(100%-2.5rem)] border-l border-emerald-700/20" /><div className="absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full border border-emerald-700/20" />
        <div className="grid h-full grid-cols-4 place-items-center gap-3 p-12 opacity-90">{Array.from({ length: 11 }).map((_, index) => { const name = names[index] || `Player ${index + 1}`; const pick = squad[index] || {}; const projection = projections[pick.player_id || pick.element] || {}; return <div key={`${name}-${index}`} className={`${index === 0 ? "col-span-4" : ""} text-center`}><div className="mx-auto grid h-11 w-11 place-items-center rounded-full border-4 border-white bg-indigo-600 text-[10px] font-bold text-white shadow-md">{Math.round(projection.expected_points || projection.xp || 0)}</div><p className="mt-1 bg-white/90 px-2 py-1 text-[10px] font-semibold text-slate-800 shadow-sm">{name}</p></div>; })}</div>
        {!names.length && <div className="absolute inset-0 grid place-items-center bg-white/35 backdrop-blur-[1px]"><span className="text-sm font-medium text-slate-600">Squad layout is loading…</span></div>}
      </div>
    </div>
    {optimization && <div className="mt-4 flex items-center gap-3 border border-indigo-100 bg-indigo-50 px-4 py-3 text-xs text-indigo-900"><Sparkles className="h-4 w-4 text-indigo-600" /> The new five-week recommendation is ready to inspect.</div>}
  </motion.div>;
}
