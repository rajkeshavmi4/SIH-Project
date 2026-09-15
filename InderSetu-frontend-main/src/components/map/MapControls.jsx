import React, { useState } from "react";
import { RotateCcw, LocateFixed, Eye, EyeOff, Layers } from "lucide-react";

export function MapControls({ resetAntarcticView, mapLayers, toggleMapLayer }) {
  const [layersOpen, setLayersOpen] = useState(false);

  const layerItems = [
    { key: "seaIce", label: "Sea Ice Density" },
    { key: "icebergs", label: "Icebergs Detection" },
    { key: "trajectories", label: "Drift Trajectories (48h)" },
    { key: "routes", label: "Navigation Routes" },
    { key: "weather", label: "Weather & Wind Fields" },
    { key: "riskZones", label: "Risk Zones" },
  ];

  return (
    <div className="no-print absolute top-3 right-3 z-[1000] flex flex-col gap-1.5">
      {/* Reset Antarctic View */}
      <button
        onClick={resetAntarcticView}
        title="Reset Antarctic View"
        className="p-2 bg-[#0d1726]/90 hover:bg-[#15243b] text-cyan-300 border border-[#1e304f] rounded-md shadow-lg transition flex items-center gap-1.5 text-xs font-medium"
      >
        <RotateCcw className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">Reset View</span>
      </button>

      {/* Layer Toggles Menu */}
      <div className="relative">
        <button
          onClick={() => setLayersOpen(!layersOpen)}
          title="Toggle Layers"
          className="p-2 bg-[#0d1726]/90 hover:bg-[#15243b] text-slate-200 border border-[#1e304f] rounded-md shadow-lg transition flex items-center gap-1.5 text-xs font-medium w-full justify-between"
        >
          <div className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Layers</span>
          </div>
        </button>

        {layersOpen && (
          <div className="absolute right-0 mt-1 w-52 bg-[#0c1626]/95 backdrop-blur border border-[#1e2f4d] rounded-md shadow-2xl p-2 text-xs space-y-1.5 text-slate-200 z-[1010]">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider border-b border-[#1a2a45] pb-1 font-semibold">
              MAP OVERLAY TOGGLES
            </div>
            {layerItems.map((item) => {
              const isEnabled = mapLayers[item.key];
              return (
                <button
                  key={item.key}
                  onClick={() => toggleMapLayer(item.key)}
                  className={`w-full flex items-center justify-between px-2 py-1 rounded transition text-left text-[11px] ${
                    isEnabled
                      ? "bg-[#15243c] text-cyan-300 font-semibold"
                      : "text-slate-400 hover:bg-[#101b2d]"
                  }`}
                >
                  <span>{item.label}</span>
                  {isEnabled ? (
                    <Eye className="w-3.5 h-3.5 text-cyan-400" />
                  ) : (
                    <EyeOff className="w-3.5 h-3.5 text-slate-600" />
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
