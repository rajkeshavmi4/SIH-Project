import React from "react";
import { RiskDonut } from "../charts/RiskDonut.jsx";
import { ShieldAlert } from "lucide-react";

export function RiskSummary({ riskAnalysis }) {
  const overall = riskAnalysis?.overallRiskPct || 28;
  const status = riskAnalysis?.status || "Moderate";
  const breakdown = riskAnalysis?.breakdown || { icePct: 35, icebergPct: 22, weatherPct: 25, routePct: 30 };

  return (
    <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3.5 shadow-lg space-y-3 text-xs text-slate-200">
      {/* Card Header */}
      <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
          <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            Risk Assessment Summary
          </h3>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950/90 text-amber-300 border border-amber-800 shrink-0">
          {status} Status
        </span>
      </div>

      {/* Two-Column Structure: Left Donut + Legend, Right Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-stretch">
        {/* Left Column: Donut Chart + Custom Legend Below */}
        <div className="bg-[#09111e]/60 p-2 rounded-md border border-[#17263c] flex flex-col justify-between">
          <RiskDonut overallRisk={overall} breakdown={breakdown} />
        </div>

        {/* Right Column: Metric List */}
        <div className="flex flex-col justify-center space-y-1.5 text-[11px]">
          <div className="flex items-center justify-between p-2 rounded bg-[#09111e] border border-[#1a2b45] hover:border-[#283e60] transition">
            <span className="text-slate-300 font-medium">Ice Concentration</span>
            <strong className="text-blue-400 font-bold text-xs">{breakdown.icePct}%</strong>
          </div>

          <div className="flex items-center justify-between p-2 rounded bg-[#09111e] border border-[#1a2b45] hover:border-[#283e60] transition">
            <span className="text-slate-300 font-medium">Iceberg Drift Exposure</span>
            <strong className="text-amber-400 font-bold text-xs">{breakdown.icebergPct}%</strong>
          </div>

          <div className="flex items-center justify-between p-2 rounded bg-[#09111e] border border-[#1a2b45] hover:border-[#283e60] transition">
            <span className="text-slate-300 font-medium">Weather & Visibility</span>
            <strong className="text-cyan-300 font-bold text-xs">{breakdown.weatherPct}%</strong>
          </div>

          <div className="flex items-center justify-between p-2 rounded bg-[#09111e] border border-[#1a2b45] hover:border-[#283e60] transition">
            <span className="text-slate-300 font-medium">Route Nav Index</span>
            <strong className="text-purple-300 font-bold text-xs">{breakdown.routePct}%</strong>
          </div>
        </div>
      </div>
    </div>
  );
}
