import { useState, useEffect, useCallback } from "react";
import {
  getMissionData,
  getSeaIceData,
  getIcebergData,
  getWeatherData,
  getRoutes,
  getRiskAnalysis,
  getAlerts,
  getForecast48h,
  getWaypoints,
  getSystemStatus,
  recalculateRoutes,
  rerouteEnRoute,
} from "../services/api.js";
import { departurePorts, destinations } from "../data/mockData.js";

export function useRouteData() {
  const [activePage, setActivePage] = useState("dashboard"); // dashboard, map-view, route-planner, risk-analysis, alerts, route-details, reports
  const [selectedRouteId, setSelectedRouteId] = useState("route-b");
  
  // Data states
  const [mission, setMission] = useState(null);
  const [seaIce, setSeaIce] = useState([]);
  const [icebergs, setIcebergs] = useState([]);
  const [weather, setWeather] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [forecastTimeline, setForecastTimeline] = useState([]);
  const [waypoints, setWaypoints] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);

  // Map state
  const [mapLayers, setMapLayers] = useState({
    seaIce: true,
    icebergs: true,
    trajectories: true,
    weather: true,
    wind: true,
    routes: true,
    riskZones: true,
  });

  const [mapCenter, setMapCenter] = useState([-64.77, -64.05]); // Palmer / Antarctic Peninsula
  const [mapZoom, setMapZoom] = useState(6);
  const [selectedWaypoint, setSelectedWaypoint] = useState(null);
  const [selectedIceberg, setSelectedIceberg] = useState(null);
  const [focusedAlert, setFocusedAlert] = useState(null);

  // Scrubber / Forecast animation state
  const [forecastStepIndex, setForecastStepIndex] = useState(0);
  const [isForecastPlaying, setIsForecastPlaying] = useState(false);

  // Alert Filter state
  const [alertFilter, setAlertFilter] = useState("All");

  // Mission Planner inputs state
  const [missionInputs, setMissionInputs] = useState({
    departurePort: "Punta Arenas - Chile",
    destination: "Palmer Station - Antarctic Peninsula",
    date: "2026-09-05",
    vessel: "R/V S.A. Agulhas II",
    cruisingSpeedKn: 20.0,
    operationalRiskThresholdPct: 30.0,
  });

  // Global loading / calculating states
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Fetch initial datasets
  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [m, ice, berg, w, r, risk, alt, fc, wp, sys] = await Promise.all([
        getMissionData(),
        getSeaIceData(),
        getIcebergData(),
        getWeatherData(),
        getRoutes(),
        getRiskAnalysis(),
        getAlerts(),
        getForecast48h(),
        getWaypoints("route-b"),
        getSystemStatus(),
      ]);

      setMission(m);
      setSeaIce(ice);
      setIcebergs(berg);
      setWeather(w);
      setRoutes(r);
      setRiskAnalysis(risk);
      setAlerts(alt);
      setForecastTimeline(fc);
      setWaypoints(wp);
      setSystemStatus(sys);
    } catch (err) {
      console.error("Failed to load navigation data:", err);
      setErrorMessage("Unable to load navigation data. Please retry.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Handle 48h forecast timeline playback
  useEffect(() => {
    let timer;
    if (isForecastPlaying && forecastTimeline.length > 0) {
      timer = setInterval(() => {
        setForecastStepIndex((prev) => (prev + 1) % forecastTimeline.length);
      }, 2000);
    }
    return () => clearInterval(timer);
  }, [isForecastPlaying, forecastTimeline.length]);

  // Toggle map layers
  const toggleMapLayer = (layerKey) => {
    setMapLayers((prev) => ({ ...prev, [layerKey]: !prev[layerKey] }));
  };

  // Select route
  const selectRoute = (routeId) => {
    setSelectedRouteId(routeId);
  };

  // Get active route object
  const activeRoute = routes.find((r) => r.id === selectedRouteId) || routes[1] || null;

  // Regional quick navigation presets
  const regionalPresets = {
    Peninsula: { center: [-64.77, -64.05], zoom: 6 },
    WeddellSea: { center: [-68.0, -55.0], zoom: 5 },
    RossSea: { center: [-75.0, 175.0], zoom: 4 },
    AmundsenSea: { center: [-73.0, -115.0], zoom: 4 },
    EastAntarctica: { center: [-70.0, 70.0], zoom: 4 },
    WestAntarctica: { center: [-78.0, -110.0], zoom: 4 },
    Palmer: { center: [-64.77, -64.05], zoom: 8 },
  };

  const focusRegion = (regionName) => {
    if (regionalPresets[regionName]) {
      setMapCenter(regionalPresets[regionName].center);
      setMapZoom(regionalPresets[regionName].zoom);
    }
  };

  const resetAntarcticView = () => {
    setMapCenter([-64.77, -64.05]);
    setMapZoom(6);
  };

  // Action: Navigate to map view and focus location (e.g. from Alert "View on Map")
  const viewAlertOnMap = (alert) => {
    if (alert && alert.lat && alert.lng) {
      setMapCenter([alert.lat, alert.lng]);
      setMapZoom(8);
      setFocusedAlert(alert);
      setActivePage("map-view");
    }
  };

  // Action: Recalculate routes with loading animation
  const handleRecalculate = async (customInputs) => {
    setIsAnalyzing(true);
    const updatedInputs = customInputs ? { ...missionInputs, ...customInputs } : missionInputs;
    setMissionInputs(updatedInputs);

    const selectedDep = departurePorts.find((p) => p.label === updatedInputs.departurePort) || departurePorts[0];
    const selectedDest = destinations.find((d) => d.label === updatedInputs.destination) || destinations[0];

    try {
      const res = await recalculateRoutes({
        ...updatedInputs,
        departureCoords: selectedDep.coords,
        destinationCoords: selectedDest.coords,
      });
      if (res.routes) {
        setRoutes(res.routes);
        const selectedUpdatedRoute = res.routes.find((route) => route.id === selectedRouteId) || res.routes[1];
        setWaypoints(
          (selectedUpdatedRoute?.waypoints || []).map(([lat, lng], index, points) => ({
            id: index === points.length - 1 ? "DEST" : `WP-${String(index).padStart(2, "0")}`,
            name: index === points.length - 1 ? "Destination" : `WP-${String(index).padStart(2, "0")}`,
            lat,
            lng,
            etaOffset: "Calculated",
            seaIcePct: 0,
            icebergRiskPct: 0,
            weatherRiskPct: 0,
            visibilityKm: 0,
            localRiskPct: 0,
            wind: "Live telemetry",
            wave: "Live telemetry",
            note: "Generated by the backend risk-aware route engine.",
          })),
        );
      }
      setMission((prev) => ({
        ...(prev || {}),
        departurePort: selectedDep.label,
        departureCoords: selectedDep.coords,
        destination: selectedDest.label,
        destinationCoords: selectedDest.coords,
        cruisingSpeedKn: updatedInputs.cruisingSpeedKn,
        operationalRiskThresholdPct: updatedInputs.operationalRiskThresholdPct,
        vesselName: updatedInputs.vessel,
        date: updatedInputs.date,
      }));

      if (selectedDest.coords) {
        setMapCenter(selectedDest.coords);
      }
    } catch (err) {
      console.error("Recalculation error:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReroute = async () => {
    setIsAnalyzing(true);
    const selectedDep = departurePorts.find((p) => p.label === missionInputs.departurePort) || departurePorts[0];
    const selectedDest = destinations.find((d) => d.label === missionInputs.destination) || destinations[0];
    try {
      const result = await rerouteEnRoute({
        ...missionInputs,
        departureCoords: selectedDep.coords,
        destinationCoords: selectedDest.coords,
      }, selectedRouteId);
      setRoutes((previousRoutes) => previousRoutes.map((route) => (
        route.id === selectedRouteId
          ? { ...route, ...result.route, waypoints: result.route.waypoints, summary: result.explanation }
          : route
      )));
      setWaypoints(mapWaypointsFromCoordinates(result.route.waypoints));
    } catch (err) {
      console.error("Reroute error:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return {
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
    setMapCenter,
    mapZoom,
    setMapZoom,
    selectedWaypoint,
    setSelectedWaypoint,
    selectedIceberg,
    setSelectedIceberg,
    focusedAlert,
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
  };
}

function mapWaypointsFromCoordinates(points = []) {
  return points.map(([lat, lng], index) => ({
    id: index === points.length - 1 ? "DEST" : `WP-${String(index).padStart(2, "0")}`,
    name: index === points.length - 1 ? "Destination" : `WP-${String(index).padStart(2, "0")}`,
    lat,
    lng,
    etaOffset: "Rerouted",
    seaIcePct: 0,
    icebergRiskPct: 0,
    weatherRiskPct: 0,
    visibilityKm: 0,
    localRiskPct: 0,
    wind: "Live telemetry",
    wave: "Live telemetry",
    note: "Generated by the en-route backend rerouting engine.",
  }));
}
