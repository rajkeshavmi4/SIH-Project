import React from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export function RiskBreakdown({ routes }) {
  const labels = ["Sea Ice Risk", "Iceberg Exposure", "Weather & Wave", "Navigation Risk"];

  const routeA = routes?.find((r) => r.id === "route-a")?.riskBreakdown || { seaIce: 28, iceberg: 26, weather: 18, navigation: 24 };
  const routeB = routes?.find((r) => r.id === "route-b")?.riskBreakdown || { seaIce: 10, iceberg: 8, weather: 14, navigation: 9 };
  const routeC = routes?.find((r) => r.id === "route-c")?.riskBreakdown || { seaIce: 5, iceberg: 4, weather: 10, navigation: 7 };

  const data = {
    labels,
    datasets: [
      {
        label: "Fastest Corridor",
        data: [routeA.seaIce, routeA.iceberg, routeA.weather, routeA.navigation],
        backgroundColor: "rgba(239, 68, 68, 0.7)",
        borderColor: "#ef4444",
        borderWidth: 1,
      },
      {
        label: "Moderate Corridor",
        data: [routeB.seaIce, routeB.iceberg, routeB.weather, routeB.navigation],
        backgroundColor: "rgba(0, 210, 255, 0.8)",
        borderColor: "#00d2ff",
        borderWidth: 1.5,
      },
      {
        label: "Safest Corridor",
        data: [routeC.seaIce, routeC.iceberg, routeC.weather, routeC.navigation],
        backgroundColor: "rgba(16, 185, 129, 0.7)",
        borderColor: "#10b981",
        borderWidth: 1,
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
        bodyColor: "#38bdf8",
        borderColor: "#2d4368",
        borderWidth: 1,
        callbacks: {
          label: (context) => ` ${context.dataset.label}: ${context.raw}% risk`,
        },
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
        suggestedMax: 35,
      },
    },
  };

  return (
    <div className="w-full h-55">
      <Bar data={data} options={options} />
    </div>
  );
}
