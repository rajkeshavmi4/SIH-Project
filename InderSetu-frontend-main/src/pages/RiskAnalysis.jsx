import React from "react";
import { RiskDonut } from "../components/charts/RiskDonut.jsx";
import { RiskBreakdown } from "../components/charts/RiskBreakdown.jsx";
import { ForecastChart } from "../components/charts/ForecastChart.jsx";
import { ShieldAlert, BarChart3, TrendingUp, Compass, HelpCircle } from "lucide-react";

export function RiskAnalysis({ riskAnalysis, routes, forecastTimeline, selectedRouteId, selectRoute }) {
  const overall = riskAnalysis?.overallRiskPct || 28;
  const regionalRisk = riskAnalysis?.regionalRisk || [];
  const explanations = riskAnalysis?.explanation || [];

  return (
    <div className="p-3 md:p-4 space-y-4 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg flex items-center justify-between shadow-lg text-xs">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          <div>
            <h2 className="font-bold text-white text-sm uppercase">
              Antarctic Sector Risk Analytics Workstation
            </h2>
            <p className="text-slate-400 text-[11px]">
              Multi-Source Environmental Safety Assessment & Regional Vulnerability Modeling
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-medium">
          <span className="text-slate-400">System Risk Status:</span>
          <span className="px-2.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-bold">
            {riskAnalysis?.status || "Moderate"} ({overall}%)
          </span>
        </div>
      </div>

      {/* Row 1: Overall Donut & Bar Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Overall Donut */}
        <div className="lg:col-span-4 bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs">
          <h3 className="font-bold text-slate-100 text-xs uppercase border-b border-[#1b2b45] pb-1">
            Overall Risk Profile
          </h3>
          <div className="h-[210px]">
            <RiskDonut overallRisk={overall} breakdown={riskAnalysis?.breakdown} />
          </div>
        </div>

        {/* Bar Breakdown */}
        <div className="lg:col-span-8 bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs">
          <h3 className="font-bold text-slate-100 text-xs uppercase border-b border-[#1b2b45] pb-1">
            Route Risk Component Comparison (A vs B vs C)
          </h3>
          <RiskBreakdown routes={routes} />
        </div>
      </div>

      {/* Row 2: Regional Risk Table & 48h Risk Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Regional Risk Table */}
        <div className="lg:col-span-7 bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs">
          <div className="flex items-center justify-between border-b border-[#1b2b45] pb-1">
            <h3 className="font-bold text-slate-100 text-xs uppercase">
              Regional Sector Risk Scores
            </h3>
            <span className="text-[10px] text-slate-400 font-medium">6 ANTARCTIC ZONES</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#1b2b45] text-slate-400 text-[10px] uppercase font-semibold">
                  <th className="py-1.5 px-2">Antarctic Region</th>
                  <th className="py-1.5 px-2">Overall Risk</th>
                  <th className="py-1.5 px-2">Ice Risk</th>
                  <th className="py-1.5 px-2">Iceberg Risk</th>
                  <th className="py-1.5 px-2">Weather Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#15233b]">
                {regionalRisk.map((reg, idx) => (
                  <tr key={idx} className="hover:bg-[#0c1626] text-slate-300">
                    <td className="py-2 px-2 font-bold text-slate-100">{reg.region}</td>
                    <td className="py-2 px-2">
                      <span
                        className={`font-bold ${
                          reg.overallPct > 50
                            ? "text-red-400"
                            : reg.overallPct > 30
                            ? "text-amber-300"
                            : "text-cyan-300"
                        }`}
                      >
                        {reg.overallPct}%
                      </span>
                    </td>
                    <td className="py-2 px-2 text-blue-300 font-medium">{reg.icePct}%</td>
                    <td className="py-2 px-2 text-amber-300 font-medium">{reg.icebergPct}%</td>
                    <td className="py-2 px-2 text-cyan-300 font-medium">{reg.weatherPct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 48h Risk Trend */}
        <div className="lg:col-span-5 bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs">
          <h3 className="font-bold text-slate-100 text-xs uppercase border-b border-[#1b2b45] pb-1">
            48-Hour Risk Trend Forecast
          </h3>
          <div className="h-[210px]">
            <ForecastChart forecastTimeline={forecastTimeline} />
          </div>
        </div>
      </div>

      {/* WHY IS THE RISK MODERATE? Explainability Panel */}
      <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-4 shadow-lg space-y-2.5 text-xs text-slate-200">
        <div className="flex items-center gap-2 border-b border-[#1b2b45] pb-2">
          <HelpCircle className="w-5 h-5 text-cyan-400" />
          <h3 className="font-bold text-slate-100 text-sm uppercase">
            Why is the Current Overall Risk Rated as Moderate (28%)?
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
          {explanations.map((exp, idx) => (
            <div key={idx} className="flex items-start gap-2 p-2 rounded bg-[#080f1c] border border-[#1a2b45]">
              <span className="text-cyan-400 font-bold text-xs">•</span>
              <span className="text-slate-300">{exp}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
