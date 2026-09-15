import React from "react";
import { Bell, MapPin, ArrowRight, AlertTriangle, Info, ShieldAlert } from "lucide-react";

export function AlertsPanel({ alerts, viewAlertOnMap, setActivePage }) {
  return (
    <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2.5 text-xs text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-amber-400" />
          <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            Alerts & Notifications
          </h3>
        </div>
        <button
          onClick={() => setActivePage("alerts")}
          className="text-[11px] text-cyan-400 hover:text-cyan-300 underline flex items-center gap-1 font-medium"
        >
          <span>View All Alerts ({alerts.length})</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
        {alerts.slice(0, 3).map((alert) => {
          const isCritical = alert.severity === "Critical" || alert.severity === "High";
          return (
            <div
              key={alert.id}
              className={`p-2 rounded-md border text-xs transition space-y-1 ${
                isCritical
                  ? "bg-red-950/40 border-red-800/60 text-red-100"
                  : "bg-[#09111e] border-[#1a2b45] text-slate-200"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 font-bold">
                  {isCritical ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                  ) : (
                    <Info className="w-3.5 h-3.5 text-cyan-400" />
                  )}
                  <span>{alert.title}</span>
                </div>
                <span
                  className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                    alert.severity === "Critical"
                      ? "bg-red-900 text-red-100"
                      : alert.severity === "High"
                      ? "bg-amber-900 text-amber-100"
                      : "bg-slate-800 text-slate-300"
                  }`}
                >
                  {alert.severity}
                </span>
              </div>

              <p className="text-[11px] text-slate-300 line-clamp-2">{alert.description}</p>

              <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400 border-t border-[#16253c]">
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-cyan-400" />
                  <span>{alert.location}</span>
                </div>

                <button
                  onClick={() => viewAlertOnMap(alert)}
                  className="px-2 py-0.5 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 font-semibold transition"
                >
                  View on Map
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
