import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Crown, TrendingUp, ArrowRight, Sparkles, RotateCcw, ChevronRight } from "lucide-react";

interface HorizonBoardProps {
  optimizationResult: any;
  playersDict: Record<number, any>;
  currentGw: number;
  onRunOptimize: (params: { horizon: number; risk_profile: string }) => void;
}

const planColors = [
  { ring: "border-indigo-600", bg: "bg-indigo-600", text: "text-indigo-700", light: "bg-indigo-50 border-indigo-200" },
  { ring: "border-slate-400", bg: "bg-slate-500", text: "text-slate-600", light: "bg-slate-50 border-slate-200" },
  { ring: "border-emerald-600", bg: "bg-emerald-600", text: "text-emerald-700", light: "bg-emerald-50 border-emerald-200" },
  { ring: "border-amber-500", bg: "bg-amber-500", text: "text-amber-700", light: "bg-amber-50 border-amber-200" },
  { ring: "border-violet-500", bg: "bg-violet-500", text: "text-violet-700", light: "bg-violet-50 border-violet-200" },
];

function GwColumn({ gwData, playersDict, isFirst }: { gwData: any; playersDict: Record<number, any>; isFirst: boolean }) {
  const tin = (gwData.transfers_in ?? []).map((id: number) => playersDict[id]?.web_name ?? `#${id}`);
  const tout = (gwData.transfers_out ?? []).map((id: number) => playersDict[id]?.web_name ?? `#${id}`);
  const cap = playersDict[gwData.captain]?.web_name ?? `#${gwData.captain}`;
  const isRoll = tin.length === 0;

  return (
    <div className="min-w-[180px] flex-1 space-y-3">
      {/* GW header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <span className="text-[10px] font-bold uppercase tracking-[.15em] text-slate-500">GW{gwData.gw}</span>
        <span className="font-mono text-[10px] tabular-nums text-slate-400">£{Number(gwData.bank ?? 0).toFixed(1)}m</span>
      </div>

      {/* Transfer action */}
      {isRoll ? (
        <div className="flex items-center gap-1.5 rounded border border-emerald-200 bg-emerald-50 px-2.5 py-2">
          <RotateCcw className="h-3 w-3 text-emerald-600" />
          <span className="text-[10px] font-bold text-emerald-700">Roll transfer (+1 FT)</span>
        </div>
      ) : (
        <div className="space-y-1.5">
          {tout.map((name: string, i: number) => (
            <div key={i} className="flex items-center gap-1.5 rounded border border-rose-200 bg-rose-50 px-2.5 py-1.5">
              <span className="text-[9px] font-bold text-rose-500">OUT</span>
              <span className="truncate text-[10px] font-semibold text-rose-700">{name}</span>
            </div>
          ))}
          {tin.map((name: string, i: number) => (
            <div key={i} className="flex items-center gap-1.5 rounded border border-emerald-200 bg-emerald-50 px-2.5 py-1.5">
              <span className="text-[9px] font-bold text-emerald-500">IN</span>
              <span className="truncate text-[10px] font-semibold text-emerald-700">{name}</span>
            </div>
          ))}
        </div>
      )}

      {/* Hit cost */}
      {(gwData.hits ?? 0) > 0 && (
        <div className="flex items-center justify-between rounded border border-amber-200 bg-amber-50 px-2.5 py-1.5">
          <span className="text-[9px] font-bold text-amber-700">HIT</span>
          <span className="font-mono text-[10px] font-semibold tabular-nums text-amber-700">-{gwData.hits * 4}pts</span>
        </div>
      )}

      {/* FT remaining */}
      <div className="flex items-center gap-1">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className={`h-1.5 flex-1 rounded-full ${i < (gwData.free_transfers ?? 1) ? "bg-indigo-500" : "bg-slate-200"}`} />
        ))}
        <span className="ml-1 font-mono text-[9px] tabular-nums text-slate-400">{gwData.free_transfers ?? 1}FT</span>
      </div>

      {/* Captain */}
      <div className="flex items-center justify-between rounded border border-amber-100 bg-amber-50 px-2.5 py-2">
        <div className="flex items-center gap-1.5">
          <Crown className="h-3 w-3 text-amber-500" />
          <span className="text-[9px] font-bold text-amber-700">Captain</span>
        </div>
        <span className="truncate font-mono text-[10px] font-semibold tabular-nums text-amber-800">{cap}</span>
      </div>
    </div>
  );
}

export const HorizonBoard: React.FC<HorizonBoardProps> = ({
  optimizationResult,
  playersDict,
  currentGw,
  onRunOptimize,
}) => {
  const [selectedPlanIdx, setSelectedPlanIdx] = useState(0);
  const [horizon, setHorizon] = useState(3);
  const [riskProfile, setRiskProfile] = useState("balanced");

  const plans = optimizationResult?.plans ?? [];
  const activePlan = plans[selectedPlanIdx] ?? null;
  const baselineXp = optimizationResult?.baseline_xp ?? 0;

  return (
    <div className="space-y-5">
      {/* Top controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center overflow-hidden border border-slate-200 bg-white">
            {([1, 3, 5] as const).map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`px-4 py-2 text-xs font-semibold transition active:scale-[.98] ${horizon === h ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}
              >
                {h} GW
              </button>
            ))}
          </div>
          <div className="flex items-center overflow-hidden border border-slate-200 bg-white">
            {(["safe", "balanced", "aggressive"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setRiskProfile(r)}
                className={`px-3 py-2 text-xs font-semibold capitalize transition active:scale-[.98] ${riskProfile === r ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={() => onRunOptimize({ horizon, risk_profile: riskProfile })}
          className="inline-flex items-center gap-2 bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-indigo-700 active:scale-[.98]"
        >
          <Sparkles className="h-3.5 w-3.5" />
          Recalculate
        </button>
      </div>

      {plans.length === 0 ? (
        <div className="grid min-h-[300px] place-items-center border border-slate-200 bg-white">
          <div className="text-center">
            <Sparkles className="mx-auto h-8 w-8 text-slate-300" />
            <p className="mt-3 text-sm font-medium text-slate-500">
              {optimizationResult === null
                ? "Run optimiser to generate transfer plans"
                : "Loading plans…"}
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Plan selector tabs */}
          <div className="flex items-stretch gap-2 overflow-x-auto pb-1">
            {plans.map((plan: any, idx: number) => {
              const c = planColors[idx] ?? planColors[0];
              const isSelected = selectedPlanIdx === idx;
              return (
                <button
                  key={idx}
                  onClick={() => setSelectedPlanIdx(idx)}
                  className={`flex min-w-[130px] flex-col items-start rounded border p-3 text-left transition active:scale-[.98] ${isSelected ? `${c.light} ${c.ring}` : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"}`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[9px] font-black text-white ${c.bg}`}>
                      {plan.plan_code || String.fromCharCode(65 + idx)}
                    </span>
                    {idx === 0 && (
                      <span className="rounded-full bg-indigo-600 px-1.5 py-0.5 text-[8px] font-bold text-white">
                        Best
                      </span>
                    )}
                  </div>
                  <span className={`mt-2 font-mono text-base font-bold tabular-nums ${isSelected ? c.text : "text-slate-700"}`}>
                    {Number(plan.expected_points).toFixed(1)} xP
                  </span>
                  <span className={`font-mono text-[10px] tabular-nums ${Number(plan.gain_vs_hold) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                    {Number(plan.gain_vs_hold) >= 0 ? "+" : ""}{Number(plan.gain_vs_hold).toFixed(1)} vs hold
                  </span>
                </button>
              );
            })}
          </div>

          {/* Horizon board */}
          {activePlan && (
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedPlanIdx}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
                className="space-y-4"
              >
                {/* Plan summary */}
                <div className="flex items-center gap-4 border border-slate-200 bg-white p-4">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">Plan {activePlan.plan_code}</p>
                    <p className="mt-1 font-mono text-2xl font-semibold tabular-nums text-slate-900">
                      {Number(activePlan.expected_points).toFixed(1)} xP
                    </p>
                  </div>
                  <div className="h-10 w-px bg-slate-200" />
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">vs Hold</p>
                    <p className={`mt-1 font-mono text-lg font-semibold tabular-nums ${Number(activePlan.gain_vs_hold) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                      {Number(activePlan.gain_vs_hold) >= 0 ? "+" : ""}{Number(activePlan.gain_vs_hold).toFixed(1)}
                    </p>
                  </div>
                  <div className="h-10 w-px bg-slate-200" />
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">Hit cost</p>
                    <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-amber-600">
                      {activePlan.hits > 0 ? `-${activePlan.hits * 4}pts` : "Free"}
                    </p>
                  </div>
                  <div className="h-10 w-px bg-slate-200" />
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">Baseline</p>
                    <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-slate-500">
                      {Number(baselineXp).toFixed(1)} xP
                    </p>
                  </div>
                </div>

                {/* GW columns */}
                <div className="overflow-x-auto">
                  <div className="flex min-w-full gap-4 p-4 border border-slate-200 bg-slate-50/60">
                    {(activePlan.gameweeks ?? []).map((gwData: any, i: number) => (
                      <GwColumn key={gwData.gw} gwData={gwData} playersDict={playersDict} isFirst={i === 0} />
                    ))}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          )}
        </>
      )}
    </div>
  );
};
