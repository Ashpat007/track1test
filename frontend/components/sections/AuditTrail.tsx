"use client";

import React, { useState, useEffect } from "react";
import { fetchAuditLogs, clearAuditLogs, AuditLogRecord } from "@/lib/api";

export default function AuditTrail() {
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const records = await fetchAuditLogs();
      setLogs(records);
    } catch (e) {
      console.error("Failed to load audit logs:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const handleClear = async () => {
    if (confirm("Clear all audit log records from SQLite?")) {
      await clearAuditLogs();
      loadLogs();
    }
  };

  return (
    <div className="space-y-4 max-w-[1200px]">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">
            Durable SQL Audit Log Inspector
          </h2>
          <p className="text-xs text-[#64748b]">
            Full chronological traceability of autonomous buyer agent decisions and Razorpay transactions.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadLogs}
            className="text-xs bg-[#1c1c2e] hover:bg-[#25253e] text-white px-3 py-1.5 rounded-md border border-[#2a2e42] transition"
          >
            Refresh
          </button>
          <button
            onClick={handleClear}
            className="text-xs bg-red-500/15 hover:bg-red-500/25 border border-red-500/30 text-red-400 px-3 py-1.5 rounded-md transition"
          >
            Reset Database Log
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-xs text-[#64748b] py-8">Loading audit trail...</div>
      ) : logs.length === 0 ? (
        <div className="bg-[#11131c] border border-[#1e2230] rounded-xl p-8 text-center text-xs text-[#64748b]">
          No audit log records found in SQLite database yet.
        </div>
      ) : (
        <div className="border border-[#1e2230] rounded-xl overflow-hidden bg-[#11131c]/70">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#1e2230] bg-[#0c0c14] text-[#6b6f85]">
                <th className="p-3 font-semibold">ID</th>
                <th className="p-3 font-semibold">Timestamp</th>
                <th className="p-3 font-semibold">Step Type</th>
                <th className="p-3 font-semibold">Proposed Action</th>
                <th className="p-3 font-semibold">Amount</th>
                <th className="p-3 font-semibold">Guardrails</th>
                <th className="p-3 font-semibold">Gating</th>
                <th className="p-3 font-semibold">Razorpay Order</th>
                <th className="p-3 font-semibold">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2230]">
              {logs.map((r) => (
                <tr key={r.id} className="hover:bg-[#161926] transition">
                  <td className="p-3 font-mono text-[#64748b]">{r.id}</td>
                  <td className="p-3 font-mono text-[#94a3b8]">{r.timestamp?.split(" ")[1] || r.timestamp}</td>
                  <td className="p-3 font-mono text-blue-400">{r.step_type}</td>
                  <td className="p-3 text-white max-w-[240px] truncate" title={r.proposed_action}>
                    {r.proposed_action}
                  </td>
                  <td className="p-3 font-semibold text-[#10b981]">
                    {r.proposed_amount_inr ? `₹${r.proposed_amount_inr.toFixed(2)}` : "N/A"}
                  </td>
                  <td className="p-3">
                    {r.guardrail_passed ? (
                      <span className="text-emerald-400 font-medium">✅ PASS</span>
                    ) : (
                      <span className="text-red-400 font-medium">❌ BLOCKED</span>
                    )}
                  </td>
                  <td className="p-3 text-[#d4d4d8]">{r.gate_status}</td>
                  <td className="p-3 font-mono text-[#00baf2] text-[11px]">
                    {r.razorpay_order_id || "N/A"}
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                        r.outcome_status.includes("SUCCESS") || r.outcome_status.includes("COMPLETED")
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/25"
                          : r.outcome_status.includes("DENIED") || r.outcome_status.includes("BLOCKED")
                          ? "bg-red-500/10 text-red-400 border border-red-500/25"
                          : "bg-blue-500/10 text-blue-400 border border-blue-500/25"
                      }`}
                    >
                      {r.outcome_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
