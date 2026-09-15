import React from "react";
import { Play, Pause, Clock, Wind, Eye, Waves, ShieldAlert, Cpu } from "lucide-react";

export function ForecastTimeline({
  forecastTimeline,
  forecastStepIndex,
  setForecastStepIndex,
  isForecastPlaying,
  setIsForecastPlaying,
}) {
  const currentStep = forecastTimeline[forecastStepIndex] || {
    step: "0h",
    seaIcePct: 28,
    icebergDensity: 0.42,
    windKn: 16,
    waveM: 1.2,
    visibilityKm: 8.5,
    overallRiskPct: 28,
  };

  return (
    <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2.5 text-xs text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1b2b45] pb-2">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            48-Hour Environmental & Risk Forecast
          </h3>
        </div>

        {/* Play / Pause Scrubber Control */}
        <button
          onClick={() => setIsForecastPlaying(!isForecastPlaying)}
          className={`px-3 py-1 rounded text-xs font-bold transition flex items-center gap-1.5 ${
            isForecastPlaying
              ? "bg-amber-600 hover:bg-amber-500 text-white"
              : "bg-cyan-600 hover:bg-cyan-500 text-white"
          }`}
        >
          {isForecastPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5" />
              <span>Pause Timeline</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5" />
              <span>Play 48h Simulation</span>
            </>
          )}
        </button>
      </div>

      {/* Timeline Steps Buttons */}
      <div className="grid grid-cols-5 gap-1">
        {forecastTimeline.map((item, idx) => {
          const isActive = forecastStepIndex === idx;
          return (
            <button
              key={item.step}
              onClick={() => {
                setIsForecastPlaying(false);
                setForecastStepIndex(idx);
              }}
              className={`py-1.5 px-2 rounded text-center transition border text-xs ${
                isActive
                  ? "bg-cyan-950 text-cyan-300 border-cyan-500 font-bold shadow-lg"
                  : "bg-[#09111e] text-slate-400 border-[#1a2b45] hover:bg-[#111f35] hover:text-slate-200"
              }`}
            >
              <div className="text-[10px] text-slate-500">T+</div>
              <div>{item.step}</div>
            </button>
          );
        })}
      </div>

      {/* Dynamic Forecast Telemetry Metrics Display */}
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 pt-1 text-[11px]">
        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45] text-center">
          <span className="text-[9px] text-slate-400 block uppercase">TIMELINE STEP</span>
          <strong className="text-cyan-300 text-sm font-bold">+{currentStep.step}</strong>
        </div>

        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45] text-center">
          <span className="text-[9px] text-slate-400 block uppercase">SEA ICE %</span>
          <strong className="text-blue-300 text-sm font-bold">{currentStep.seaIcePct}%</strong>
        </div>

        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45] text-center">
          <span className="text-[9px] text-slate-400 block uppercase">ICEBERG DENSITY</span>
          <strong className="text-amber-300 text-sm font-bold">{currentStep.icebergDensity} /100km²</strong>
        </div>

        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45] text-center">
          <span className="text-[9px] text-slate-400 block uppercase">WIND VELOCITY</span>
          <strong className="text-slate-100 text-sm font-bold">{currentStep.windKn} kn NE</strong>
        </div>

        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45] text-center">
          <span className="text-[9px] text-slate-400 block uppercase">SWELL HEIGHT</span>
          <strong className="text-cyan-300 text-sm font-bold">{currentStep.waveM} m</strong>
        </div>

        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45] text-center">
          <span className="text-[9px] text-slate-400 block uppercase">OVERALL RISK</span>
          <strong className="text-amber-400 text-sm font-bold">{currentStep.overallRiskPct}%</strong>
        </div>
      </div>
    </div>
  );
}
