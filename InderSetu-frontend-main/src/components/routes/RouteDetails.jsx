import React from "react";
import { AntarcticMap } from "../map/AntarcticMap.jsx";
import { WaypointTable } from "./WaypointTable.jsx";
import { RiskBreakdown } from "../charts/RiskBreakdown.jsx";
import { ForecastChart } from "../charts/ForecastChart.jsx";
import {
  Navigation,
  CheckCircle2,
  Cpu,
  Fuel,
  Clock,
  ShieldCheck,
  ArrowLeft,
  RotateCcw,
  Compass,
  FileText,
  AlertTriangle,
  Flame,
} from "lucide-react";

export function RouteDetails({
  activeRoute,
  routes,
  selectedRouteId,
  selectRoute,
  waypoints,
  selectedWaypoint,
  setSelectedWaypoint,
  selectedIceberg,
  setSelectedIceberg,
  icebergs,
  seaIce,
  mapLayers,
  toggleMapLayer,
  mapCenter,
  mapZoom,
  focusRegion,
  resetAntarcticView,
  setActivePage,
  handleRecalculate,
  handleReroute,
  forecastTimeline,
}) {
  const route = activeRoute || routes[1] || {};
  const startPoint = waypoints?.[0];
  const destinationPoint = waypoints?.[waypoints.length - 1];
  const confidence = route.confidencePct || Math.max(1, Math.round(100 - (route.riskPct || 0)));
  const breakdown = route.riskBreakdown || {};

  const timelineSteps = (waypoints || []).map((point, index, points) => ({
    name: index === 0 ? `Departure (${point.name || "Origin"})` : index === points.length - 1 ? `Destination (${point.name || "Destination"})` : point.name || `Waypoint ${index}`,
    offset: point.etaOffset || "Calculated",
    status: index === 0 ? "Origin" : index === points.length - 1 ? "Docking" : "Route checkpoint",
  }));

  return (
    <div className="space-y-4">
      {/* Route Header Banner & Actions */}
      <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-xl flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActivePage("dashboard")}
            className="p-2 rounded-md bg-[#132238] hover:bg-[#1a2e4c] text-cyan-300 border border-[#1e3254] transition flex items-center gap-1.5 text-xs font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Dashboard</span>
          </button>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white">
                {route.name || "Route B"} - Full Deep Dive Specification
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-700">
                RECOMMENDED CORRIDOR
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {startPoint?.name || "Departure"} → {destinationPoint?.name || "Destination"} | {route.distanceNm ?? "--"} nm | {route.etaFormatted || "--"} | Calculated Risk: {route.riskPct ?? "--"}%
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleReroute}
            className="px-3 py-1.5 bg-[#14233c] hover:bg-[#1d3254] text-cyan-300 border border-[#1f375e] rounded text-xs font-semibold transition flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Dynamic Reroute</span>
          </button>

          <button
            onClick={() => setActivePage("route-planner")}
            className="px-3 py-1.5 bg-[#14233c] hover:bg-[#1d3254] text-slate-200 border border-[#1f375e] rounded text-xs font-semibold transition flex items-center gap-1.5"
          >
            <Compass className="w-3.5 h-3.5 text-cyan-400" />
            <span>Alternative Routes</span>
          </button>

          <button
            onClick={() => setActivePage("reports")}
            className="px-3 py-1.5 bg-linear-to-r from-cyan-600 to-blue-700 hover:from-cyan-500 hover:to-blue-600 text-white rounded text-xs font-semibold transition flex items-center gap-1.5 shadow"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Export Route Report</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-2.5 rounded-lg text-center">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">TOTAL DISTANCE</span>
          <strong className="text-lg text-cyan-300 font-bold">{route.distanceNm ?? "--"} nm</strong>
        </div>
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-2.5 rounded-lg text-center">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">ESTIMATED FUEL</span>
          <strong className="text-lg text-amber-300 font-bold">{route.estimatedFuelMt ?? "--"} MT</strong>
        </div>
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-2.5 rounded-lg text-center">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">ETA VOYAGE TIME</span>
          <strong className="text-lg text-slate-100 font-bold">{route.etaFormatted || "--"}</strong>
        </div>
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-2.5 rounded-lg text-center">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">NAVIGATION RISK</span>
          <strong className="text-lg text-emerald-400 font-bold">{route.riskPct ?? "--"}%</strong>
        </div>
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-2.5 rounded-lg text-center col-span-2 sm:col-span-1">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">AI CONFIDENCE</span>
          <strong className="text-lg text-cyan-300 font-bold">{confidence}%</strong>
        </div>
      </div>

      {/* Main Route Map */}
      <div className="h-120">
        <AntarcticMap
          mapCenter={mapCenter}
          mapZoom={mapZoom}
          mapLayers={mapLayers}
          toggleMapLayer={toggleMapLayer}
          routes={routes}
          selectedRouteId={selectedRouteId}
          selectRoute={selectRoute}
          waypoints={waypoints}
          icebergs={icebergs}
          seaIce={seaIce}
          selectedWaypoint={selectedWaypoint}
          setSelectedWaypoint={setSelectedWaypoint}
          selectedIceberg={selectedIceberg}
          setSelectedIceberg={setSelectedIceberg}
          focusRegion={focusRegion}
          resetAntarcticView={resetAntarcticView}
          setActivePage={setActivePage}
        />
      </div>

      {/* WHY ROUTE B? Explainability Card */}
      <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-4 shadow-lg space-y-3 text-xs text-slate-200">
        <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
              <h3 className="font-bold text-slate-100 text-sm uppercase tracking-wide">
                Why {route.name || "Selected Route"}? - Decision Explainability Analysis
            </h3>
          </div>
          <span className="px-2.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold text-xs">
            {confidence}% AI CONFIDENCE SCORE
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded bg-[#080f1c] border border-[#1a2b45] space-y-2">
            <h4 className="font-bold text-cyan-300 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-cyan-400" />
              <span>Safety & Environmental Rationale</span>
            </h4>
            <ul className="space-y-1.5 text-slate-300 text-[11px]">
              <li className="flex items-start gap-1.5">
                <span className="text-cyan-400 font-bold">•</span>
                <span><strong>Iceberg exposure:</strong> {breakdown.iceberg ?? "--"}% weighted iceberg risk along this corridor.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-cyan-400 font-bold">•</span>
                <span><strong>Sea-ice exposure:</strong> {breakdown.seaIce ?? "--"}% weighted sea-ice risk along this corridor.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-cyan-400 font-bold">•</span>
                <span><strong>Threshold check:</strong> {route.riskPct ?? "--"}% calculated risk is evaluated against the active operational limit.</span>
              </li>
            </ul>
          </div>

          <div className="p-3 rounded bg-[#080f1c] border border-[#1a2b45] space-y-2">
            <h4 className="font-bold text-emerald-400 flex items-center gap-1.5">
              <Fuel className="w-4 h-4 text-emerald-400" />
              <span>Fuel & Voyage Efficiency Rationale</span>
            </h4>
            <ul className="space-y-1.5 text-slate-300 text-[11px]">
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span><strong>Fuel estimate:</strong> {route.estimatedFuelMt ?? "--"} MT for the selected vessel and route.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span><strong>Transit window:</strong> ETA is {route.etaFormatted || "--"} for the selected station pair.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span><strong>Balanced Trade-off:</strong> Strikes the ideal multi-objective pareto frontier between safety, speed, and fuel burn.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Waypoint Table */}
      <WaypointTable
        waypoints={waypoints}
        selectedWaypoint={selectedWaypoint}
        setSelectedWaypoint={setSelectedWaypoint}
      />

      {/* Voyage Timeline & Risk Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Voyage Timeline Progress */}
        <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs text-slate-200">
          <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
                Voyage Transit Timeline Log
              </h3>
            </div>
            <span className="text-[10px] text-slate-400 font-medium">AVG 20 KN CRUISE</span>
          </div>

          <div className="space-y-2 pt-1 text-[11px]">
            {timelineSteps.map((step, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded bg-[#09111e] border border-[#1a2b45]"
              >
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800 flex items-center justify-center font-bold text-[10px]">
                    {idx + 1}
                  </span>
                  <span className="font-bold text-slate-200">{step.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400">{step.offset}</span>
                  <span className="px-1.5 py-0.2 rounded bg-slate-800 text-cyan-300 text-[10px] font-semibold">
                    {step.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 48h Forecast Trend */}
        <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs text-slate-200">
          <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
            <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
              48h Route Corridor Forecast Trend
            </h3>
            <span className="text-[10px] text-slate-400 font-medium">0h → 48h PROJECTION</span>
          </div>
          <div className="h-52.5">
            <ForecastChart forecastTimeline={forecastTimeline} />
          </div>
        </div>
      </div>
    </div>
  );
}
