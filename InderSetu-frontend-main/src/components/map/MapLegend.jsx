import React, { useState } from "react";
import { ChevronDown, ChevronUp, Info } from "lucide-react";

export function MapLegend({ routes = [] }) {
  const [collapsed, setCollapsed] = useState(false);
  const getRoute = (id) => routes.find((route) => route.id === id);

  return (
    <div className="no-print absolute bottom-3 left-3 z-1000 bg-[#0c1626]/90 backdrop-blur-md border border-[#1e2f4d] rounded-md text-[11px] text-slate-300 shadow-xl max-w-60">
      <div
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between px-2.5 py-1.5 border-b border-[#1a2a45] cursor-pointer hover:bg-[#13223b] transition rounded-t-md select-none"
      >
        <div className="flex items-center gap-1.5 font-bold text-slate-100">
          <Info className="w-3.5 h-3.5 text-cyan-400" />
          <span>MAP LEGEND</span>
        </div>
        {collapsed ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        )}
      </div>

      {!collapsed && (
        <div className="p-2 space-y-2">
          {/* Navigation Routes */}
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">
              Routes
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-cyan-400 rounded-full inline-block"></span>
                  <span className="text-slate-200">{getRoute("route-b")?.name || "Moderate Corridor"}</span>
                </div>
                <span className="text-[9px] text-cyan-300 font-bold">{getRoute("route-b")?.riskPct ?? "--"}%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-red-500 border-dashed border-red-500 border-b inline-block"></span>
                  <span className="text-slate-300">{getRoute("route-a")?.name || "Fastest Corridor"}</span>
                </div>
                <span className="text-[9px] text-red-400 font-bold">{getRoute("route-a")?.riskPct ?? "--"}%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-emerald-400 rounded-full inline-block"></span>
                  <span className="text-slate-300">{getRoute("route-c")?.name || "Safest Corridor"}</span>
                </div>
                <span className="text-[9px] text-emerald-400 font-bold">{getRoute("route-c")?.riskPct ?? "--"}%</span>
              </div>
            </div>
          </div>

          {/* Sea Ice Concentration */}
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">
              Sea Ice Density
            </div>
            <div className="h-2 rounded mb-1" style={{ background: "linear-gradient(90deg, #2563eb 0%, #22d3ee 35%, #f59e0b 70%, #ef4444 100%)" }}></div>
            <div className="grid grid-cols-4 gap-1 text-[9px] text-center font-medium">
              <div className="text-blue-300">25% open</div>
              <div className="text-cyan-300">50%</div>
              <div className="text-amber-300">75%</div>
              <div className="text-red-300">100% core</div>
            </div>
          </div>

          {/* Hazards & Vectors */}
          <div className="pt-1 border-t border-[#1a2a45]">
            <div className="flex items-center justify-between text-[10px]">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rotate-45 bg-amber-500 border border-amber-300 inline-block"></span>
                <span className="text-slate-300">Iceberg Drift Hazard</span>
              </div>
              <span className="text-slate-500">Trajectories (48h)</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
