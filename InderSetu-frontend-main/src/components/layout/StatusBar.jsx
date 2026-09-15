import React from "react";
import { Activity, Database, MapPin, Cpu, Server, CheckCircle2 } from "lucide-react";

export function StatusBar({ systemStatus }) {
  return (
    <footer className="no-print bg-[#080f1c] border-t border-[#1a2b45] px-4 py-1.5 text-[11px] text-slate-400 flex flex-wrap items-center justify-between gap-2 shadow-inner">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <span>System:</span>
          <strong className="text-slate-200">{systemStatus?.system || "Operational"}</strong>
        </div>

        <div className="flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span>Data Layer:</span>
          <strong className="text-cyan-300">{systemStatus?.dataMode || "Connected / Demo Mode"}</strong>
        </div>

        <div className="flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-blue-400" />
          <span>Map Engine:</span>
          <strong className="text-slate-200">{systemStatus?.mapService || "Available"}</strong>
        </div>

        <div className="flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-purple-400" />
          <span>AI Engine:</span>
          <strong className="text-slate-200">{systemStatus?.aiEngine || "Ready"}</strong>
        </div>

        <div className="flex items-center gap-1.5">
          <Server className="w-3.5 h-3.5 text-amber-400" />
          <span>Backend API:</span>
          <span className="px-1.5 py-0.2 rounded bg-amber-950/80 text-amber-300 border border-amber-800/60 text-[10px]">
            {systemStatus?.backendApi || "Demo / Ready for Integration"}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        <span className="text-slate-400">
          Last Sync: <strong className="text-slate-300">{systemStatus?.lastSyncUtc || "UTC"}</strong>
        </span>
      </div>
    </footer>
  );
}
