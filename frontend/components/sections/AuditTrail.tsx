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
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">
            Durable SQL Audit Log Inspector
          </h2>
          <p className="text-xs text-[var(--text-secondary)]">
            Full chronological traceability of autonomous buyer agent decisions and Razorpay transactions.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadLogs}
            className="text-xs bg-[var(--bg-card)] hover:bg-[var(--bg-pill)] text-[var(--text-primary)] px-3 py-1.5 rounded-md border border-[var(--border-color)] transition shadow-[var(--card-shadow)]"
          >
            Refresh
          </button>
          <button
            onClick={handleClear}
            className="text-xs bg-[var(--danger-bg)] hover:opacity-80 border border-[var(--danger-border)] text-[var(--danger-text)] px-3 py-1.5 rounded-md transition shadow-[var(--card-shadow)] font-medium"
          >
            Reset Database Log
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-xs text-[var(--text-secondary)] py-8">Loading audit trail...</div>
      ) : logs.length === 0 ? (
        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl p-8 text-center text-xs text-[var(--text-secondary)] shadow-[var(--card-shadow)]">
          No audit log records found in SQLite database yet.
        </div>
      ) : (
        <div className="border border-[var(--border-color)] rounded-xl overflow-hidden bg-[var(--bg-card)] shadow-[var(--card-shadow)]">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[var(--border-color)] bg-[var(--table-header-bg)] text-[var(--text-muted)]">
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
            <tbody className="divide-y divide-[var(--border-color)]">
              {logs.map((r) => (
                <tr key={r.id} className="hover:bg-[var(--table-row-hover)] transition">
                  <td className="p-3 font-mono text-[var(--text-muted)]">{r.id}</td>
                  <td className="p-3 font-mono text-[var(--text-secondary)]">{r.timestamp?.split(" ")[1] || r.timestamp}</td>
                  <td className="p-3 font-mono text-blue-500 font-medium">{r.step_type}</td>
                  <td className="p-3 text-[var(--text-primary)] max-w-[240px] truncate" title={r.proposed_action}>
                    {r.proposed_action}
                  </td>
                  <td className="p-3 font-semibold text-[var(--success-text)]">
                    {r.proposed_amount_inr ? `₹${r.proposed_amount_inr.toFixed(2)}` : "N/A"}
                  </td>
                  <td className="p-3">
                    {r.guardrail_passed ? (
                      <span className="text-[var(--success-text)] font-semibold">✅ PASS</span>
                    ) : (
                      <span className="text-[var(--danger-text)] font-semibold">❌ BLOCKED</span>
                    )}
                  </td>
                  <td className="p-3 text-[var(--text-secondary)]">{r.gate_status}</td>
                  <td className="p-3 font-mono text-[#00baf2] text-[11px]">
                    {r.razorpay_order_id || "N/A"}
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                        r.outcome_status.includes("SUCCESS") || r.outcome_status.includes("COMPLETED")
                          ? "bg-[var(--success-bg)] text-[var(--success-text)] border border-[var(--success-border)]"
                          : r.outcome_status.includes("DENIED") || r.outcome_status.includes("BLOCKED")
                          ? "bg-[var(--danger-bg)] text-[var(--danger-text)] border border-[var(--danger-border)]"
                          : "bg-blue-500/10 text-blue-500 border border-blue-500/25"
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
