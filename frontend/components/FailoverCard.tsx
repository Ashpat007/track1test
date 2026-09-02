"use client";

import React from "react";

interface FailoverCardProps {
  storeAProduct?: string;
  storeBProduct?: string;
  amount?: number;
}

export default function FailoverCard({
  storeAProduct = "Kashmiri Kahwa",
  storeBProduct = "Kahwa (Botanical Blend)",
  amount = 360,
}: FailoverCardProps) {
  return (
    <div className="bg-[#0b0c16] border border-[#1b1e2e] rounded-2xl p-5 my-4 space-y-4 shadow-2xl">
      {/* Header Row */}
      <div className="flex items-center gap-2.5">
        <div className="w-5 h-5 rounded bg-blue-600/30 border border-blue-500/40 text-blue-400 flex items-center justify-center text-xs font-bold shrink-0">
          🔄
        </div>
        <span className="text-[#3b82f6] font-bold text-xs tracking-wider uppercase">
          FEDERATED FAILOVER TRIGGERED
        </span>
      </div>

      {/* Two side-by-side panels connected by an arrow */}
      <div className="grid grid-cols-1 sm:grid-cols-[1fr,auto,1fr] items-center gap-4">
        {/* Left: Store A (Depleted) */}
        <div className="bg-[#181115] border border-red-900/30 rounded-xl p-4 flex flex-col justify-between space-y-2">
          <div className="text-[10px] font-semibold text-rose-400/80 uppercase tracking-wider">
            STORE A · AURA ARTISAN TEAS
          </div>
          <div className="text-sm font-bold text-white leading-tight">
            {storeAProduct}
          </div>
          <div className="text-xs text-rose-400 font-medium flex items-center gap-1">
            <span>✕</span>
            <span>0 units — out of stock</span>
          </div>
        </div>

        {/* Center connector arrow */}
        <div className="flex justify-center text-[#60a5fa] text-lg font-bold select-none py-1 sm:py-0">
          ➔
        </div>

        {/* Right: Store B (In Stock Failover) */}
        <div className="bg-[#0b1c18] border border-emerald-500/40 rounded-xl p-4 flex flex-col justify-between space-y-2">
          <div className="text-[10px] font-semibold text-emerald-400/90 uppercase tracking-wider">
            STORE B · BOTANICAL LEAF CO.
          </div>
          <div className="text-sm font-bold text-white leading-tight">
            {storeBProduct}
          </div>
          <div className="text-xs text-emerald-400 font-medium flex items-center gap-1 font-mono">
            <span>✓</span>
            <span>15 units in stock — ₹{amount.toFixed(0)}</span>
          </div>
        </div>
      </div>

      {/* Bottom Explanatory Caption */}
      <p className="text-xs text-[#64748b] leading-relaxed">
        Agent automatically discovered an in-stock match at a federated partner store and re-routed checkout — no user intervention required.
      </p>
    </div>
  );
}
