import React, { useState, useEffect } from "react";
import { getRouteReport } from "../../services/api.js";
import { Printer, Download, ArrowLeft, ShieldCheck, FileText, CheckCircle2, AlertTriangle } from "lucide-react";

export function FullReport({ selectedRouteId = "route-b", setActivePage }) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadReport() {
      setLoading(true);
      try {
        const data = await getRouteReport(selectedRouteId);
        setReportData(data);
      } catch (err) {
        console.error("Failed to load report:", err);
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, [selectedRouteId]);

  const handlePrint = () => {
    window.print();
  };

  if (loading || !reportData) {
    return (
      <div className="p-8 text-center text-slate-300 font-medium">
        Generating Official Mission Report...
      </div>
    );
  }

  const { mission, route, waypoints, environment, risk, icebergs, alerts, systemStatus, generatedAtUtc } = reportData;

  return (
    <div className="space-y-4 max-w-5xl mx-auto report-page-container">
      {/* Top Action Bar */}
      <div className="no-print bg-[#0e1726] border border-[#1e2e4a] p-3 rounded-lg flex items-center justify-between shadow-lg">
        <button
          onClick={() => setActivePage("dashboard")}
          className="px-3 py-1.5 bg-[#132238] hover:bg-[#1a2e4c] text-cyan-300 border border-[#1e3254] rounded text-xs font-semibold transition flex items-center gap-1.5"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePrint}
            className="px-4 py-2 bg-linear-to-r from-cyan-600 to-blue-700 hover:from-cyan-500 hover:to-blue-600 text-white rounded text-xs font-bold transition flex items-center gap-2 shadow-lg"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Save as PDF Report</span>
          </button>
        </div>
      </div>

      {/* Printable Report Paper Layout */}
      <div className="bg-[#0b1322] print:bg-white text-slate-200 print:text-slate-900 p-6 md:p-8 rounded-lg border border-[#1e2e4a] print:border-none shadow-2xl space-y-6 report-card">
        {/* Document Header */}
        <div className="border-b-2 border-cyan-500/40 print:border-slate-800 pb-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-cyan-400 print:text-slate-900 tracking-wide uppercase">
              IndraSetu - Antarctic Navigation System
            </h1>
            <h2 className="text-sm font-semibold text-slate-300 print:text-slate-700 mt-0.5 uppercase">
              Official Mission Voyage & Risk Assessment Report
            </h2>
          </div>
          <div className="text-right text-xs text-slate-400 print:text-slate-600">
            <div>Mission ID: <strong className="text-slate-100 print:text-slate-900">{mission.voyageId}</strong></div>
            <div>Generated: {generatedAtUtc}</div>
          </div>
        </div>

        {/* 1. Mission Overview */}
        <section className="space-y-2">
          <h3 className="text-sm font-bold text-cyan-300 print:text-slate-900 border-b border-[#1b2b45] print:border-slate-300 pb-1 uppercase">
            1. Mission Overview
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded border border-[#1a2b45] print:border-slate-300">
              <span className="text-[10px] text-slate-400 print:text-slate-600 uppercase font-semibold block">VESSEL</span>
              <strong>{mission.vesselName}</strong>
            </div>
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded border border-[#1a2b45] print:border-slate-300">
              <span className="text-[10px] text-slate-400 print:text-slate-600 uppercase font-semibold block">DEPARTURE</span>
              <strong>{mission.departurePort}</strong>
            </div>
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded border border-[#1a2b45] print:border-slate-300">
              <span className="text-[10px] text-slate-400 print:text-slate-600 uppercase font-semibold block">DESTINATION</span>
              <strong>{mission.destination}</strong>
            </div>
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded border border-[#1a2b45] print:border-slate-300">
              <span className="text-[10px] text-slate-400 print:text-slate-600 uppercase font-semibold block">DATE / SPEED</span>
              <strong>{mission.date} @ {mission.cruisingSpeedKn} kn</strong>
            </div>
          </div>
        </section>

        {/* 2. Environmental Conditions */}
        <section className="space-y-2">
          <h3 className="text-sm font-bold text-cyan-300 print:text-slate-900 border-b border-[#1b2b45] print:border-slate-300 pb-1 uppercase">
            2. Environmental Conditions
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded">Wind: {environment.windSpeedKn} kn {environment.windDirection}</div>
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded">Air Temp: {environment.airTempC}°C</div>
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded">Sea Temp: {environment.seaTempC}°C</div>
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded">Wave Height: {environment.waveHeightM} m</div>
            <div className="p-2 bg-[#09111e] print:bg-slate-100 rounded">Visibility: {environment.visibilityKm} km</div>
          </div>
        </section>

        {/* 3 & 4. Sea Ice & Iceberg Analysis */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <section className="space-y-2">
            <h3 className="text-sm font-bold text-cyan-300 print:text-slate-900 border-b border-[#1b2b45] print:border-slate-300 pb-1 uppercase">
              3. Sea Ice Analysis
            </h3>
            <p className="text-xs text-slate-300 print:text-slate-700">
              Weddell Sea pack ice density is 75% (Critical). Route B transit corridor maintains an average sea ice density under 18% (Low risk).
            </p>
          </section>

          <section className="space-y-2">
            <h3 className="text-sm font-bold text-cyan-300 print:text-slate-900 border-b border-[#1b2b45] print:border-slate-300 pb-1 uppercase">
              4. Iceberg Hazard Analysis
            </h3>
            <p className="text-xs text-slate-300 print:text-slate-700">
              Tabular iceberg IB-042 (480 m length, NE drift 1.8 kn) remains 18 nm clear of Route B corridor. Trajectory monitoring active.
            </p>
          </section>
        </div>

        {/* 5, 6, 7. Selected Route & Fuel Efficiency */}
        <section className="space-y-2">
          <h3 className="text-sm font-bold text-cyan-300 print:text-slate-900 border-b border-[#1b2b45] print:border-slate-300 pb-1 uppercase">
            5. Selected Route Analysis (Route B - Recommended)
          </h3>
          <div className="p-3 bg-[#09111e] print:bg-slate-100 rounded border border-[#1a2b45] print:border-slate-300 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div>Distance: <strong>{route.distanceNm} nm</strong></div>
            <div>Estimated Fuel: <strong>{route.estimatedFuelMt} MT</strong></div>
            <div>ETA: <strong>{route.etaFormatted}</strong></div>
            <div>Calculated Risk: <strong className="text-cyan-400 print:text-slate-900 font-bold">{route.riskPct}%</strong></div>
          </div>
        </section>

        {/* 8 & 9. Risk Breakdown & Why Route B */}
        <section className="space-y-2">
          <h3 className="text-sm font-bold text-cyan-300 print:text-slate-900 border-b border-[#1b2b45] print:border-slate-300 pb-1 uppercase">
            6. Decision Explainability
          </h3>
          <div className="p-3 bg-[#09111e] print:bg-slate-100 rounded text-xs space-y-1.5">
            <div className="font-bold text-cyan-400 print:text-slate-900">
              Selected Route B - 92% System Confidence Rating
            </div>
            <ul className="list-disc list-inside text-slate-300 print:text-slate-700 space-y-1 text-[11px]">
              <li>Lower iceberg exposure along western Drake Passage corridor (&gt;18 nm radar margin)</li>
              <li>Acceptable sea-ice concentration (&lt;25% average across transit path)</li>
              <li>Optimal safety/fuel trade-off (782 L burn vs 845 L on Route C)</li>
              <li>Within vessel operational threshold (12% calculated risk vs 30% safety limit)</li>
              <li>Lower overall navigation risk index compared to direct Route A</li>
            </ul>
          </div>
        </section>

        {/* 10. Waypoint Breakdown Table */}
        <section className="space-y-2">
          <h3 className="text-sm font-bold text-cyan-300 print:text-slate-900 border-b border-[#1b2b45] print:border-slate-300 pb-1 uppercase">
            7. Waypoint Hydrographic Directory
          </h3>
          <table className="w-full text-left text-xs border-collapse report-table">
            <thead>
              <tr className="border-b border-[#1b2b45] print:border-slate-400 text-slate-400 print:text-slate-700 text-[10px] uppercase font-semibold">
                <th className="py-1">Waypoint</th>
                <th className="py-1">Coords</th>
                <th className="py-1">Ice %</th>
                <th className="py-1">Iceberg Risk</th>
                <th className="py-1">Visibility</th>
                <th className="py-1">Local Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#15233b] print:divide-slate-300">
              {waypoints.map((wp) => (
                <tr key={wp.id}>
                  <td className="py-1.5 font-bold">{wp.name}</td>
                  <td className="py-1.5">{wp.lat.toFixed(2)}°, {wp.lng.toFixed(2)}°</td>
                  <td className="py-1.5">{wp.seaIcePct}%</td>
                  <td className="py-1.5">{wp.icebergRiskPct}%</td>
                  <td className="py-1.5">{wp.visibilityKm} km</td>
                  <td className="py-1.5 font-bold text-cyan-300 print:text-slate-900">{wp.localRiskPct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Report Footer & Disclaimer */}
        <div className="pt-4 border-t border-[#1b2b45] print:border-slate-400 flex flex-wrap items-center justify-between text-[10px] text-slate-400 print:text-slate-600">
          <div>
            System Status: Operational | Data Mode: Demo / Ready for Python Integration
          </div>
          <div>
            Final navigation decisions remain with the vessel operator.
          </div>
        </div>
      </div>
    </div>
  );
}
