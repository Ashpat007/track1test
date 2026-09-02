"use client";

import React from "react";

export interface GatingItemDetail {
  product_name: string;
  unit_price_inr: number;
  quantity: number;
  subtotal_inr: number;
}

interface GatingCardProps {
  summaryNames: string;
  totalAmount: number;
  spendingCap: number;
  itemsDetail?: GatingItemDetail[];
  reasoning?: string;
  onApprove: () => void;
  onDeny: () => void;
  isLoading?: boolean;
}

export default function GatingCard({
  summaryNames,
  totalAmount,
  spendingCap,
  itemsDetail,
  reasoning,
  onApprove,
  onDeny,
  isLoading = false,
}: GatingCardProps) {
  const hasMultipleItems = itemsDetail && itemsDetail.length > 1;

  return (
    <div className="bg-[#0000D6] border border-[#1a1aff] rounded-2xl p-6 shadow-2xl text-white my-4 transition-all">
      <div className="text-xs font-normal text-white/80 mb-3">
        {hasMultipleItems ? "Gating checkpoint · bundle" : "Gating checkpoint"}
      </div>

      {hasMultipleItems ? (
        <div className="space-y-2 mb-4">
          {itemsDetail.map((item, idx) => (
            <div key={idx} className="flex justify-between items-center text-sm font-semibold text-white">
              <span>{item.quantity}x {item.product_name}</span>
              <span className="font-mono font-semibold">₹{item.subtotal_inr.toFixed(2)}</span>
            </div>
          ))}
          <div className="border-t border-white/20 pt-3 flex justify-between items-center text-sm font-medium text-white">
            <span>Total</span>
            <span className="font-mono font-semibold">
              ₹{totalAmount.toLocaleString("en-IN", { minimumFractionDigits: 2 })} within ₹{spendingCap.toLocaleString("en-IN")} cap
            </span>
          </div>
        </div>
      ) : (
        <div className="text-xl font-bold text-white mb-4">
          {summaryNames} — ₹{totalAmount.toFixed(0)} within ₹{spendingCap.toFixed(0)} cap
        </div>
      )}

      {/* AGENT RATIONALE & REASONING CALLOUT BOX */}
      {reasoning && (
        <div className="bg-white/10 border border-white/25 rounded-xl p-3.5 mb-5 text-xs leading-relaxed text-white/95 flex items-start gap-2.5 shadow-inner">
          <span className="text-base leading-none">🧠</span>
          <div>
            <span className="font-bold text-white uppercase tracking-wider text-[10px] block mb-0.5 text-blue-200">
              Agent Decision Rationale:
            </span>
            <span>{reasoning}</span>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={onApprove}
          disabled={isLoading}
          className="flex-1 bg-white text-[#0000D6] font-semibold text-sm py-2.5 px-6 rounded-lg hover:bg-slate-100 transition shadow-md disabled:opacity-50 text-center"
        >
          {isLoading ? "Executing..." : "Approve"}
        </button>
        <button
          onClick={onDeny}
          disabled={isLoading}
          className="flex-1 bg-transparent border border-white/40 text-white font-medium text-sm py-2.5 px-6 rounded-lg hover:bg-red-500/20 hover:border-red-500 transition text-center disabled:opacity-50"
        >
          Deny
        </button>
      </div>
    </div>
  );
}
