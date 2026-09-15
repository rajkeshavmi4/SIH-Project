import React from "react";
import { MissionPlanner } from "../components/dashboard/MissionPlanner.jsx";
import { EnvironmentalConditions } from "../components/dashboard/EnvironmentalConditions.jsx";
import { RiskSummary } from "../components/dashboard/RiskSummary.jsx";
import { AIRecommendation } from "../components/dashboard/AIRecommendation.jsx";
import { RouteComparison } from "../components/dashboard/RouteComparison.jsx";
import { AlertsPanel } from "../components/dashboard/AlertsPanel.jsx";
import { ForecastTimeline } from "../components/dashboard/ForecastTimeline.jsx";
import { AntarcticMap } from "../components/map/AntarcticMap.jsx";
import { Activity, ShieldCheck, Cpu, Anchor } from "lucide-react";

export function Dashboard({
  missionInputs,
  setMissionInputs,
  handleRecalculate,
  isAnalyzing,
  weather,
  riskAnalysis,
  activeRoute,
  routes,
  selectedRouteId,
  selectRoute,
  alerts,
  forecastTimeline,
  forecastStepIndex,
  setForecastStepIndex,
  isForecastPlaying,
  setIsForecastPlaying,
  waypoints,
  icebergs,
  seaIce,
  mapLayers,
  toggleMapLayer,
  mapCenter,
  mapZoom,
  selectedWaypoint,
  setSelectedWaypoint,
  selectedIceberg,
  setSelectedIceberg,
  focusRegion,
  resetAntarcticView,
  viewAlertOnMap,
  setActivePage,
}) {
  const activeRisk = activeRoute?.riskPct ?? riskAnalysis?.overallRiskPct ?? "--";
  const origin = missionInputs?.departurePort?.split(" - ")[0] || "Departure";
  const destination = missionInputs?.destination?.split(" - ")[0] || "Destination";
  return (
    <div className="p-3 md:p-4 space-y-4 max-w-[1700px] mx-auto">
      {/* 3-Column Sophisticated Command Center Workstation Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        
        {/* LEFT COLUMN: Mission Planner & Operational Inputs (~24% / 3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          <MissionPlanner
            missionInputs={missionInputs}
            setMissionInputs={setMissionInputs}
            handleRecalculate={handleRecalculate}
            isAnalyzing={isAnalyzing}
          />

          <EnvironmentalConditions weather={weather} />

          <AlertsPanel
            alerts={alerts}
            viewAlertOnMap={viewAlertOnMap}
            setActivePage={setActivePage}
          />
        </div>

        {/* CENTER COLUMN: Interactive Antarctic Map (Visual Centerpiece!) & AI Support (~52% / 6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          {/* Map Container */}
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

          {/* AI Recommendation Banner */}
          <AIRecommendation
            activeRoute={activeRoute}
            setActivePage={setActivePage}
          />

          {/* 48h Forecast Scrubber */}
          <ForecastTimeline
            forecastTimeline={forecastTimeline}
            forecastStepIndex={forecastStepIndex}
            setForecastStepIndex={setForecastStepIndex}
            isForecastPlaying={isForecastPlaying}
            setIsForecastPlaying={setIsForecastPlaying}
          />
        </div>

        {/* RIGHT COLUMN: Risk Analytics & Route Alternatives (~24% / 3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          <RiskSummary riskAnalysis={riskAnalysis} />

          <RouteComparison
            routes={routes}
            selectedRouteId={selectedRouteId}
            selectRoute={selectRoute}
            setActivePage={setActivePage}
          />

          {/* Voyage & Telemetry Summary Card */}
          <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs text-slate-200">
            <div className="flex items-center justify-between border-b border-[#1b2b45] pb-1.5">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <h4 className="font-bold text-slate-100 uppercase">VOYAGE STATUS LOG</h4>
              </div>
              <span className="px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px]">
                ACTIVE
              </span>
            </div>

            <div className="space-y-1 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Current Leg:</span>
                <span>{origin} → {destination}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Selected Route:</span>
                <span className="text-cyan-300 font-bold">{activeRoute?.name || "--"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Risk Threshold:</span>
                <span className="text-emerald-400 font-bold">{activeRisk}% / {missionInputs?.operationalRiskThresholdPct || 30}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Nearest Waypoint:</span>
                <span className="text-slate-200">{waypoints?.[1]?.name || "Calculating"}</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
