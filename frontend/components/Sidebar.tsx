"use client";

import React, { useState } from "react";

interface SidebarProps {
  activeNav: string;
  setActiveNav: (nav: string) => void;
  spendingCap: number;
  setSpendingCap: (cap: number) => void;
  gatingMode: string;
  setGatingMode: (mode: string) => void;
  isSystemHalted: boolean;
  toggleSystemHalt: () => void;
}

export default function Sidebar({
  activeNav,
  setActiveNav,
  spendingCap,
  setSpendingCap,
  gatingMode,
  setGatingMode,
  isSystemHalted,
  toggleSystemHalt,
}: SidebarProps) {
  const [isEditingCap, setIsEditingCap] = useState(false);
  const [capInputValue, setCapInputValue] = useState(spendingCap.toString());

  const navItems = ["Catalog API", "Agent Studio", "Audit Trail", "Docs"];

  const handleCapSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(capInputValue);
    if (!isNaN(val) && val > 0) {
      setSpendingCap(val);
    }
    setIsEditingCap(false);
  };

  const toggleGating = () => {
    setGatingMode(gatingMode === "Human Review Gate" ? "Auto Approve" : "Human Review Gate");
  };

  return (
    <aside className="w-[210px] min-w-[210px] max-w-[210px] h-screen bg-[#0c0c14] border-r border-[#1e2230] p-4 flex flex-col justify-between select-none fixed left-0 top-0 z-30">
      {/* Top section */}
      <div>
        {/* Wordmark */}
        <div className="pb-3 border-b border-[#1e2230] mb-3.5">
          <h1 className="text-[22px] font-bold text-white tracking-tight leading-tight">
            Boundly
          </h1>
          <p className="text-[11px] text-[#6b6f85] font-normal mt-0.5">
            Bounded agent commerce
          </p>
        </div>

        {/* NAVIGATION Section */}
        <div className="mb-4">
          <div className="text-[10px] uppercase font-semibold text-[#6b6f85] tracking-wider mb-2">
            NAVIGATION
          </div>
          <div className="flex flex-col gap-1">
            {navItems.map((item) => {
              const isActive = activeNav === item;
              return (
                <button
                  key={item}
                  onClick={() => setActiveNav(item)}
                  className={`text-left text-xs px-2.5 py-1.5 rounded-md transition-colors ${
                    isActive
                      ? "bg-[#1c1c2e] text-white font-medium"
                      : "text-[#6b6f85] hover:text-[#d4d4d8] hover:bg-[#151522] bg-transparent"
                  }`}
                >
                  {item}
                </button>
              );
            })}
          </div>
        </div>

        {/* SECURITY Section */}
        <div className="mb-4">
          <div className="text-[10px] uppercase font-semibold text-[#6b6f85] tracking-wider mb-2">
            SECURITY
          </div>
          <div className="flex flex-col gap-2">
            {/* Spending Cap */}
            {isEditingCap ? (
              <form onSubmit={handleCapSubmit} className="flex items-center gap-1">
                <span className="text-xs text-[#a1a1aa]">Cap ₹</span>
                <input
                  type="number"
                  value={capInputValue}
                  onChange={(e) => setCapInputValue(e.target.value)}
                  onBlur={() => {
                    const val = parseFloat(capInputValue);
                    if (!isNaN(val) && val > 0) setSpendingCap(val);
                    setIsEditingCap(false);
                  }}
                  autoFocus
                  className="w-16 bg-[#181a26] border border-[#2a2e42] rounded px-1 py-0.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </form>
            ) : (
              <div
                onClick={() => {
                  setCapInputValue(spendingCap.toString());
                  setIsEditingCap(true);
                }}
                className="text-xs text-white font-medium cursor-pointer hover:text-blue-400 transition flex items-center justify-between"
                title="Click to edit spending cap"
              >
                <span>Cap ₹{spendingCap.toFixed(2)}</span>
                <span className="text-[10px] text-[#6b6f85]">✎</span>
              </div>
            )}

            {/* Gating Mode */}
            <div
              onClick={toggleGating}
              className="text-xs text-[#d4d4d8] cursor-pointer hover:text-white transition flex items-center justify-between"
              title="Click to switch between Human Review Gate and Auto Approve"
            >
              <span>{gatingMode}</span>
              <span className="text-[10px] text-[#6b6f85]">⟳</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Pinned Status Section */}
      <div className="pt-3 flex flex-col gap-2 border-t border-[#1e2230]/50">
        {/* Kill switch pill */}
        <button
          onClick={toggleSystemHalt}
          className={`w-full text-left text-[11px] px-2.5 py-1.5 rounded-md border transition-all flex items-center justify-between ${
            isSystemHalted
              ? "bg-[rgba(239,68,68,0.2)] border-[rgba(239,68,68,0.5)] text-[#f87171]"
              : "bg-[rgba(226,75,74,0.1)] border-[rgba(226,75,74,0.3)] text-[#f09595] hover:bg-[rgba(226,75,74,0.18)]"
          }`}
          title="Toggle Emergency System Kill Switch"
        >
          <span>{isSystemHalted ? "🚨 Kill switch: on" : "🚨 Kill switch: off"}</span>
          <span className="text-[10px] opacity-75">{isSystemHalted ? "FROZEN" : "OFF"}</span>
        </button>

        {/* API online status badge */}
        <div className="font-mono text-[10px] text-[#5dcaa5] flex items-center gap-1.5 px-0.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#5dcaa5] animate-pulse"></span>
          <span>online :8000</span>
        </div>
      </div>
    </aside>
  );
}
