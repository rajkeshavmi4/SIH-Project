import React from "react";
import { Cpu, CheckCircle2, ShieldCheck, AlertCircle, ArrowRight } from "lucide-react";

export function AIRecommendation({ activeRoute, setActivePage }) {
  const confidence = activeRoute?.confidencePct || Math.max(1, Math.round(100 - (activeRoute?.riskPct || 0)));
  const routeName = activeRoute?.name || "Moderate Corridor";
  const distance = activeRoute?.distanceNm || "--";
  const eta = activeRoute?.etaFormatted || "--";
  const fuel = activeRoute?.estimatedFuelMt || "--";
  const risk = activeRoute?.riskPct ?? "--";

  const reasons = [
    `${activeRoute?.riskBreakdown?.iceberg ?? "--"}% modeled iceberg exposure along the selected corridor`,
    `${activeRoute?.riskBreakdown?.seaIce ?? "--"}% weighted sea-ice risk across the route`,
    `${fuel} MT fuel estimate for ${distance} NM`,
    `${risk}% composite risk against the configured operational threshold`,
    `${eta} estimated transit time from the selected station pair`,
    "Recommendation recomputed from the latest route response",
  ];

  return (
    <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2.5 text-xs text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            AI Decision Support Recommendation
          </h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold text-[10px]">
          {confidence}% CONFIDENCE
        </span>
      </div>

      {/* Recommended Banner */}
      <div className="p-2.5 rounded-md bg-linear-to-r from-cyan-950/80 via-blue-950/50 to-[#0e1726] border border-cyan-500/40 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-cyan-400" />
            <h4 className="font-bold text-sm text-cyan-300">
              {routeName} - Recommended Voyage Corridor
            </h4>
          </div>
          <p className="text-[11px] text-slate-300 mt-0.5">
            Optimal balance of environmental safety, fuel burn efficiency, and ETA predictability.
          </p>
        </div>

        <button
          onClick={() => setActivePage("route-details")}
          className="px-2.5 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[11px] font-semibold transition shrink-0 flex items-center gap-1 shadow"
        >
          <span>{routeName} Details</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Explainability Rationale List */}
      <div>
        <div className="text-[10px] text-slate-400 uppercase tracking-wide mb-1 font-semibold">
          AI Optimization Rationale:
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
          {reasons.map((reason, idx) => (
            <div key={idx} className="flex items-start gap-1.5 p-1.5 rounded bg-[#080f1c] border border-[#1a2b45] text-[11px]">
              <span className="text-cyan-400 font-bold text-[10px]">•</span>
              <span className="text-slate-300">{reason}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Mandatory Operational Disclaimer */}
      <div className="p-2 rounded bg-[#09111e] border border-amber-800/40 flex items-center gap-2 text-[10px] text-amber-300">
        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong>Operational Support Disclaimer:</strong> Final navigation decisions and helm commands remain with the vessel master and ice navigator.
        </span>
      </div>
    </div>
  );
}
