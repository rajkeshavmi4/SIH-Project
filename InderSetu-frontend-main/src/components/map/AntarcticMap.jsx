import React, { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  Circle,
  Marker,
  Popup,
  Tooltip,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";
import { MapLegend } from "./MapLegend.jsx";
import { MapControls } from "./MapControls.jsx";
import { MapInfoPanel } from "./MapInfoPanel.jsx";
import { Ship, TriangleAlert, Shield, Layers, Navigation } from "lucide-react";

// Helper component to programmatically pan/zoom Leaflet map
function ChangeView({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center && Array.isArray(center) && center.length === 2) {
      map.setView(center, zoom, { animate: true, duration: 1.0 });
    }
  }, [center, zoom, map]);
  return null;
}

function SeaIceHeatmap({ seaIce, visible }) {
  const map = useMap();
  useEffect(() => {
    if (!visible) return undefined;
    const points = (seaIce || [])
      .filter((zone) => zone.isHeatPoint)
      .map((zone) => [zone.centerLat, zone.centerLng, zone.concentrationPct / 100]);
    if (!points.length || !L.heatLayer) return undefined;
    const layer = L.heatLayer(points, {
      radius: 28,
      blur: 24,
      maxZoom: 7,
      minOpacity: 0.2,
      gradient: {
        0.05: "#2563eb",
        0.25: "#22d3ee",
        0.5: "#f59e0b",
        0.75: "#ef4444",
        1.0: "#991b1b",
      },
    }).addTo(map);
    return () => map.removeLayer(layer);
  }, [map, seaIce, visible]);
  return null;
}

// Custom Marker Icons using Leaflet divIcon
const createVesselIcon = () =>
  L.divIcon({
    className: "vessel-marker-custom",
    html: `
      <div style="position: relative; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
        <div style="position: absolute; inset: 0; border: 2px solid #00d2ff; border-radius: 50%; animation: radar-ping 2s cubic-bezier(0,0,0.2,1) infinite;"></div>
        <div style="width: 24px; height: 24px; background: #075985; border: 2px solid #38bdf8; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(0, 210, 255, 0.8);">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 19 21 12 17 5 21 12 2"></polygon>
          </svg>
        </div>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });

const createIcebergIcon = (riskLevel) => {
  const isHigh = riskLevel === "High" || riskLevel === "Critical";
  const color = isHigh ? "#ef4444" : "#f59e0b";
  return L.divIcon({
    className: "iceberg-marker-custom",
    html: `
      <div style="position: relative; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">
        <div style="width: 22px; height: 22px; background: #0f172a; border: 2px solid ${color}; border-radius: 6px; transform: rotate(45deg); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px ${color}80;">
          <div style="transform: rotate(-45deg);">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2.5">
              <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
          </div>
        </div>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
};

const createWaypointIcon = (name, isSelected) =>
  L.divIcon({
    className: "waypoint-marker-custom",
    html: `
      <div style="position: relative; display: flex; flex-direction: column; align-items: center;">
        <div style="width: 22px; height: 22px; background: ${
          isSelected ? "#00d2ff" : "#1e293b"
        }; border: 2px solid ${
      isSelected ? "#ffffff" : "#38bdf8"
    }; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: ${
      isSelected ? "#09111e" : "#f1f5f9"
    }; font-family: monospace; box-shadow: ${
      isSelected ? "0 0 12px #00d2ff" : "0 2px 5px rgba(0,0,0,0.5)"
    };">
          ${name.replace("WP-", "")}
        </div>
      </div>
    `,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });

export function AntarcticMap({
  mapCenter,
  mapZoom,
  mapLayers,
  toggleMapLayer,
  routes,
  selectedRouteId,
  selectRoute,
  waypoints,
  icebergs,
  seaIce,
  selectedWaypoint,
  setSelectedWaypoint,
  selectedIceberg,
  setSelectedIceberg,
  focusRegion,
  resetAntarcticView,
  setActivePage,
}) {
  const tileUrl = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=cb1_3lw2_1_f37870c6e8e9fb454645db60";

  const routeCoordinates = (routeId) => {
    const route = routes.find((item) => item.id === routeId);
    return (route?.waypoints || []).map(([lat, lng]) => [lat, lng]);
  };

  const routeACoords = routeCoordinates("route-a");
  const routeBCoords = routeCoordinates("route-b");
  const routeCCoords = routeCoordinates("route-c");
  const activeRoute = routes.find((route) => route.id === selectedRouteId) || routes[1];
  const activeRouteCoordinates = routeCoordinates(selectedRouteId);
  const vesselCoords = activeRouteCoordinates[Math.min(2, Math.max(activeRouteCoordinates.length - 1, 0))] || [-61.8, -64.9];
  const routeLabel = (routeId) => routes.find((route) => route.id === routeId)?.name || routeId;
  const routeStats = (routeId) => {
    const route = routes.find((item) => item.id === routeId);
    return route ? `${route.distanceNm} nm / Risk ${route.riskPct}%` : "Backend route";
  };

  return (
    <div className="relative w-full h-full min-h-112.5 bg-[#060b14] rounded-lg overflow-hidden border border-[#1e2e4a] shadow-2xl flex flex-col">
      {/* Top Map Header Controls */}
      <div className="no-print bg-[#09111f]/90 backdrop-blur border-b border-[#1a2b45] px-3 py-2 flex flex-wrap items-center justify-between gap-2 z-1000">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-slate-200 tracking-wide uppercase">
            Antarctic Sector Telemetry Map
          </span>
          <span className="px-1.5 py-0.2 text-[10px] bg-slate-800 text-slate-300 rounded border border-slate-700">
            CartoDB Dark Polar
          </span>
        </div>

        {/* Quick Regional Presets */}
        <div className="flex items-center gap-1 overflow-x-auto text-[11px]">
          <span className="text-slate-400 hidden md:inline font-medium">Regions:</span>
          {[
            { id: "Peninsula", label: "Peninsula" },
            { id: "WeddellSea", label: "Weddell Sea" },
            { id: "RossSea", label: "Ross Sea" },
            { id: "AmundsenSea", label: "Amundsen Sea" },
            { id: "Palmer", label: "Palmer Station" },
          ].map((reg) => (
            <button
              key={reg.id}
              onClick={() => focusRegion(reg.id)}
              className="px-2 py-0.5 rounded bg-[#111e33] hover:bg-[#1a2d4c] text-cyan-300 border border-[#1e3254] transition text-[10px] font-medium"
            >
              {reg.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Interactive Leaflet Map Container */}
      <div className="relative flex-1 w-full h-full">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          zoomControl={false}
          className="w-full h-full"
        >
          <ChangeView center={mapCenter} zoom={mapZoom} />
          <SeaIceHeatmap seaIce={seaIce} visible={mapLayers.seaIce} />
          
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url={tileUrl}
            subdomains="abcd"
            maxZoom={20}
          />

          {/* SEA ICE CONCENTRATION ZONES */}
          {mapLayers.seaIce &&
            seaIce.filter((zone) => !zone.isHeatPoint).map((zone) => (
              <Circle
                key={zone.id}
                center={[zone.centerLat, zone.centerLng]}
                radius={zone.radiusMeters}
                pathOptions={{
                  color: zone.color,
                  fillColor: zone.color,
                  fillOpacity: zone.isHeatPoint ? 0.28 + (zone.concentrationPct / 100) * 0.34 : zone.concentrationPct / 300,
                  weight: zone.isHeatPoint ? 0 : 1.5,
                  dashArray: zone.isHeatPoint ? undefined : "4,4",
                }}
              >
                <Popup className="sea-ice-popup">
                  <div className="p-1 space-y-1.5 text-xs text-slate-100 min-w-50">
                    <div className="flex items-center justify-between border-b border-slate-700 pb-1">
                      <strong className="text-cyan-300">{zone.region}</strong>
                      <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-slate-800 text-amber-300 border border-amber-700">
                        {zone.concentrationPct}% Concentration
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-300">
                      <div>Trend: <span className="text-slate-100 font-semibold">{zone.trend}</span></div>
                      <div>Forecast: <span className="text-slate-100 font-semibold">{zone.forecast48h}</span></div>
                      <div>Wind: <span className="text-slate-100 font-semibold">{zone.wind}</span></div>
                      <div>Visibility: <span className="text-slate-100 font-semibold">{zone.visibilityKm} km</span></div>
                    </div>
                  </div>
                </Popup>
              </Circle>
            ))}

          {/* ROUTE POLYLINES */}
          {mapLayers.routes && (
            <>
              {/* Route A (Red / Direct) */}
              <Polyline
                positions={routeACoords}
                pathOptions={{
                  color: "#ef4444",
                  weight: selectedRouteId === "route-a" ? 4 : 2,
                  dashArray: "6,6",
                  opacity: selectedRouteId === "route-a" ? 1.0 : 0.5,
                }}
                eventHandlers={{
                  click: () => selectRoute("route-a"),
                }}
              >
                <Tooltip sticky>{routeLabel("route-a")} ({routeStats("route-a")})</Tooltip>
              </Polyline>

              {/* Route B (Cyan / Recommended) */}
              <Polyline
                positions={routeBCoords}
                pathOptions={{
                  color: "#00d2ff",
                  weight: selectedRouteId === "route-b" ? 5 : 3,
                  opacity: selectedRouteId === "route-b" ? 1.0 : 0.6,
                }}
                eventHandlers={{
                  click: () => selectRoute("route-b"),
                }}
              >
                <Tooltip sticky>{routeLabel("route-b")} ({routeStats("route-b")})</Tooltip>
              </Polyline>

              {/* Route C (Green / Safest) */}
              <Polyline
                positions={routeCCoords}
                pathOptions={{
                  color: "#10b981",
                  weight: selectedRouteId === "route-c" ? 4 : 2,
                  opacity: selectedRouteId === "route-c" ? 1.0 : 0.5,
                }}
                eventHandlers={{
                  click: () => selectRoute("route-c"),
                }}
              >
                <Tooltip sticky>{routeLabel("route-c")} ({routeStats("route-c")})</Tooltip>
              </Polyline>
            </>
          )}

          {/* ICEBERGS & TRAJECTORIES */}
          {mapLayers.icebergs &&
            icebergs.map((berg) => (
              <React.Fragment key={berg.id}>
                {/* Iceberg Marker */}
                <Marker
                  position={[berg.lat, berg.lng]}
                  icon={createIcebergIcon(berg.riskLevel)}
                  eventHandlers={{
                    click: () => setSelectedIceberg(berg),
                  }}
                >
                  <Popup>
                    <div className="p-1 space-y-1 text-xs text-slate-100 min-w-52.5">
                      <div className="flex items-center justify-between border-b border-slate-700 pb-1">
                        <strong className="text-amber-400">{berg.id}</strong>
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-red-950 text-red-300 border border-red-800">
                          {berg.riskLevel} Risk
                        </span>
                      </div>
                      <div className="text-[11px] space-y-0.5 text-slate-300">
                        <div>Size: <strong className="text-slate-100">{berg.size}</strong></div>
                        <div>Length: <strong className="text-slate-100">{berg.lengthMeters} m</strong></div>
                        <div>Distance to Route: <strong className="text-cyan-300">{berg.distanceToRouteNm} nm</strong></div>
                        <div>Drift: <strong className="text-slate-100">{berg.driftSpeedKn} kn {berg.driftDirection}</strong></div>
                      </div>
                      <div className="pt-1.5 flex gap-1 border-t border-slate-700">
                        <button
                          onClick={() => setSelectedIceberg(berg)}
                          className="w-full px-2 py-1 bg-cyan-900 hover:bg-cyan-800 text-cyan-200 rounded text-[10px] font-semibold"
                        >
                          View Iceberg Report & Trajectory
                        </button>
                      </div>
                    </div>
                  </Popup>
                </Marker>

                {/* Trajectory Polyline */}
                {mapLayers.trajectories && berg.predictedPositions && (
                  <Polyline
                    positions={berg.predictedPositions.map((pos) => [pos.lat, pos.lng])}
                    pathOptions={{
                      color: berg.riskLevel === "High" ? "#ef4444" : "#f59e0b",
                      weight: 1.5,
                      dashArray: "3,3",
                      opacity: 0.7,
                    }}
                  />
                )}
              </React.Fragment>
            ))}

          {/* ROUTE WAYPOINTS */}
          {mapLayers.routes &&
            waypoints.map((wp) => (
              <Marker
                key={wp.id}
                position={[wp.lat, wp.lng]}
                icon={createWaypointIcon(wp.id, selectedWaypoint?.id === wp.id)}
                eventHandlers={{
                  click: () => setSelectedWaypoint(wp),
                }}
              >
                <Tooltip direction="top" offset={[0, -10]}>
                  <div className="text-xs font-bold">{wp.name} ({wp.localRiskPct}% Risk)</div>
                </Tooltip>
              </Marker>
            ))}

          {/* RESEARCH VESSEL MARKER */}
          <Marker position={vesselCoords} icon={createVesselIcon()}>
            <Tooltip permanent direction="right" offset={[15, 0]}>
              <div className="text-xs font-bold text-cyan-300">
                R/V S.A. Agulhas II - {activeRoute?.name || "Active Route"}
              </div>
            </Tooltip>
          </Marker>
        </MapContainer>

        {/* Map Controls Floating Component */}
        <MapControls
          resetAntarcticView={resetAntarcticView}
          mapLayers={mapLayers}
          toggleMapLayer={toggleMapLayer}
        />

        {/* Map Legend Overlay */}
        <MapLegend routes={routes} />

        {/* Selected Object Info Sidebar / Drawer Panel */}
        <MapInfoPanel
          selectedWaypoint={selectedWaypoint}
          setSelectedWaypoint={setSelectedWaypoint}
          selectedIceberg={selectedIceberg}
          setSelectedIceberg={setSelectedIceberg}
          setActivePage={setActivePage}
        />
      </div>
    </div>
  );
}
