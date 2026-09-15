import React from "react";
import { Wind, Thermometer, Waves, Eye, Clock, CloudSnow } from "lucide-react";

export function EnvironmentalConditions({ weather }) {
  const windSpeed = weather?.windSpeedKn || 16;
  const windDir = weather?.windDirection || "NE";
  const airTemp = weather?.airTempC || -18.6;
  const seaTemp = weather?.seaTempC || -1.8;
  const waveHeight = weather?.waveHeightM || 1.2;
  const visibility = weather?.visibilityKm || 8.5;
  const timestamp = weather?.lastUpdatedUtc || "2026-09-04 18:00 UTC";

  return (
    <div className="bg-[#0e1726] border border-[#1e2e4a] rounded-lg p-3 shadow-lg space-y-2 text-xs text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1b2b45] pb-1.5">
        <div className="flex items-center gap-2">
          <CloudSnow className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            ENVIRONMENTAL METRICS
          </h3>
        </div>
        <div className="flex items-center gap-1 text-[10px] text-slate-400">
          <Clock className="w-3 h-3 text-cyan-400" />
          <span>{timestamp}</span>
        </div>
      </div>

      {/* Compact Metric Rows */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45]">
          <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mb-0.5 uppercase">
            <Wind className="w-3 h-3 text-cyan-400" />
            <span>WIND VELOCITY</span>
          </div>
          <div className="text-sm font-bold text-slate-100">
            {windSpeed} kn <span className="text-cyan-300 text-xs">{windDir}</span>
          </div>
        </div>

        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45]">
          <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mb-0.5 uppercase">
            <Thermometer className="w-3 h-3 text-blue-400" />
            <span>AIR / SEA TEMP</span>
          </div>
          <div className="text-sm font-bold text-slate-100">
            {airTemp}°C <span className="text-blue-300 text-xs">/ {seaTemp}°C</span>
          </div>
        </div>

        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45]">
          <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mb-0.5 uppercase">
            <Waves className="w-3 h-3 text-cyan-400" />
            <span>SWELL WAVE</span>
          </div>
          <div className="text-sm font-bold text-slate-100">
            {waveHeight} m
          </div>
        </div>

        <div className="p-2 rounded bg-[#09111e] border border-[#1a2b45] col-span-2 sm:col-span-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 uppercase">
              <Eye className="w-3.5 h-3.5 text-emerald-400" />
              <span>VISIBILITY RANGE (WEATHER RISK FACTOR)</span>
            </div>
            <strong className="text-emerald-300 text-sm">{visibility} km</strong>
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">
            Note: Visibility is an operational weather risk factor for lookout watchkeeping.
          </p>
        </div>
      </div>
    </div>
  );
}
