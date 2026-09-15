import React from "react";
import { Navigation, Play, RotateCcw, Loader2, Anchor, ShieldCheck } from "lucide-react";
import { departurePorts, destinations } from "../../data/mockData.js";

export function MissionPlanner({
  missionInputs,
  setMissionInputs,
  handleRecalculate,
  isAnalyzing,
}) {
  const handleChange = (field, value) => {
    setMissionInputs((prev) => ({ ...prev, [field]: value }));
  };

  const isSameLocation =
    missionInputs.departurePort &&
    missionInputs.destination &&
    missionInputs.departurePort === missionInputs.destination;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isSameLocation) return;
    handleRecalculate(missionInputs);
  };

  return (
    <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-3 text-xs text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
        <div className="flex items-center gap-2">
          <Anchor className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            MISSION PLANNER
          </h3>
        </div>
        <span className="px-1.5 py-0.5 text-[10px] rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
          OPERATIONAL INPUTS
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-2.5">
        {/* Departure & Destination */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">
              Departure Port
            </label>
            <select
              value={missionInputs.departurePort || "Punta Arenas - Chile"}
              onChange={(e) => handleChange("departurePort", e.target.value)}
              className="w-full px-2.5 py-1.5 bg-[#080f1c] border border-[#1e304f] rounded text-slate-200 focus:outline-none focus:border-cyan-500 text-xs"
            >
              {departurePorts.map((port) => (
                <option key={port.label} value={port.label}>
                  {port.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">
              Destination
            </label>
            <select
              value={missionInputs.destination || "Palmer Station - Antarctic Peninsula"}
              onChange={(e) => handleChange("destination", e.target.value)}
              className="w-full px-2.5 py-1.5 bg-[#080f1c] border border-[#1e304f] rounded text-slate-200 focus:outline-none focus:border-cyan-500 text-xs"
            >
              {destinations.map((dest) => (
                <option key={dest.label} value={dest.label}>
                  {dest.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {isSameLocation && (
          <p className="text-[10px] text-amber-400">
            ⚠ Departure port and destination cannot be identical.
          </p>
        )}

        {/* Date & Vessel */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">
              Departure Date
            </label>
            <input
              type="date"
              value={missionInputs.date}
              onChange={(e) => handleChange("date", e.target.value)}
              className="w-full px-2.5 py-1.5 bg-[#080f1c] border border-[#1e304f] rounded text-slate-200 focus:outline-none focus:border-cyan-500 text-xs"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">
              Vessel Type
            </label>
            <select
              value={missionInputs.vessel}
              onChange={(e) => handleChange("vessel", e.target.value)}
              className="w-full px-2.5 py-1.5 bg-[#080f1c] border border-[#1e304f] rounded text-slate-200 focus:outline-none focus:border-cyan-500 text-xs"
            >
              <option value="R/V S.A. Agulhas II">R/V S.A. Agulhas II (PC 5)</option>
              <option value="R/V Polar Star">R/V Polar Star (Heavy Icebreaker)</option>
              <option value="Research Vessel Standard">Standard Expedition Vessel</option>
            </select>
          </div>
        </div>

        {/* Speed & Risk Threshold */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">
              Cruising Speed (kn)
            </label>
            <input
              type="number"
              min="10"
              max="25"
              step="0.5"
              value={missionInputs.cruisingSpeedKn}
              onChange={(e) => handleChange("cruisingSpeedKn", parseFloat(e.target.value))}
              className="w-full px-2.5 py-1.5 bg-[#080f1c] border border-[#1e304f] rounded text-slate-200 focus:outline-none focus:border-cyan-500 text-xs"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">
              Risk Threshold (%)
            </label>
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                min="10"
                max="50"
                value={missionInputs.operationalRiskThresholdPct}
                onChange={(e) => handleChange("operationalRiskThresholdPct", parseFloat(e.target.value))}
                className="w-full px-2.5 py-1.5 bg-[#080f1c] border border-[#1e304f] rounded text-slate-200 focus:outline-none focus:border-cyan-500 text-xs"
              />
              <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0" />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-1 grid grid-cols-2 gap-2">
          <button
            type="submit"
            disabled={isAnalyzing}
            className="w-full py-2 bg-gradient-to-r from-cyan-600 to-blue-700 hover:from-cyan-500 hover:to-blue-600 text-white font-semibold rounded text-xs transition flex items-center justify-center gap-1.5 shadow-md shadow-cyan-950"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Navigation className="w-3.5 h-3.5" />
                <span>Analyze & Generate</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => handleRecalculate(missionInputs)}
            disabled={isAnalyzing}
            className="w-full py-2 bg-[#14233c] hover:bg-[#1d3254] text-cyan-300 border border-[#1f375e] font-semibold rounded text-xs transition flex items-center justify-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Recalculate</span>
          </button>
        </div>
      </form>
    </div>
  );
}
