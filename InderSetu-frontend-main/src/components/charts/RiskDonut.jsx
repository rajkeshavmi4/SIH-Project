import React from "react";
import { Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
} from "chart.js";

ChartJS.register(ArcElement, Tooltip);

export function RiskDonut({ overallRisk = 28, breakdown }) {
  const ice = breakdown?.icePct || 35;
  const iceberg = breakdown?.icebergPct || 22;
  const weather = breakdown?.weatherPct || 25;
  const route = breakdown?.routePct || 30;

  const data = {
    labels: ["Ice Concentration", "Iceberg Drift", "Weather/Visibility", "Route Nav Risk"],
    datasets: [
      {
        data: [ice, iceberg, weather, route],
        backgroundColor: [
          "#3b82f6", // Ice - Blue
          "#f59e0b", // Iceberg - Amber
          "#00d2ff", // Weather - Cyan
          "#8b5cf6", // Route - Purple
        ],
        borderColor: "#0e1726",
        borderWidth: 2,
        hoverOffset: 3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false, // Custom legend below to prevent collision
      },
      tooltip: {
        backgroundColor: "#0e1726",
        titleColor: "#f1f5f9",
        bodyColor: "#00d2ff",
        borderColor: "#2d4368",
        borderWidth: 1,
        callbacks: {
          label: (context) => ` ${context.label}: ${context.raw}%`,
        },
      },
    },
    cutout: "74%",
  };

  return (
    <div className="flex flex-col h-full justify-between space-y-2">
      {/* Donut Ring with Centered Text */}
      <div className="relative w-full h-[135px] flex items-center justify-center">
        <Doughnut data={data} options={options} />
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-xl font-bold text-cyan-300 leading-none">{overallRisk}%</span>
          <span className="text-[9px] text-slate-400 font-medium tracking-wider uppercase mt-0.5">OVERALL RISK</span>
        </div>
      </div>

      {/* Custom Clean Legend Below Donut */}
      <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-slate-300 pt-1.5 border-t border-[#1a2b45]/60 font-medium">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0"></span>
          <span className="truncate">Ice Concentration</span>
        </div>
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0"></span>
          <span className="truncate">Iceberg Drift</span>
        </div>
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="w-2 h-2 rounded-full bg-cyan-400 shrink-0"></span>
          <span className="truncate">Weather/Visibility</span>
        </div>
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="w-2 h-2 rounded-full bg-purple-500 shrink-0"></span>
          <span className="truncate">Route Nav Risk</span>
        </div>
      </div>
    </div>
  );
}
