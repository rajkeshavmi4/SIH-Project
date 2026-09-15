import React from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export function ForecastChart({ forecastTimeline }) {
  const labels = forecastTimeline?.map((f) => f.step) || ["0h", "12h", "24h", "36h", "48h"];

  const data = {
    labels,
    datasets: [
      {
        label: "Sea Ice Concentration (%)",
        data: forecastTimeline?.map((f) => f.seaIcePct) || [28, 30, 33, 35, 37],
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        tension: 0.3,
        fill: true,
      },
      {
        label: "Overall Nav Risk (%)",
        data: forecastTimeline?.map((f) => f.overallRiskPct) || [28, 29, 32, 35, 36],
        borderColor: "#00d2ff",
        backgroundColor: "transparent",
        borderDash: [4, 4],
        tension: 0.3,
      },
      {
        label: "Wind Speed (kn)",
        data: forecastTimeline?.map((f) => f.windKn) || [16, 18, 21, 24, 22],
        borderColor: "#f59e0b",
        backgroundColor: "transparent",
        tension: 0.3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "#94a3b8",
          font: { size: 10, family: "monospace" },
          usePointStyle: true,
          boxWidth: 8,
        },
      },
      tooltip: {
        backgroundColor: "#0e1726",
        titleColor: "#f1f5f9",
        bodyColor: "#00d2ff",
        borderColor: "#2d4368",
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks: { color: "#94a3b8", font: { size: 10 } },
        grid: { color: "rgba(30, 46, 74, 0.5)" },
      },
      y: {
        ticks: { color: "#94a3b8", font: { size: 10 } },
        grid: { color: "rgba(30, 46, 74, 0.5)" },
        suggestedMax: 45,
      },
    },
  };

  return (
    <div className="w-full h-[220px]">
      <Line data={data} options={options} />
    </div>
  );
}
