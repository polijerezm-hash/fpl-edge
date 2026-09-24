import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, BarChart3, CalendarRange, Command, LoaderCircle, ShieldCheck } from "lucide-react";
import { BrandMark } from "@/components/BrandMark";

interface LandingExperienceProps {
  initialManagerId?: number;
  isLaunching?: boolean;
  error?: string | null;
  onLaunch: (managerId: number) => void;
  onDemo: () => void;
}

const previewPlayers = [
  { x: 50, y: 16 }, { x: 25, y: 38 }, { x: 50, y: 42 }, { x: 75, y: 38 },
  { x: 14, y: 65 }, { x: 38, y: 62 }, { x: 62, y: 62 }, { x: 86, y: 65 },
  { x: 29, y: 84 }, { x: 50, y: 80 }, { x: 71, y: 84 },
];

export function LandingExperience({ initialManagerId, isLaunching, error, onLaunch, onDemo }: LandingExperienceProps) {
  const [managerId, setManagerId] = useState(initialManagerId && initialManagerId !== 99999 ? String(initialManagerId) : "");
  const score = useMemo(() => {
    if (!managerId) return 0;
    const seed = managerId.split("").reduce((total, digit) => total + Number(digit || 0), 0);
    return Math.min(94, 64 + (seed % 31));
  }, [managerId]);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const parsed = Number(managerId);
    if (Number.isFinite(parsed) && parsed > 0) onLaunch(parsed);
  };

  return (
    <motion.main initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.985 }} transition={{ duration: 0.3 }} className="min-h-screen bg-white text-slate-950">
      <nav className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 lg:px-8">
        <div className="flex items-center gap-3">
          <BrandMark className="h-9 w-9" />
          <span className="text-[15px] font-semibold tracking-tight">FPL Edge</span>
          <span className="hidden border-l border-slate-200 pl-3 text-xs text-slate-500 sm:block">Tactical planning engine</span>
        </div>
        <button onClick={onDemo} className="text-sm font-medium text-slate-600 transition hover:text-indigo-600 active:scale-[.98]">Explore demo <span aria-hidden="true">↗</span></button>
      </nav>

      <section className="mx-auto grid max-w-7xl items-center gap-14 px-5 pb-20 pt-12 lg:grid-cols-[1.03fr_.97fr] lg:px-8 lg:pb-28 lg:pt-20">
        <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="mb-7 inline-flex items-center gap-2 border border-indigo-100 bg-indigo-50 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[.16em] text-indigo-700"><ShieldCheck className="h-3.5 w-3.5" /> Decision support, not guesswork</div>
          <h1 className="max-w-3xl text-5xl font-semibold leading-[.98] tracking-[-.05em] text-slate-950 sm:text-6xl lg:text-[74px]">The Linear-Grade Tactical Engine for FPL</h1>
          <p className="mt-7 max-w-xl text-lg leading-8 text-slate-600">Build transfers across the next five gameweeks, inspect every assumption and make the move that improves your whole plan—not just this Saturday.</p>

          <form onSubmit={submit} className="mt-9 max-w-xl">
            <label htmlFor="manager-id" className="mb-2 block text-xs font-semibold uppercase tracking-[.14em] text-slate-500">FPL manager ID</label>
            <div className="flex border border-slate-300 bg-white p-1 shadow-[0_14px_35px_rgba(15,23,42,.08)] focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-100">
              <input id="manager-id" inputMode="numeric" value={managerId} onChange={(event) => setManagerId(event.target.value.replace(/\D/g, ""))} placeholder="e.g. 1234567" className="min-w-0 flex-1 bg-transparent px-4 py-3 font-mono text-sm tabular-nums text-slate-900 placeholder:text-slate-400" />
              <button type="submit" disabled={!managerId || isLaunching} className="inline-flex min-w-36 items-center justify-center gap-2 bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 active:scale-[.98] disabled:cursor-not-allowed disabled:bg-slate-300">
                {isLaunching ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <>Launch engine <ArrowRight className="h-4 w-4" /></>}
              </button>
            </div>
            {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
            <p className="mt-3 text-xs text-slate-500">Find your ID in the address bar of your FPL Points page.</p>
          </form>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.12, duration: 0.55 }} className="relative mx-auto w-full max-w-[570px]">
          <div className="absolute -inset-8 bg-[radial-gradient(circle_at_center,rgba(79,70,229,.14),transparent_65%)]" />
          <div className="relative border border-slate-200 bg-slate-50 p-3 shadow-[0_28px_80px_rgba(15,23,42,.12)]">
            <div className="mb-3 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
              <div><p className="text-[10px] font-semibold uppercase tracking-[.16em] text-slate-400">Live team preview</p><p className="mt-1 text-sm font-semibold text-slate-800">Gameweek tactical score</p></div>
              <div className="text-right"><motion.span key={score} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="font-mono text-3xl font-semibold tabular-nums text-indigo-600">{score}</motion.span><span className="font-mono text-xs text-slate-400">/100</span></div>
            </div>
            <div className="relative aspect-[1.12] overflow-hidden bg-[#e6f6ec]">
              <div className="absolute inset-3 border border-emerald-700/25" /><div className="absolute left-1/2 top-3 h-[calc(100%-1.5rem)] border-l border-emerald-700/20" /><div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border border-emerald-700/20" />
              {previewPlayers.map((player, index) => <motion.div key={index} initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: managerId ? 1 : 0.45, scale: 1 }} transition={{ delay: index * 0.025 }} className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${player.x}%`, top: `${player.y}%` }}><div className="h-8 w-8 rounded-full border-2 border-white bg-indigo-600 shadow-sm" /><div className="mx-auto mt-1 h-1.5 w-10 rounded-full bg-slate-900/20 blur-[1px]" /></motion.div>)}
              <div className="absolute inset-0 bg-white/15 backdrop-blur-[1.5px]" />
              <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between border border-white/70 bg-white/85 px-4 py-3 shadow-sm backdrop-blur"><span className="text-xs font-medium text-slate-600">Type your ID to calculate</span><span className="font-mono text-xs font-semibold tabular-nums text-emerald-700">5 GW model ready</span></div>
            </div>
          </div>
        </motion.div>
      </section>

      <section className="border-y border-slate-200 bg-slate-50/70"><div className="mx-auto grid max-w-7xl divide-y divide-slate-200 px-5 md:grid-cols-3 md:divide-x md:divide-y-0 lg:px-8">
        {[
          { icon: CalendarRange, kicker: "Planning", title: "Five-gameweek horizon", copy: "See the downstream cost of a transfer before you lock it in." },
          { icon: BarChart3, kicker: "Forecasting", title: "Hybrid expected points", copy: "Minutes, form, fixtures, odds and uncertainty in one inspectable model." },
          { icon: Command, kicker: "Matchday", title: "Command bar", copy: "Track effective ownership, safety margin and rank impact as matches unfold." },
        ].map(({ icon: Icon, kicker, title, copy }) => <article key={title} className="px-0 py-9 md:px-8 first:pl-0 last:pr-0"><div className="flex items-start gap-4"><div className="border border-slate-200 bg-white p-2.5 text-indigo-600"><Icon className="h-5 w-5" /></div><div><p className="text-[10px] font-bold uppercase tracking-[.17em] text-indigo-600">{kicker}</p><h2 className="mt-2 text-base font-semibold tracking-tight text-slate-900">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{copy}</p></div></div></article>)}
      </div></section>
    </motion.main>
  );
}
