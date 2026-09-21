import React, { useState, useEffect, useCallback } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { DataStatusBanner } from "@/components/DataStatusBanner";
import { OverviewDashboard } from "@/components/OverviewDashboard";
import { MyTeamPitch } from "@/components/MyTeamPitch";
import { TransferPlanner } from "@/components/TransferPlanner";
import { PlanComparisonModal } from "@/components/PlanComparisonModal";
import { CaptaincyView } from "@/components/CaptaincyView";
import { PlayerExplorer } from "@/components/PlayerExplorer";
import { FixturePlanner } from "@/components/FixturePlanner";
import { ChipStrategyView } from "@/components/ChipStrategyView";
import { MiniLeagueView } from "@/components/MiniLeagueView";
import { ModelAccuracyView } from "@/components/ModelAccuracyView";
import { AIAssistantDrawer } from "@/components/AIAssistantDrawer";
import { PlayerDetailModal } from "@/components/PlayerDetailModal";

// Read ?mode=demo from URL at startup (sets FRONTEND state only)
const getInitialDataMode = (): "live" | "demo" => {
  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    if (params.get("mode") === "demo") return "demo";
  }
  return "live";
};

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("overview");

  // Manager identity
  const [managerId, setManagerId] = useState<number>(0);
  const [dataMode, setDataMode] = useState<"live" | "demo">(getInitialDataMode);

  // Live status (from /api/data/status)
  const [liveStatus, setLiveStatus] = useState<any>(null);
  const [statusError, setStatusError] = useState<string | null>(null);

  // Squad state
  const [managerState, setManagerState] = useState<any>(null);
  const [managerError, setManagerError] = useState<string | null>(null);

  // Free transfers confirmation (Q1 decision)
  const [confirmedFT, setConfirmedFT] = useState<number | null>(null);
  const [ftConfirmed, setFtConfirmed] = useState(false);

  // Core data
  const [players, setPlayers] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [fixtures, setFixtures] = useState<any[]>([]);
  const [gameweeks, setGameweeks] = useState<any[]>([]);
  const [projectionsDict, setProjectionsDict] = useState<Record<number, any>>({});
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [captainPicks, setCaptainPicks] = useState<any>(null);
  const [chipData, setChipData] = useState<any>(null);
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [optimizeError, setOptimizeError] = useState<string | null>(null);

  // Modals & Drawers
  const [selectedPlayerForDetail, setSelectedPlayerForDetail] = useState<any>(null);
  const [comparisonModalData, setComparisonModalData] = useState<{ planA: any; planB: any } | null>(null);
  const [isAssistantOpen, setIsAssistantOpen] = useState<boolean>(false);

  const dm = dataMode; // alias for readability

  // 1. Fetch live data status on mount and data mode change
  const fetchStatus = useCallback(async () => {
    try {
      const resp = await fetch(`/api/data/status?data_mode=${dm}`);
      if (resp.ok) {
        setLiveStatus(await resp.json());
        setStatusError(null);
      } else {
        const errData = await resp.json();
        setStatusError(errData?.message || "Failed to load data status");
      }
    } catch (e: any) {
      setStatusError("Cannot reach FPL Edge API");
    }
  }, [dm]);

  // 2. Fetch core reference data (players, teams, fixtures, gameweeks, projections)
  const fetchCoreData = useCallback(async (gw?: number) => {
    const targetGw = gw || liveStatus?.gameweek || 4;
    const [pResp, tResp, fResp, gResp, prResp, evalResp] = await Promise.all([
      fetch(`/api/players?data_mode=${dm}`),
      fetch(`/api/teams?data_mode=${dm}`),
      fetch(`/api/fixtures?data_mode=${dm}`),
      fetch(`/api/gameweeks?data_mode=${dm}`),
      fetch(`/api/projections?gw=${targetGw}&data_mode=${dm}`),
      fetch("/api/evaluation"),
    ]);

    if (pResp.ok) setPlayers(await pResp.json());
    if (tResp.ok) setTeams(await tResp.json());
    if (fResp.ok) setFixtures(await fResp.json());
    if (gResp.ok) setGameweeks(await gResp.json());

    if (prResp.ok) {
      const pData = await prResp.json();
      const dict: Record<number, any> = {};
      (pData.projections || []).forEach((proj: any) => {
        dict[proj.player_id] = proj;
      });
      setProjectionsDict(dict);
    }

    if (evalResp.ok) setEvaluationData(await evalResp.json());
  }, [dm, liveStatus?.gameweek]);

  // 3. Fetch manager state
  const fetchManagerState = useCallback(async (id: number) => {
    if (!id) return;
    setManagerError(null);
    try {
      const resp = await fetch(`/api/team/${id}?data_mode=${dm}`);
      if (resp.ok) {
        const data = await resp.json();
        setManagerState(data);
        // Pre-fill FT estimate; require user confirmation before optimising
        setConfirmedFT(data.free_transfers ?? 1);
        setFtConfirmed(data.free_transfers_confirmed ?? false);

        // Auto-fetch captain picks & chips for this manager
        const [capResp, chipResp] = await Promise.all([
          fetch(`/api/captaincy?manager_id=${id}&data_mode=${dm}`, { method: "POST" }),
          fetch(`/api/chips/analyse?manager_id=${id}&data_mode=${dm}`, { method: "POST" }),
        ]);
        if (capResp.ok) setCaptainPicks(await capResp.json());
        if (chipResp.ok) setChipData(await chipResp.json());
      } else {
        const errData = await resp.json();
        setManagerError(errData?.message || `Failed to import team ${id}`);
        setManagerState(null);
      }
    } catch (e: any) {
      setManagerError(`Network error importing team: ${e.message}`);
    }
  }, [dm]);

  // 4. Run optimisation (only when FT confirmed)
  const fetchOptimization = useCallback(async (params: { horizon: number; risk_profile: string }) => {
    if (!managerState) return;
    setOptimizeError(null);

    const payload: any = {
      manager_id: managerState.manager_id,
      data_mode: dm,
      horizon: params.horizon,
      risk_profile: params.risk_profile,
      confirm_free_transfers: ftConfirmed,
    };
    if (confirmedFT !== null) {
      payload.free_transfers = confirmedFT;
    }

    try {
      const resp = await fetch("/api/optimise", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        setOptimizationResult(await resp.json());
      } else {
        const errData = await resp.json();
        if (errData?.code === "FREE_TRANSFERS_UNCONFIRMED") {
          setOptimizeError(`Free transfers must be confirmed before optimising. Estimated: ${errData.estimated_free_transfers} FT.`);
        } else {
          setOptimizeError(errData?.message || "Optimisation failed");
        }
      }
    } catch (e: any) {
      setOptimizeError(`Optimisation network error: ${e.message}`);
    }
  }, [managerState, dm, ftConfirmed, confirmedFT]);

  // 5. Data refresh (triggers backend snapshot refresh + re-fetch everything)
  const handleRefreshData = async () => {
    try {
      await fetch(`/api/data/refresh?data_mode=${dm}`, { method: "POST" });
    } catch {}
    await fetchStatus();
    if (liveStatus?.gameweek) await fetchCoreData(liveStatus.gameweek);
    if (managerId) await fetchManagerState(managerId);
  };

  // Trigger on mount + data mode change
  useEffect(() => {
    fetchStatus().then(() => {
      fetchCoreData();
    });
    // If demo mode, auto-load demo manager 99999
    if (dm === "demo") {
      setManagerId(99999);
    }
  }, [dm]);

  // When liveStatus becomes available, trigger core data with correct GW
  useEffect(() => {
    if (liveStatus?.gameweek) {
      fetchCoreData(liveStatus.gameweek);
    }
  }, [liveStatus?.gameweek]);

  // When managerId changes, load manager state
  useEffect(() => {
    if (managerId && managerId > 0) {
      fetchManagerState(managerId);
    }
  }, [managerId, dm]);

  // When manager state is loaded, run optimisation if FT is already confirmed (demo mode)
  useEffect(() => {
    if (managerState && (ftConfirmed || dm === "demo")) {
      fetchOptimization({ horizon: 3, risk_profile: "balanced" });
    }
  }, [managerState?.manager_id, ftConfirmed]);

  const playersDict = (players || []).reduce((acc: any, p: any) => {
    acc[p.player_id] = p;
    return acc;
  }, {});

  const handleImportTeam = (id: number) => {
    setManagerId(id);
    setDataMode("live");
    setFtConfirmed(false);
    setOptimizationResult(null);
  };

  const handleSwitchToDemo = () => {
    setDataMode("demo");
    setManagerId(99999);
    setFtConfirmed(true);
    setOptimizationResult(null);
  };

  const handleConfirmFT = (ft: number) => {
    setConfirmedFT(ft);
    setFtConfirmed(true);
    setOptimizeError(null);
    fetchOptimization({ horizon: 3, risk_profile: "balanced" });
  };

  const handleOpenAskAI = (_question?: string) => {
    setIsAssistantOpen(true);
  };

  // Derive current gameweek and deadline
  const currentGw = liveStatus?.gameweek || managerState?.gameweek || 4;
  const currentDeadline = liveStatus?.current_deadline || gameweeks.find(g => g.gameweek === currentGw)?.deadline_time || "";

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col md:flex-row font-sans">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab === "assistant" ? "overview" : activeTab}
        setActiveTab={(tab) => {
          if (tab === "assistant") {
            setIsAssistantOpen(true);
          } else {
            setActiveTab(tab);
          }
        }}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 pb-20 md:pb-6">
        {/* Header */}
        <Header
          managerId={managerId}
          onImportTeam={handleImportTeam}
          onSwitchToDemo={handleSwitchToDemo}
          teamName={managerState?.team_name || (dm === "demo" ? "FPL Edge Demo XI" : "No team loaded")}
          managerName={managerState?.manager_name || (dm === "demo" ? "Demo Manager" : "—")}
          overallRank={managerState?.overall_rank || 0}
          totalPoints={managerState?.overall_points || 0}
          currentGameweek={currentGw}
          deadlineTime={currentDeadline}
          dataMode={dm}
          confirmedFT={confirmedFT}
          ftConfirmed={ftConfirmed}
          onConfirmFT={handleConfirmFT}
          onRefreshData={handleRefreshData}
          managerError={managerError}
        />

        {/* Data Status Banner */}
        <DataStatusBanner
          statusData={liveStatus}
          isDemo={dm === "demo"}
        />

        {/* Error States */}
        {statusError && (
          <div className="mx-6 mt-4 bg-red-950/40 border border-red-800/60 rounded-xl px-5 py-3 text-sm text-red-300 flex items-center gap-3">
            <span className="font-mono text-[11px] bg-red-800/40 px-2 py-0.5 rounded text-red-400">LIVE_DATA_UNAVAILABLE</span>
            <span>{statusError}</span>
          </div>
        )}

        {optimizeError && (
          <div className="mx-6 mt-4 bg-amber-950/40 border border-amber-800/60 rounded-xl px-5 py-3 text-sm text-amber-300 flex items-center gap-3">
            <span className="font-mono text-[11px] bg-amber-800/40 px-2 py-0.5 rounded text-amber-400">ACTION REQUIRED</span>
            <span>{optimizeError}</span>
          </div>
        )}

        {/* Dynamic Tab Views */}
        <main className="flex-1 overflow-y-auto">
          {activeTab === "overview" && (
            <OverviewDashboard
              optimizationResult={optimizationResult}
              managerState={managerState}
              captainPicks={captainPicks}
              playersDict={playersDict}
              projectionsDict={projectionsDict}
              snapshotId={liveStatus?.snapshot_id || ""}
              asOfTimestamp={liveStatus?.as_of_timestamp || ""}
              onNavigateTab={setActiveTab}
              onAskAI={handleOpenAskAI}
            />
          )}

          {activeTab === "team" && (
            <MyTeamPitch
              managerState={managerState}
              playersDict={playersDict}
              projectionsDict={projectionsDict}
              onSelectPlayer={setSelectedPlayerForDetail}
            />
          )}

          {activeTab === "planner" && (
            <TransferPlanner
              optimizationResult={optimizationResult}
              playersDict={playersDict}
              onRunOptimize={fetchOptimization}
              onOpenCompare={(planA: any, planB: any) => setComparisonModalData({ planA, planB })}
              onAskAI={handleOpenAskAI}
            />
          )}

          {activeTab === "captaincy" && (
            <CaptaincyView
              captainData={captainPicks}
              playersDict={playersDict}
            />
          )}

          {activeTab === "players" && (
            <PlayerExplorer
              players={players}
              teams={teams}
              projectionsDict={projectionsDict}
              onSelectPlayer={setSelectedPlayerForDetail}
            />
          )}

          {activeTab === "fixtures" && (
            <FixturePlanner
              teams={teams}
              fixtures={fixtures}
              gameweeks={gameweeks}
            />
          )}

          {activeTab === "chips" && (
            <ChipStrategyView chipData={chipData} />
          )}

          {activeTab === "minileague" && (
            <MiniLeagueView managerState={managerState} />
          )}

          {activeTab === "accuracy" && (
            <ModelAccuracyView evaluationData={evaluationData} />
          )}
        </main>
      </div>

      {/* Modals & Drawers */}
      {selectedPlayerForDetail && (
        <PlayerDetailModal
          playerData={selectedPlayerForDetail}
          onClose={() => setSelectedPlayerForDetail(null)}
        />
      )}

      {comparisonModalData && (
        <PlanComparisonModal
          planA={comparisonModalData.planA}
          planB={comparisonModalData.planB}
          onClose={() => setComparisonModalData(null)}
        />
      )}

      <AIAssistantDrawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        managerId={managerId}
      />
    </div>
  );
}
