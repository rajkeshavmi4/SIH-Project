import React from "react";
import { Navigation, MapPin, Eye, Wind } from "lucide-react";

export function WaypointTable({ waypoints, selectedWaypoint, setSelectedWaypoint }) {
  return (
    <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            Route B Waypoint Directory & Hydrographic Analysis
          </h3>
        </div>
        <span className="text-[10px] text-slate-400 font-medium">
          {waypoints.length} WAYPOINTS LOGGED
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#1b2b45] text-slate-400 text-[10px] uppercase font-semibold">
              <th className="py-2 px-2">Waypoint</th>
              <th className="py-2 px-2">Latitude</th>
              <th className="py-2 px-2">Longitude</th>
              <th className="py-2 px-2">Sea Ice %</th>
              <th className="py-2 px-2">Iceberg Risk</th>
              <th className="py-2 px-2">Weather Risk</th>
              <th className="py-2 px-2">Visibility</th>
              <th className="py-2 px-2">Local Risk</th>
              <th className="py-2 px-2">Operational Note</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#15233b]">
            {waypoints.map((wp) => {
              const isSelected = selectedWaypoint?.id === wp.id;
              return (
                <tr
                  key={wp.id}
                  onClick={() => setSelectedWaypoint(wp)}
                  className={`cursor-pointer transition ${
                    isSelected
                      ? "bg-[#162744] text-cyan-300 font-bold"
                      : "hover:bg-[#0c1626] text-slate-300"
                  }`}
                >
                  <td className="py-2 px-2 font-bold text-cyan-400 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>{wp.name}</span>
                  </td>
                  <td className="py-2 px-2">{wp.lat.toFixed(2)}°S</td>
                  <td className="py-2 px-2">{wp.lng.toFixed(2)}°W</td>
                  <td className="py-2 px-2 text-blue-300 font-medium">{wp.seaIcePct}%</td>
                  <td className="py-2 px-2 text-amber-300 font-medium">{wp.icebergRiskPct}%</td>
                  <td className="py-2 px-2 text-cyan-300 font-medium">{wp.weatherRiskPct}%</td>
                  <td className="py-2 px-2">{wp.visibilityKm} km</td>
                  <td className="py-2 px-2 font-bold text-emerald-400">{wp.localRiskPct}%</td>
                  <td className="py-2 px-2 text-[10px] text-slate-400 italic">{wp.note}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
