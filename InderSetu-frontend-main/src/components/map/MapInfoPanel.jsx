import React from "react";
import { X, Navigation, TriangleAlert, Wind, Eye, Compass, ArrowRight } from "lucide-react";

export function MapInfoPanel({
  selectedWaypoint,
  setSelectedWaypoint,
  selectedIceberg,
  setSelectedIceberg,
  setActivePage,
}) {
  if (!selectedWaypoint && !selectedIceberg) return null;

  return (
    <div className="no-print absolute top-14 right-3 z-[1000] w-80 max-w-[calc(100vw-2rem)] bg-[#0a1322]/95 backdrop-blur border border-[#1e304f] rounded-lg shadow-2xl p-3 text-xs text-slate-200 animate-fadeIn">
      {/* Waypoint Detail Drawer */}
      {selectedWaypoint && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between border-b border-[#1a2b45] pb-2">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-300 flex items-center justify-center font-bold text-xs">
                {selectedWaypoint.name.replace("WP-", "")}
              </div>
              <div>
                <h4 className="font-bold text-slate-100">{selectedWaypoint.name}</h4>
                <p className="text-[10px] text-slate-400">
                  {selectedWaypoint.lat.toFixed(2)}°, {selectedWaypoint.lng.toFixed(2)}°
                </p>
              </div>
            </div>
            <button
              onClick={() => setSelectedWaypoint(null)}
              className="p-1 text-slate-400 hover:text-slate-200 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="p-1.5 rounded bg-[#111f36] border border-[#1b2f50]">
              <span className="text-slate-400 block text-[10px]">Local Risk</span>
              <strong className="text-cyan-300 text-sm font-bold">{selectedWaypoint.localRiskPct}%</strong>
            </div>
            <div className="p-1.5 rounded bg-[#111f36] border border-[#1b2f50]">
              <span className="text-slate-400 block text-[10px]">ETA Offset</span>
              <strong className="text-slate-200 text-sm font-bold">+{selectedWaypoint.etaOffset}</strong>
            </div>
            <div className="p-1.5 rounded bg-[#111f36] border border-[#1b2f50]">
              <span className="text-slate-400 block text-[10px]">Sea Ice Density</span>
              <strong className="text-blue-300 font-bold">{selectedWaypoint.seaIcePct}%</strong>
            </div>
            <div className="p-1.5 rounded bg-[#111f36] border border-[#1b2f50]">
              <span className="text-slate-400 block text-[10px]">Visibility</span>
              <strong className="text-slate-200 font-bold">{selectedWaypoint.visibilityKm} km</strong>
            </div>
          </div>

          <div className="p-2 rounded bg-[#111f36] border border-[#1b2f50] space-y-1">
            <div className="flex items-center gap-1 text-[10px] text-slate-400">
              <Wind className="w-3 h-3 text-cyan-400" />
              <span>Conditions: {selectedWaypoint.wind} | Wave: {selectedWaypoint.wave}</span>
            </div>
            <p className="text-[11px] text-slate-300 italic">"{selectedWaypoint.note}"</p>
          </div>

          <button
            onClick={() => setActivePage("route-details")}
            className="w-full py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-semibold text-xs transition flex items-center justify-center gap-1.5 shadow"
          >
            <span>View Full Route B Waypoint Breakdown</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Iceberg Detail Drawer */}
      {selectedIceberg && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between border-b border-[#1a2b45] pb-2">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-amber-950/80 border border-amber-500/40 text-amber-300 flex items-center justify-center font-bold text-xs">
                <TriangleAlert className="w-4 h-4 text-amber-400" />
              </div>
              <div>
                <h4 className="font-bold text-amber-300">{selectedIceberg.id}</h4>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-red-950 text-red-300 border border-red-800 font-semibold">
                  {selectedIceberg.riskLevel} Hazard
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedIceberg(null)}
              className="p-1 text-slate-400 hover:text-slate-200 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="p-1.5 rounded bg-[#111f36] border border-[#1b2f50]">
              <span className="text-slate-400 block text-[10px]">Classification</span>
              <strong className="text-slate-100">{selectedIceberg.size}</strong>
            </div>
            <div className="p-1.5 rounded bg-[#111f36] border border-[#1b2f50]">
              <span className="text-slate-400 block text-[10px]">Distance to Route</span>
              <strong className="text-cyan-300 font-bold">{selectedIceberg.distanceToRouteNm} nm</strong>
            </div>
            <div className="p-1.5 rounded bg-[#111f36] border border-[#1b2f50]">
              <span className="text-slate-400 block text-[10px]">Length / Scale</span>
              <strong className="text-slate-200 font-bold">{selectedIceberg.lengthMeters} m</strong>
            </div>
            <div className="p-1.5 rounded bg-[#111f36] border border-[#1b2f50]">
              <span className="text-slate-400 block text-[10px]">Drift Velocity</span>
              <strong className="text-amber-300 font-bold">{selectedIceberg.driftSpeedKn} kn {selectedIceberg.driftDirection}</strong>
            </div>
          </div>

          {/* 48h Trajectory Steps */}
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1 font-semibold">
              Predicted 48h Drift Positions
            </span>
            <div className="space-y-1">
              {selectedIceberg.predictedPositions?.map((pos, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between px-2 py-1 rounded bg-[#111f36] text-[10px]"
                >
                  <span className="text-cyan-400 font-bold">{pos.step}</span>
                  <span className="text-slate-300">
                    {pos.lat.toFixed(2)}°, {pos.lng.toFixed(2)}°
                  </span>
                  <span className="text-slate-500">T+{pos.time}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="text-[10px] text-slate-400 italic">
            Trajectory calculated via hydrodynamic ocean drift vectors. DEMO simulated data.
          </p>
        </div>
      )}
    </div>
  );
}
