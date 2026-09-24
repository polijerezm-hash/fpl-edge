import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  ChevronRight,
  CircleAlert,
  RefreshCw,
  ShieldCheck,
  Target,
  Trophy,
  Users,
} from "lucide-react";

interface MiniLeagueViewProps {
  managerState: any;
  dataMode: "live" | "demo";
}

const formatRank = (rank?: number | null) => rank ? `#${rank.toLocaleString()}` : "—";

export const MiniLeagueView: React.FC<MiniLeagueViewProps> = ({ managerState, dataMode }) => {
  const [leagues, setLeagues] = useState<any[]>([]);
  const [selectedLeagueId, setSelectedLeagueId] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loadingLeagues, setLoadingLeagues] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const managerId = managerState?.manager_id;

  useEffect(() => {
    if (!managerId) return;
    let cancelled = false;
    setLoadingLeagues(true);
    setError(null);
    fetch(`/api/mini-leagues?manager_id=${managerId}&data_mode=${dataMode}`)
      .then(async response => {
        if (!response.ok) throw new Error("Could not load your mini-leagues");
        return response.json();
      })
      .then(data => {
        if (cancelled) return;
        const nextLeagues = data.leagues || [];
        setLeagues(nextLeagues);
        setSelectedLeagueId(current => current && nextLeagues.some((league: any) => league.id === current)
          ? current
          : nextLeagues[0]?.id ?? null);
      })
      .catch(err => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoadingLeagues(false));
    return () => { cancelled = true; };
  }, [managerId, dataMode]);

  useEffect(() => {
    if (!managerId || !selectedLeagueId) return;
    let cancelled = false;
    setLoadingAnalysis(true);
    setError(null);
    fetch(`/api/mini-leagues/${selectedLeagueId}/analysis?manager_id=${managerId}&data_mode=${dataMode}`)
      .then(async response => {
        if (!response.ok) throw new Error("Could not analyse this mini-league");
        return response.json();
      })
      .then(data => !cancelled && setAnalysis(data))
      .catch(err => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoadingAnalysis(false));
    return () => { cancelled = true; };
  }, [managerId, selectedLeagueId, dataMode]);

  const selectedLeague = leagues.find(league => league.id === selectedLeagueId);
  const managerStanding = useMemo(
    () => analysis?.standings?.find((row: any) => row.entry === managerId),
    [analysis, managerId],
  );
  const leader = analysis?.standings?.[0];
  const gapToLeader = managerStanding && leader ? managerStanding.total - leader.total : null;

  if (!managerId) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="panel rounded-2xl p-10 text-center">
          <Trophy className="mx-auto h-8 w-8 text-primary mb-4" />
          <h2 className="text-xl font-bold text-slate-100">Import your FPL team first</h2>
          <p className="mt-2 text-sm text-slate-400">Your current classic mini-leagues will appear here automatically.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-[1440px] mx-auto space-y-5">
      <header className="flex flex-col gap-3 border-b border-surfaceBorder pb-5 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="eyebrow">League room</div>
          <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-100">Mini-leagues</h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-400">
            Live standings, effective ownership and the players that can move your position.
          </p>
        </div>
        {analysis && (
          <div className="text-right text-xs text-slate-500">
            Based on {analysis.sample_size} sampled teams · GW{analysis.gameweek}
          </div>
        )}
      </header>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-800/60 bg-rose-950/30 px-4 py-3 text-sm text-rose-300">
          <CircleAlert className="h-4 w-4" /> {error}
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="panel rounded-xl overflow-hidden self-start">
          <div className="border-b border-surfaceBorder px-4 py-3">
            <div className="eyebrow">Your competitions</div>
          </div>
          {loadingLeagues ? (
            <div className="flex items-center gap-2 p-5 text-sm text-slate-400">
              <RefreshCw className="h-4 w-4 animate-spin" /> Loading leagues…
            </div>
          ) : leagues.length === 0 ? (
            <p className="p-5 text-sm text-slate-400">No classic mini-leagues were found for this team.</p>
          ) : (
            <div className="divide-y divide-surfaceBorder">
              {leagues.map(league => {
                const active = league.id === selectedLeagueId;
                const movement = (league.last_rank || league.rank) - (league.rank || league.last_rank);
                return (
                  <button
                    key={league.id}
                    onClick={() => setSelectedLeagueId(league.id)}
                    className={`w-full px-4 py-4 text-left transition-colors ${active ? "bg-primary/10" : "hover:bg-surfaceHover/60"}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className={`truncate text-sm font-bold ${active ? "text-primary" : "text-slate-200"}`}>{league.name}</span>
                      <ChevronRight className={`h-4 w-4 shrink-0 ${active ? "text-primary" : "text-slate-600"}`} />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                      <span>{formatRank(league.rank)}</span>
                      <span className={movement > 0 ? "text-primary" : movement < 0 ? "text-rose-400" : ""}>
                        {movement > 0 ? `↑ ${movement}` : movement < 0 ? `↓ ${Math.abs(movement)}` : "No change"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </aside>

        <main className="min-w-0 space-y-5">
          {loadingAnalysis && !analysis ? (
            <div className="panel rounded-xl p-10 flex items-center justify-center gap-2 text-sm text-slate-400">
              <RefreshCw className="h-4 w-4 animate-spin" /> Building league exposure…
            </div>
          ) : analysis && (
            <>
              <section className="panel rounded-xl p-5">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="eyebrow">Selected league</div>
                    <h3 className="mt-1 text-xl font-black text-slate-100">{selectedLeague?.name}</h3>
                  </div>
                  <div className="grid grid-cols-3 gap-px overflow-hidden rounded-lg border border-surfaceBorder bg-surfaceBorder min-w-[360px]">
                    <div className="bg-background/50 px-4 py-3">
                      <div className="eyebrow">Position</div>
                      <div className="mt-1 text-xl font-black text-slate-100">{formatRank(managerStanding?.rank || selectedLeague?.rank)}</div>
                    </div>
                    <div className="bg-background/50 px-4 py-3">
                      <div className="eyebrow">Leader gap</div>
                      <div className={`mt-1 text-xl font-black ${gapToLeader === 0 ? "text-primary" : "text-rose-400"}`}>
                        {gapToLeader === null ? "—" : gapToLeader === 0 ? "Leader" : `${gapToLeader} pts`}
                      </div>
                    </div>
                    <div className="bg-background/50 px-4 py-3">
                      <div className="eyebrow">GW score</div>
                      <div className="mt-1 text-xl font-black text-slate-100">{managerStanding?.event_total ?? "—"}</div>
                    </div>
                  </div>
                </div>
              </section>

              <div className="grid gap-5 xl:grid-cols-2">
                <ExposureList
                  title="Your differentials"
                  subtitle="Owned by you, under-owned by the league"
                  icon={<Target className="h-4 w-4 text-primary" />}
                  rows={analysis.differentials || []}
                  type="edge"
                />
                <ExposureList
                  title="Rank threats"
                  subtitle="Popular players you do not own"
                  icon={<ShieldCheck className="h-4 w-4 text-amber-400" />}
                  rows={analysis.threats || []}
                  type="threat"
                />
              </div>

              <section className="panel rounded-xl overflow-hidden">
                <div className="flex items-center justify-between border-b border-surfaceBorder px-5 py-4">
                  <div>
                    <h3 className="font-bold text-slate-100">Standings</h3>
                    <p className="mt-0.5 text-xs text-slate-500">Top sampled managers in this league</p>
                  </div>
                  <Users className="h-4 w-4 text-slate-500" />
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-surfaceBorder text-[10px] uppercase tracking-[0.14em] text-slate-500">
                      <tr><th className="px-5 py-3">Rank</th><th className="px-5 py-3">Team</th><th className="px-5 py-3">Manager</th><th className="px-5 py-3 text-right">GW</th><th className="px-5 py-3 text-right">Total</th></tr>
                    </thead>
                    <tbody className="divide-y divide-surfaceBorder">
                      {(analysis.standings || []).slice(0, 15).map((row: any) => (
                        <tr key={row.entry} className={row.entry === managerId ? "bg-primary/8" : "hover:bg-surfaceHover/40"}>
                          <td className="px-5 py-3 font-mono text-slate-400">{row.rank}</td>
                          <td className="px-5 py-3 font-semibold text-slate-100">{row.entry_name}</td>
                          <td className="px-5 py-3 text-slate-400">{row.player_name}</td>
                          <td className="px-5 py-3 text-right font-mono text-slate-300">{row.event_total}</td>
                          <td className="px-5 py-3 text-right font-mono font-bold text-slate-100">{row.total}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  );
};

const ExposureList = ({ title, subtitle, icon, rows, type }: any) => (
  <section className="panel rounded-xl overflow-hidden">
    <div className="border-b border-surfaceBorder px-5 py-4">
      <div className="flex items-center gap-2 font-bold text-slate-100">{icon}{title}</div>
      <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
    </div>
    <div className="divide-y divide-surfaceBorder">
      {rows.length === 0 ? (
        <p className="px-5 py-6 text-sm text-slate-500">No material {type === "edge" ? "differentials" : "threats"} in the current sample.</p>
      ) : rows.map((row: any) => (
        <div key={row.player_id} className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-4 px-5 py-3.5">
          <div className="min-w-0">
            <div className="truncate font-semibold text-slate-100">{row.web_name}</div>
            <div className="mt-0.5 text-xs text-slate-500">{row.xmins} xMins · {row.mean_xp} xP</div>
          </div>
          <div className="text-right">
            <div className="font-mono text-sm text-slate-300">{row.league_eo}%</div>
            <div className="text-[10px] uppercase tracking-wide text-slate-600">League EO</div>
          </div>
          <div className={`flex min-w-[58px] items-center justify-end gap-1 font-mono text-sm font-bold ${type === "edge" ? "text-primary" : "text-rose-400"}`}>
            {type === "edge" ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
            {Math.abs(type === "edge" ? row.edge_score : row.threat_score).toFixed(1)}
          </div>
        </div>
      ))}
    </div>
  </section>
);
