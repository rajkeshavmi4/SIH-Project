import React from "react";
import { AntarcticMap } from "../components/map/AntarcticMap.jsx";
import { Compass, Map as MapIcon } from "lucide-react";

export function MapView({
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
  return (
    <div className="p-3 md:p-4 space-y-3 max-w-[1700px] mx-auto h-[calc(100vh-100px)] flex flex-col">
      {/* Map Header Toolbar */}
      <div className="bg-[#0e1726] border border-[#1e2e4a] p-2.5 rounded-lg flex flex-wrap items-center justify-between gap-2 shadow-lg shrink-0 text-xs">
        <div className="flex items-center gap-2">
          <MapIcon className="w-4 h-4 text-cyan-400" />
          <h2 className="font-bold text-slate-100 uppercase tracking-wide">
            Antarctic High-Resolution Navigation Map Station
          </h2>
        </div>

        <div className="flex items-center gap-2 text-[11px] font-medium">
          <span className="text-slate-400">Selected Route:</span>
          <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold">
            {selectedRouteId.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Full Height Map */}
      <div className="flex-1 w-full h-full min-h-[500px]">
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
    </div>
  );
}
