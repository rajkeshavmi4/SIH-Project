import React from "react";
import { Navigation, Check, AlertTriangle, ArrowRight } from "lucide-react";

export function RouteComparison({ routes, selectedRouteId, selectRoute, setActivePage }) {
  return (
    <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2.5 text-xs text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            Route Alternatives Comparison
          </h3>
        </div>
        <button
          onClick={() => setActivePage("route-planner")}
          className="text-[11px] text-cyan-400 hover:text-cyan-300 underline flex items-center gap-1 font-medium"
        >
          <span>Open Full Planner</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#1b2b45] text-slate-400 text-[10px] uppercase font-semibold">
              <th className="py-1.5 px-2">Route</th>
              <th className="py-1.5 px-2">Distance</th>
              <th className="py-1.5 px-2">Est. Fuel</th>
              <th className="py-1.5 px-2">ETA</th>
              <th className="py-1.5 px-2">Risk</th>
              <th className="py-1.5 px-2">Status</th>
              <th className="py-1.5 px-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#15233b]">
            {routes.map((route) => {
              const isSelected = selectedRouteId === route.id;
              const isRec = route.recommended;

              return (
                <tr
                  key={route.id}
                  onClick={() => selectRoute(route.id)}
                  className={`cursor-pointer transition ${
                    isSelected
                      ? "bg-[#14243e] font-medium text-slate-100"
                      : "hover:bg-[#0c1626] text-slate-300"
                  }`}
                >
                  <td className="py-2 px-2 font-bold flex items-center gap-1.5">
                    <span
                      className="w-2.5 h-2.5 rounded-full inline-block"
                      style={{ backgroundColor: route.color }}
                    ></span>
                    <span>{route.name}</span>
                    {isRec && (
                      <span className="px-1.5 py-0.2 rounded text-[9px] bg-cyan-950 text-cyan-300 border border-cyan-700 font-semibold">
                        RECOMMENDED
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-2">{route.distanceNm} nm</td>
                  <td className="py-2 px-2">{route.estimatedFuelMt} MT</td>
                  <td className="py-2 px-2">{route.etaFormatted}</td>
                  <td className="py-2 px-2">
                    <span
                      className={`font-bold ${
                        route.riskPct > 20
                          ? "text-red-400"
                          : route.riskPct > 10
                          ? "text-cyan-300"
                          : "text-emerald-400"
                      }`}
                    >
                      {route.riskPct}%
                    </span>
                  </td>
                  <td className="py-2 px-2 text-[10px]">
                    <span
                      className={`px-1.5 py-0.5 rounded ${
                        isRec
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800 font-semibold"
                          : route.riskPct > 20
                          ? "bg-red-950 text-red-300 border border-red-800 font-semibold"
                          : "bg-slate-800 text-slate-300 font-semibold"
                      }`}
                    >
                      {route.status}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        selectRoute(route.id);
                        setActivePage("route-details");
                      }}
                      className="px-2 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 rounded border border-cyan-800 text-[10px] font-medium transition inline-flex items-center gap-1"
                    >
                      <span>View Full Route</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
