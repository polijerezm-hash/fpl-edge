
import React from "react";
import { X, ArrowRightLeft, Check, ShieldCheck, TrendingUp } from "lucide-react";

interface PlanComparisonModalProps {
  planA: any;
  planB: any;
  onClose: () => void;
}

export const PlanComparisonModal: React.FC<PlanComparisonModalProps> = ({
  planA,
  planB,
  onClose,
}) => {
  if (!planA || !planB) return null;

  const diffXp = roundVal(planA.expected_points - planB.expected_points);

  function roundVal(v: number) {
    return Math.round(v * 100) / 100;
  }

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-surface border border-surfaceBorder rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl space-y-6 p-6 md:p-8 animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-surfaceBorder pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-secondary/20 border border-secondary/30 flex items-center justify-center text-secondary">
              <ArrowRightLeft className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-extrabold text-slate-100">Plan Comparison Matrix</h3>
              <p className="text-xs text-slate-400">Side-by-side trade-off analysis of top optimization plans</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-surfaceHover text-slate-400 hover:text-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Comparison Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-surfaceBorder text-slate-400 text-xs uppercase tracking-wider">
                <th className="py-3 px-4 font-semibold">METRIC</th>
                <th className="py-3 px-4 font-bold text-primary bg-primary/10 rounded-t-xl">
                  PLAN {planA.plan_code || "A"}
                </th>
                <th className="py-3 px-4 font-bold text-secondary bg-secondary/10 rounded-t-xl">
                  PLAN {planB.plan_code || "B"}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surfaceBorder text-slate-200 font-mono">
              <tr>
                <td className="py-3.5 px-4 font-sans font-medium text-slate-300">Expected Score (xP)</td>
                <td className="py-3.5 px-4 font-extrabold text-primary bg-primary/5">{planA.expected_points} xP</td>
                <td className="py-3.5 px-4 font-bold text-slate-200 bg-secondary/5">{planB.expected_points} xP</td>
              </tr>
              <tr>
                <td className="py-3.5 px-4 font-sans font-medium text-slate-300">Gain vs HOLD</td>
                <td className="py-3.5 px-4 font-bold text-primary bg-primary/5">+{planA.gain_vs_hold} xP</td>
                <td className="py-3.5 px-4 font-bold text-slate-200 bg-secondary/5">+{planB.gain_vs_hold} xP</td>
              </tr>
              <tr>
                <td className="py-3.5 px-4 font-sans font-medium text-slate-300">Hit Costs</td>
                <td className="py-3.5 px-4 bg-primary/5 text-amber-400 font-bold">{planA.hits * 4} pts ({planA.hits} hits)</td>
                <td className="py-3.5 px-4 bg-secondary/5 text-slate-200">{planB.hits * 4} pts ({planB.hits} hits)</td>
              </tr>
              <tr>
                <td className="py-3.5 px-4 font-sans font-medium text-slate-300">Final Bank Remaining</td>
                <td className="py-3.5 px-4 bg-primary/5 text-emerald-400 font-bold">£{planA.final_bank}m</td>
                <td className="py-3.5 px-4 bg-secondary/5 text-emerald-400 font-bold">£{planB.final_bank}m</td>
              </tr>
              <tr>
                <td className="py-3.5 px-4 font-sans font-medium text-slate-300">Plan Robustness</td>
                <td className="py-3.5 px-4 bg-primary/5 text-slate-200">{Math.round((planA.robustness || 0.88) * 100)}% Confidence</td>
                <td className="py-3.5 px-4 bg-secondary/5 text-slate-200">{Math.round((planB.robustness || 0.82) * 100)}% Confidence</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Strategic Trade-off Summary */}
        <div className="bg-surfaceHover/80 border border-surfaceBorder rounded-2xl p-4 text-xs text-slate-300 leading-relaxed">
          <strong className="text-slate-100 font-semibold block mb-1">Strategic Trade-Off Summary:</strong>
          Plan A outranks Plan B by <strong className="text-primary font-mono">+{diffXp} xP</strong>.
          Plan A offers higher immediate point output, whereas Plan B preserves flexibility and money in bank.
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="bg-primary text-slate-950 font-bold px-6 py-2.5 rounded-xl text-sm hover:bg-primary-hover transition-colors"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};
