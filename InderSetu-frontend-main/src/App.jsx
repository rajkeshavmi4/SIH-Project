import React from "react";
import { Navbar } from "./components/layout/Navbar.jsx";
import { StatusBar } from "./components/layout/StatusBar.jsx";
import { useRouteData } from "./hooks/useRouteData.js";
import { Dashboard } from "./pages/Dashboard.jsx";
import { MapView } from "./pages/MapView.jsx";
import { RoutePlanner } from "./pages/RoutePlanner.jsx";
import { RiskAnalysis } from "./pages/RiskAnalysis.jsx";
import { Alerts } from "./pages/Alerts.jsx";
import { RouteDetails } from "./components/routes/RouteDetails.jsx";
import { FullReport } from "./components/reports/FullReport.jsx";
import { Loader2 } from "lucide-react";

export default function App() {
  const routeDataState = useRouteData();

  const {
    activePage,
    setActivePage,
    selectedRouteId,
    selectRoute,
    activeRoute,
    mission,
    seaIce,
    icebergs,
    weather,
    routes,
    riskAnalysis,
    alerts,
    forecastTimeline,
    waypoints,
    systemStatus,
    mapLayers,
    toggleMapLayer,
    mapCenter,
    mapZoom,
    selectedWaypoint,
    setSelectedWaypoint,
    selectedIceberg,
    setSelectedIceberg,
    forecastStepIndex,
    setForecastStepIndex,
    isForecastPlaying,
    setIsForecastPlaying,
    alertFilter,
    setAlertFilter,
    missionInputs,
    setMissionInputs,
    isLoading,
    isAnalyzing,
    errorMessage,
    loadInitialData,
    focusRegion,
    resetAntarcticView,
    viewAlertOnMap,
    handleRecalculate,
    handleReroute,
  } = routeDataState;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#070d19] flex flex-col items-center justify-center text-cyan-400 space-y-3 font-medium">
        <Loader2 className="w-8 h-8 animate-spin" />
        <p className="text-sm tracking-wider uppercase">Loading IndraSetu Antarctic Navigation System...</p>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="min-h-screen bg-[#070d19] flex flex-col items-center justify-center text-slate-200 p-4 space-y-4 font-medium">
        <div className="p-4 bg-red-950/80 border border-red-800 rounded-lg max-w-md text-center space-y-3">
          <h3 className="font-bold text-red-300">DATA TRANSMISSION ERROR</h3>
          <p className="text-xs text-slate-300">{errorMessage}</p>
          <button
            onClick={loadInitialData}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded font-bold text-xs"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#070d19] text-slate-100 font-sans">
      {/* Top Navbar */}
      <Navbar
        activePage={activePage}
        setActivePage={setActivePage}
        alertsCount={alerts.length}
      />

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto">
        {activePage === "dashboard" && (
          <Dashboard
            missionInputs={missionInputs}
            setMissionInputs={setMissionInputs}
            handleRecalculate={handleRecalculate}
            isAnalyzing={isAnalyzing}
            weather={weather}
            riskAnalysis={riskAnalysis}
            activeRoute={activeRoute}
            routes={routes}
            selectedRouteId={selectedRouteId}
            selectRoute={selectRoute}
            alerts={alerts}
            forecastTimeline={forecastTimeline}
            forecastStepIndex={forecastStepIndex}
            setForecastStepIndex={setForecastStepIndex}
            isForecastPlaying={isForecastPlaying}
            setIsForecastPlaying={setIsForecastPlaying}
            waypoints={waypoints}
            icebergs={icebergs}
            seaIce={seaIce}
            mapLayers={mapLayers}
            toggleMapLayer={toggleMapLayer}
            mapCenter={mapCenter}
            mapZoom={mapZoom}
            selectedWaypoint={selectedWaypoint}
            setSelectedWaypoint={setSelectedWaypoint}
            selectedIceberg={selectedIceberg}
            setSelectedIceberg={setSelectedIceberg}
            focusRegion={focusRegion}
            resetAntarcticView={resetAntarcticView}
            viewAlertOnMap={viewAlertOnMap}
            setActivePage={setActivePage}
          />
        )}

        {activePage === "map-view" && (
          <MapView
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
        )}

        {activePage === "route-planner" && (
          <RoutePlanner
            missionInputs={missionInputs}
            setMissionInputs={setMissionInputs}
            handleRecalculate={handleRecalculate}
            isAnalyzing={isAnalyzing}
            routes={routes}
            selectedRouteId={selectedRouteId}
            selectRoute={selectRoute}
            setActivePage={setActivePage}
          />
        )}

        {activePage === "risk-analysis" && (
          <RiskAnalysis
            riskAnalysis={riskAnalysis}
            routes={routes}
            forecastTimeline={forecastTimeline}
            selectedRouteId={selectedRouteId}
            selectRoute={selectRoute}
          />
        )}

        {activePage === "alerts" && (
          <Alerts
            alerts={alerts}
            alertFilter={alertFilter}
            setAlertFilter={setAlertFilter}
            viewAlertOnMap={viewAlertOnMap}
            setActivePage={setActivePage}
          />
        )}

        {activePage === "route-details" && (
          <div className="p-3 md:p-4 max-w-[1700px] mx-auto">
            <RouteDetails
              activeRoute={activeRoute}
              routes={routes}
              selectedRouteId={selectedRouteId}
              selectRoute={selectRoute}
              waypoints={waypoints}
              selectedWaypoint={selectedWaypoint}
              setSelectedWaypoint={setSelectedWaypoint}
              selectedIceberg={selectedIceberg}
              setSelectedIceberg={setSelectedIceberg}
              icebergs={icebergs}
              seaIce={seaIce}
              mapLayers={mapLayers}
              toggleMapLayer={toggleMapLayer}
              mapCenter={mapCenter}
              mapZoom={mapZoom}
              focusRegion={focusRegion}
              resetAntarcticView={resetAntarcticView}
              setActivePage={setActivePage}
              handleRecalculate={handleRecalculate}
              handleReroute={handleReroute}
              forecastTimeline={forecastTimeline}
            />
          </div>
        )}

        {activePage === "reports" && (
          <div className="p-3 md:p-4">
            <FullReport
              selectedRouteId={selectedRouteId}
              setActivePage={setActivePage}
            />
          </div>
        )}
      </main>

      {/* Bottom Status Telemetry Footer */}
      <StatusBar systemStatus={systemStatus} />
    </div>
  );
}
