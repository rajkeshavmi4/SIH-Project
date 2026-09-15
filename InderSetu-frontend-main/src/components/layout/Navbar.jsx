import React, { useState, useEffect } from "react";
import {
  Compass,
  Map as MapIcon,
  Navigation,
  ShieldAlert,
  Bell,
  FileText,
  Clock,
  Radio,
  UserCheck,
} from "lucide-react";

export function Navbar({ activePage, setActivePage, alertsCount = 0 }) {
  const [utcTime, setUtcTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Compass },
    { id: "map-view", label: "Map View", icon: MapIcon },
    { id: "route-planner", label: "Route Planner", icon: Navigation },
    { id: "risk-analysis", label: "Risk Analysis", icon: ShieldAlert },
    { id: "alerts", label: "Alerts", icon: Bell, badge: alertsCount },
    { id: "reports", label: "Reports", icon: FileText },
  ];

  return (
    <header className="no-print bg-[#0a1220] border-b border-[#1e2e4a] text-slate-100 shadow-md">
      {/* Top Meta Header Bar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2 text-xs border-b border-[#142238] bg-[#070d18]">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-950/80 border border-blue-800/60 text-blue-300 font-semibold tracking-wider uppercase">
            <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
            <span>DEMO MODE - PRE-FLIGHT SIMULATION</span>
          </div>
          <span className="text-slate-500 hidden sm:inline">|</span>
          <span className="text-slate-400 hidden sm:inline">
            Vessel: <strong className="text-slate-200">R/V S.A. Agulhas II</strong> (PC 5)
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-slate-300 text-[11px]">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>{utcTime || "UTC LOADING..."}</span>
          </div>

          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
            <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Capt. E. Shackleton</span>
          </div>
        </div>
      </div>

      {/* Main Command Navigation Header */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg overflow-hidden border border-cyan-400/40 shadow-lg shadow-cyan-950/50 shrink-0 bg-slate-900">
            <img src="/logo.png" alt="IndraSetu Logo" className="w-full h-full object-cover" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">
              IndraSetu
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">
              Antarctic Navigation System and IndraSetu
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 mt-2 sm:mt-0 overflow-x-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-150 relative ${
                  isActive
                    ? "bg-[#162744] text-cyan-300 border border-cyan-500/40 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#111e33]"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-cyan-400" : "text-slate-400"}`} />
                <span>{item.label}</span>
                {item.badge > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
