import React from "react";
import { MissionPlanner } from "../components/dashboard/MissionPlanner.jsx";
import { RouteComparison } from "../components/dashboard/RouteComparison.jsx";
import { Navigation, ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight, RotateCcw } from "lucide-react";

export function RoutePlanner({
  missionInputs,
  setMissionInputs,
  handleRecalculate,
  isAnalyzing,
  routes,
  selectedRouteId,
  selectRoute,
  setActivePage,
}) {
  const threshold = missionInputs.operationalRiskThresholdPct || 30;

  return (
    <div className="p-3 md:p-4 space-y-4 max-w-[1500px] mx-auto">
      {/* Header Banner */}
      <div className="bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg flex items-center justify-between shadow-lg text-xs">
        <div className="flex items-center gap-2">
          <Navigation className="w-5 h-5 text-cyan-400" />
          <div>
            <h2 className="font-bold text-white text-sm uppercase">
              Antarctic Route Optimization Planner
            </h2>
            <p className="text-slate-400 text-[11px]">
              Multi-Objective Pathfinding Engine | Safety, Fuel, and Ice Exposure Evaluation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-medium">
          <span className="text-slate-400">Operational Risk Threshold:</span>
          <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold">
            {threshold}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Left Input Planner Form */}
        <div className="lg:col-span-4 space-y-4">
          <MissionPlanner
            missionInputs={missionInputs}
            setMissionInputs={setMissionInputs}
            handleRecalculate={handleRecalculate}
            isAnalyzing={isAnalyzing}
          />

          <div className="bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg space-y-2 text-xs text-slate-200">
            <h4 className="font-bold text-cyan-300 uppercase border-b border-[#1b2b45] pb-1">
              Pathfinding Parameters
            </h4>
            <div className="space-y-1.5 text-[11px] text-slate-300 font-medium">
              <div className="flex justify-between">
                <span className="text-slate-400">Hydrodynamic Drag Model:</span>
                <span>PC 5 Ice Class</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Radar Safety Margin:</span>
                <span>&gt;18.0 nm</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Sea-Ice Density Limit:</span>
                <span>35.0%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Route Alternative Cards */}
        <div className="lg:col-span-8 space-y-4">
          {/* Loading Overlay State */}
          {isAnalyzing && (
            <div className="p-8 bg-[#0e1726] border border-[#1e2e4a] rounded-lg text-center font-medium space-y-2 text-cyan-300">
              <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
              <div>Analyzing environmental conditions & generating route alternatives...</div>
            </div>
          )}

          {/* 3 Route Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {routes.map((route) => {
              const isSelected = selectedRouteId === route.id;
              const isRecommended = route.recommended;
              const isWithinThreshold = route.riskPct <= threshold;

              return (
                <div
                  key={route.id}
                  onClick={() => selectRoute(route.id)}
                  className={`bg-[#0e1726] border rounded-lg p-3 shadow-lg space-y-3 cursor-pointer transition relative flex flex-col justify-between ${
                    isSelected
                      ? "border-cyan-500 bg-[#122037] ring-1 ring-cyan-500"
                      : "border-[#1e2e4a] hover:border-slate-600"
                  }`}
                >
                  <div className="space-y-2">
                    {/* Card Title Header */}
                    <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span
                            className="w-3 h-3 rounded-full inline-block"
                            style={{ backgroundColor: route.color }}
                          ></span>
                          <h3 className="font-bold text-slate-100 text-sm">
                            {route.name}
                          </h3>
                        </div>
                        <span className="text-[10px] text-slate-400 block">{route.label}</span>
                      </div>

                      {isRecommended && (
                        <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 text-[9px] font-bold">
                          RECOMMENDED
                        </span>
                      )}
                    </div>

                    {/* Operational Risk Threshold Compliance Badge */}
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-400 font-medium">Threshold Compliance:</span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                          isWithinThreshold
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : "bg-red-950 text-red-300 border border-red-800"
                        }`}
                      >
                        {isWithinThreshold ? `${route.riskPct}% - Within Threshold` : `${route.riskPct}% - Exceeds Limit`}
                      </span>
                    </div>

                    {/* Metrics */}
                    <div className="grid grid-cols-2 gap-1.5 text-[11px] pt-1">
                      <div className="p-1.5 rounded bg-[#080f1c] border border-[#1a2b45]">
                        <span className="text-[9px] text-slate-400 block font-medium">DISTANCE</span>
                        <strong className="text-slate-100 font-bold">{route.distanceNm} nm</strong>
                      </div>
                      <div className="p-1.5 rounded bg-[#080f1c] border border-[#1a2b45]">
                        <span className="text-[9px] text-slate-400 block font-medium">EST. FUEL</span>
                        <strong className="text-amber-300 font-bold">{route.estimatedFuelMt} MT</strong>
                      </div>
                      <div className="p-1.5 rounded bg-[#080f1c] border border-[#1a2b45]">
                        <span className="text-[9px] text-slate-400 block font-medium">ETA VOYAGE</span>
                        <strong className="text-slate-200 font-bold">{route.etaFormatted}</strong>
                      </div>
                      <div className="p-1.5 rounded bg-[#080f1c] border border-[#1a2b45]">
                        <span className="text-[9px] text-slate-400 block font-medium">RISK INDEX</span>
                        <strong
                          className={
                            route.riskPct > 20
                              ? "text-red-400 font-bold"
                              : route.riskPct > 10
                              ? "text-cyan-300 font-bold"
                              : "text-emerald-400 font-bold"
                          }
                        >
                          {route.riskPct}%
                        </strong>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-300 italic pt-1">{route.summary}</p>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      selectRoute(route.id);
                      setActivePage("route-details");
                    }}
                    className="w-full mt-3 py-1.5 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 rounded font-semibold text-xs transition flex items-center justify-center gap-1 shadow"
                  >
                    <span>Inspect Route Details</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>

          <RouteComparison
            routes={routes}
            selectedRouteId={selectedRouteId}
            selectRoute={selectRoute}
            setActivePage={setActivePage}
          />
        </div>
      </div>
    </div>
  );
}
