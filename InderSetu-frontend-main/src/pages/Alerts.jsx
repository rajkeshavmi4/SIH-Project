import React from "react";
import { Bell, AlertTriangle, ShieldAlert, MapPin, CheckCircle2, Info, Filter } from "lucide-react";

export function Alerts({
  alerts,
  alertFilter,
  setAlertFilter,
  viewAlertOnMap,
  setActivePage,
}) {
  const categories = ["All", "Ice", "Iceberg", "Weather", "Route", "Critical"];

  const filteredAlerts = alerts.filter((alt) => {
    if (alertFilter === "All") return true;
    if (alertFilter === "Critical") return alt.severity === "Critical" || alt.severity === "High";
    return alt.category.toLowerCase() === alertFilter.toLowerCase();
  });

  const totalCount = alerts.length;
  const criticalCount = alerts.filter((a) => a.severity === "Critical" || a.severity === "High").length;
  const activeCount = alerts.filter((a) => a.status === "Active").length;
  const ackCount = alerts.filter((a) => a.status === "Acknowledged").length;

  return (
    <div className="p-3 md:p-4 space-y-4 max-w-[1500px] mx-auto">
      {/* Header */}
      <div className="bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg flex items-center justify-between shadow-lg text-xs">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-amber-400" />
          <div>
            <h2 className="font-bold text-white text-sm uppercase">
              Operational Alerts & Notifications Center
            </h2>
            <p className="text-slate-400 text-[11px]">
              Real-Time Hydrographic Hazards, Iceberg Trajectory Crossings, & Meteorological Warnings
            </p>
          </div>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg text-center">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">TOTAL ALERTS</span>
          <strong className="text-xl text-slate-100 font-bold">{totalCount}</strong>
        </div>
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg text-center">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">HIGH / CRITICAL</span>
          <strong className="text-xl text-red-400 font-bold">{criticalCount}</strong>
        </div>
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg text-center">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">ACTIVE STATUS</span>
          <strong className="text-xl text-amber-300 font-bold">{activeCount}</strong>
        </div>
        <div className="bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg text-center">
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">ACKNOWLEDGED</span>
          <strong className="text-xl text-cyan-300 font-bold">{ackCount}</strong>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="flex items-center gap-1.5 overflow-x-auto text-xs">
        <div className="flex items-center gap-1 text-slate-400 pr-2 font-medium">
          <Filter className="w-3.5 h-3.5 text-cyan-400" />
          <span>Filter:</span>
        </div>
        {categories.map((cat) => {
          const isActive = alertFilter === cat;
          return (
            <button
              key={cat}
              onClick={() => setAlertFilter(cat)}
              className={`px-3 py-1.5 rounded-md transition font-semibold text-xs border ${
                isActive
                  ? "bg-cyan-950 text-cyan-300 border-cyan-500 shadow-md"
                  : "bg-[#0e1726] text-slate-400 border-[#1e2e4a] hover:bg-[#132238] hover:text-slate-200"
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Alert Feed List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="p-8 bg-[#0e1726] border border-[#1e2e4a] rounded-lg text-center text-slate-400 font-medium">
            No active alerts matching filter "{alertFilter}".
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const isCritical = alert.severity === "Critical" || alert.severity === "High";
            return (
              <div
                key={alert.id}
                className={`p-3.5 rounded-lg border text-xs shadow-lg space-y-2 transition ${
                  isCritical
                    ? "bg-red-950/30 border-red-800/60"
                    : "bg-[#0e1726] border-[#1e2e4a]"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1b2b45] pb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded font-bold text-[10px] uppercase ${
                        alert.severity === "Critical"
                          ? "bg-red-900 text-red-100 border border-red-700"
                          : alert.severity === "High"
                          ? "bg-amber-900 text-amber-100 border border-amber-700"
                          : "bg-slate-800 text-slate-300 border border-slate-700"
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <h3 className="font-bold text-slate-100 text-sm">
                      {alert.title}
                    </h3>
                  </div>

                  <div className="flex items-center gap-3 text-[11px]">
                    <span className="text-slate-400 font-medium">{alert.timestamp}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        alert.status === "Active"
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {alert.status}
                    </span>
                  </div>
                </div>

                <p className="text-slate-300 text-xs">{alert.description}</p>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#1b2b45] text-[11px]">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Location: <strong className="text-slate-200">{alert.location}</strong></span>
                  </div>

                  <button
                    onClick={() => viewAlertOnMap(alert)}
                    className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-semibold text-xs transition shadow flex items-center gap-1"
                  >
                    <MapPin className="w-3.5 h-3.5" />
                    <span>View on Map & Focus Location</span>
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
