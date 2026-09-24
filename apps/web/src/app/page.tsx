import React, { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, ArrowRight, LoaderCircle, Sparkles } from "lucide-react";
import { LandingExperience } from "@/components/LandingExperience";
import { WorkstationShell } from "@/components/WorkstationShell";
import { TacticalPitchCanvas } from "@/components/TacticalPitchCanvas";
import { HorizonBoard } from "@/components/HorizonBoard";
import { OverviewDashboard } from "@/components/OverviewDashboard";
import { PlayerInspectorDrawer } from "@/components/PlayerInspectorDrawer";

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
  const [selectedPlayerInfo, setSelectedPlayerInfo] = useState<any>(null);

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

  const fetchOptimization = useCallback(async (state: any, mode: DataMode, horizon = 5, riskProfile = "balanced") => {
    if (!state) return;
    try {
      const response = await fetch("/api/optimise", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
        manager_id: state.manager_id, data_mode: mode, horizon, risk_profile: riskProfile, confirm_free_transfers: mode === "demo" || ftConfirmed, free_transfers: confirmedFT ?? state.free_transfers ?? 1,
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
  const teamsDict = useMemo(() => Object.fromEntries(teams.map((team: any) => [team.team_id || team.id, team])), [teams]);
  const currentGw = liveStatus?.gameweek || managerState?.gameweek || 1;

  return (
    <>
      <AnimatePresence mode="wait">{view === "landing" ? (
        <LandingExperience key="landing" initialManagerId={managerId} isLaunching={managerId > 0 && !managerState} error={managerError || statusError} onLaunch={(id) => launch(id, "live")} onDemo={() => launch(99999, "demo")} />
      ) : (
        <WorkstationShell key="workstation" managerState={managerState} liveStatus={liveStatus} managerId={managerId} currentGw={currentGw} activeTab={activeTab} setActiveTab={setActiveTab} dockOpen={dockOpen} setDockOpen={setDockOpen} isRefreshing={isRefreshing} onRefresh={refresh} onExit={() => setView("landing")} optimizationResult={optimizationResult} playersDict={playersDict} projectionsDict={projectionsDict}>
          {managerError ? <StatePanel icon={AlertTriangle} title="Team import needs attention" copy={managerError} /> : !managerState ? <StatePanel icon={LoaderCircle} spinning title="Building your tactical workspace" copy="Importing your squad, refreshing projections and calculating a five-gameweek baseline." /> : (
            <WorkspaceOverview
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              managerState={managerState}
              playersDict={playersDict}
              teamsDict={teamsDict}
              fixtures={fixtures}
              projections={projectionsDict}
              optimization={optimizationResult}
              currentGw={currentGw}
              onSelectPlayer={(info: any) => setSelectedPlayerInfo(info)}
              onRunOptimize={(params: any) => fetchOptimization(managerState, dataMode, params.horizon, params.risk_profile)}
            />
          )}
        </WorkstationShell>
      )}</AnimatePresence>

      <PlayerInspectorDrawer
        player={selectedPlayerInfo?.player || null}
        squadPlayer={selectedPlayerInfo?.squadPlayer}
        proj={selectedPlayerInfo?.proj}
        teamsDict={teamsDict}
        fixtures={fixtures}
        currentGw={currentGw}
        isOpen={Boolean(selectedPlayerInfo)}
        onClose={() => setSelectedPlayerInfo(null)}
      />
    </>
  );
}

function StatePanel({ icon: Icon, title, copy, spinning }: { icon: React.ElementType; title: string; copy: string; spinning?: boolean }) {
  return <div className="grid min-h-[65vh] place-items-center border border-slate-200 bg-white p-8 text-center"><div className="max-w-md"><Icon className={`mx-auto h-7 w-7 text-indigo-600 ${spinning ? "animate-spin" : ""}`} /><h1 className="mt-5 text-xl font-semibold tracking-tight text-slate-900">{title}</h1><p className="mt-2 text-sm leading-6 text-slate-500">{copy}</p></div></div>;
}

function WorkspaceOverview({
  activeTab,
  setActiveTab,
  managerState,
  playersDict,
  teamsDict,
  fixtures,
  projections,
  optimization,
  currentGw,
  onSelectPlayer,
  onRunOptimize,
}: any) {
  const headline = activeTab === "pitch" ? "Squad workspace" : activeTab === "horizon" ? "Five-gameweek plan" : "Performance analytics";

  return (
    <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ type: "spring", stiffness: 400, damping: 30 }} className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.17em] text-indigo-600">GW{currentGw} · Live model</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-[-.025em] text-slate-950">{headline}</h1>
          <p className="mt-1 text-sm text-slate-500">{managerState.team_name || "Your squad"} · balanced risk profile</p>
        </div>
        {activeTab !== "horizon" && (
          <button onClick={() => setActiveTab("horizon")} className="inline-flex items-center gap-2 bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-indigo-700 active:scale-[.98]">
            Review recommendation <ArrowRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {activeTab === "pitch" && (
        <TacticalPitchCanvas
          managerState={managerState}
          playersDict={playersDict}
          projectionsDict={projections}
          teamsDict={teamsDict}
          fixtures={fixtures}
          currentGw={currentGw}
          onSelectPlayer={onSelectPlayer}
        />
      )}

      {activeTab === "horizon" && (
        <HorizonBoard
          optimizationResult={optimization}
          playersDict={playersDict}
          currentGw={currentGw}
          onRunOptimize={onRunOptimize}
        />
      )}

      {activeTab === "analytics" && (
        <OverviewDashboard
          optimizationResult={optimization}
          managerState={managerState}
          captainPicks={[]}
          playersDict={playersDict}
          projectionsDict={projections}
          onNavigateTab={(tab) => setActiveTab(tab as any)}
          onAskAI={() => {}}
        />
      )}

      {optimization && activeTab === "pitch" && (
        <div className="flex items-center gap-3 border border-indigo-100 bg-indigo-50 px-4 py-3 text-xs text-indigo-900">
          <Sparkles className="h-4 w-4 text-indigo-600 shrink-0" /> The new five-week recommendation is ready to inspect.
        </div>
      )}
    </motion.div>
  );
}
