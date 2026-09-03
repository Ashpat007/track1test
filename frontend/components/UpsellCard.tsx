"use client";

import React from "react";

interface UpsellCardProps {
  upsellData: {
    budget_breached?: boolean;
    breached_product_id?: string;
    breached_product_name?: string;
    breached_product_price_inr?: number;
    alternative_product_name?: string;
    alternative_product_price_inr?: number;
    suggested_cap_increase_inr?: number;
    recommendation_reasoning?: string;
  };
  spendingCap: number;
  onSelectOption: (option: "A" | "B" | "C") => void;
  isLoading?: boolean;
}

export default function UpsellCard({
  upsellData,
  spendingCap,
  onSelectOption,
  isLoading = false,
}: UpsellCardProps) {
  const breachedName = upsellData.breached_product_name || "Matcha Grade-A";
  const altName = upsellData.alternative_product_name || "Pashmina Kashmiri Kahwa";
  const altPrice = upsellData.alternative_product_price_inr || 360;
  const newCap = upsellData.suggested_cap_increase_inr || 1050;

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--amber-border)] rounded-2xl p-5 my-4 space-y-4 shadow-[var(--card-shadow)] transition-colors">
      {/* Top Header Row with Amber Accent Token */}
      <div className="flex items-center gap-2 text-[var(--amber-text)] font-semibold text-xs tracking-wide uppercase">
        <span className="text-base leading-none">🛍️</span>
        <span>{breachedName.toUpperCase()} EXCEEDS ₹{spendingCap.toFixed(0)} CAP — AGENT SUGGESTS</span>
      </div>

      {/* Explanation text */}
      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
        {upsellData.recommendation_reasoning ||
          `The requested item exceeds your current ₹${spendingCap.toFixed(0)} single-action cap. Here is the agent's recommended in-budget alternative:`}
      </p>

      {/* PROMINENT HERO CARD: Recommended in-budget alternative pulled forward */}
      <div className="bg-[var(--amber-bg)] border border-[var(--amber-border)] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-block bg-[var(--amber-border)] text-[var(--amber-text)] text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider mb-1">
            Recommended in-budget swap
          </div>
          <div className="text-sm font-semibold text-[var(--text-primary)]">{altName}</div>
          <div className="text-xs text-[var(--amber-text)] font-medium font-mono">
            ₹{altPrice.toFixed(2)}{" "}
            <span className="text-[var(--text-muted)] font-normal">(under your ₹{spendingCap.toFixed(0)} cap)</span>
          </div>
        </div>

        <button
          onClick={() => onSelectOption("A")}
          disabled={isLoading}
          className="bg-amber-500 hover:bg-amber-400 text-black font-semibold text-xs px-5 py-2.5 rounded-lg transition shadow-md whitespace-nowrap text-center disabled:opacity-50"
        >
          {isLoading ? "Executing..." : `Buy this (₹${altPrice.toFixed(0)})`}
        </button>
      </div>

      {/* SECONDARY LOWER-EMPHASIS OPTIONS */}
      <div className="pt-2 border-t border-[var(--border-color)] flex flex-col sm:flex-row items-stretch sm:items-center gap-2 text-xs">
        <button
          onClick={() => onSelectOption("B")}
          disabled={isLoading}
          className="flex-1 bg-[var(--bg-pill)] hover:bg-[var(--bg-pill-hover)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] px-3 py-2 rounded-lg transition text-left sm:text-center text-[11px] disabled:opacity-50 flex items-center justify-between sm:justify-center gap-2"
        >
          <span>Upgrade cap to ₹{newCap.toFixed(0)} & buy {breachedName}</span>
          <span className="text-[var(--success-text)] font-mono text-[10px]">↗</span>
        </button>

        <button
          onClick={() => onSelectOption("C")}
          disabled={isLoading}
          className="bg-[var(--danger-bg)] hover:opacity-80 border border-[var(--danger-border)] text-[var(--danger-text)] px-3 py-2 rounded-lg transition text-center text-[11px] disabled:opacity-50 whitespace-nowrap font-medium"
        >
          Decline / Abort
        </button>
      </div>
    </div>
  );
}
