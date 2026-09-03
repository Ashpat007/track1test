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
  theme: "dark" | "light";
  toggleTheme: () => void;
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
  theme,
  toggleTheme,
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
    <aside className="w-[210px] min-w-[210px] max-w-[210px] h-screen bg-[var(--bg-sidebar)] border-r border-[var(--border-color)] p-4 flex flex-col justify-between select-none fixed left-0 top-0 z-30 transition-colors duration-200">
      {/* Top section */}
      <div>
        {/* Wordmark */}
        <div className="pb-3 border-b border-[var(--border-color)] mb-3.5">
          <h1 className="text-[22px] font-bold text-[var(--text-primary)] tracking-tight leading-tight">
            Boundly
          </h1>
          <p className="text-[11px] text-[var(--text-secondary)] font-normal mt-0.5">
            Bounded agent commerce
          </p>
        </div>

        {/* NAVIGATION Section */}
        <div className="mb-4">
          <div className="text-[10px] uppercase font-semibold text-[var(--text-muted)] tracking-wider mb-2">
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
                      ? "bg-[var(--bg-pill)] text-[var(--text-primary)] font-medium shadow-[var(--card-shadow)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-pill-hover)] bg-transparent"
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
          <div className="text-[10px] uppercase font-semibold text-[var(--text-muted)] tracking-wider mb-2">
            SECURITY
          </div>
          <div className="flex flex-col gap-2">
            {/* Spending Cap */}
            {isEditingCap ? (
              <form onSubmit={handleCapSubmit} className="flex items-center gap-1">
                <span className="text-xs text-[var(--text-secondary)]">Cap ₹</span>
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
                  className="w-16 bg-[var(--bg-card-subtle)] border border-[var(--border-subtle)] rounded px-1 py-0.5 text-xs text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </form>
            ) : (
              <div
                onClick={() => {
                  setCapInputValue(spendingCap.toString());
                  setIsEditingCap(true);
                }}
                className="text-xs text-[var(--text-primary)] font-medium cursor-pointer hover:text-blue-500 transition flex items-center justify-between"
                title="Click to edit spending cap"
              >
                <span>Cap ₹{spendingCap.toFixed(2)}</span>
                <span className="text-[10px] text-[var(--text-secondary)]">✎</span>
              </div>
            )}

            {/* Gating Mode */}
            <div
              onClick={toggleGating}
              className="text-xs text-[var(--text-secondary)] cursor-pointer hover:text-[var(--text-primary)] transition flex items-center justify-between"
              title="Click to switch between Human Review Gate and Auto Approve"
            >
              <span>{gatingMode}</span>
              <span className="text-[10px] text-[var(--text-secondary)]">⟳</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Pinned Status & Actions Section */}
      <div className="pt-3 flex flex-col gap-2.5 border-t border-[var(--border-color)]">
        {/* 1. Theme Toggle Button (Compact sun/moon icon toggle above kill switch) */}
        <button
          onClick={toggleTheme}
          className="w-full text-left text-[11px] px-2.5 py-1.5 rounded-md border transition-all flex items-center justify-between bg-[var(--bg-card)] border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-subtle)] shadow-[var(--card-shadow)]"
          title={`Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`}
        >
          <span className="flex items-center gap-1.5 font-medium">
            <span className="text-xs">{theme === "dark" ? "🌙" : "☀️"}</span>
            <span>{theme === "dark" ? "Dark Theme" : "Light Theme"}</span>
          </span>
          <span className="text-[10px] font-mono opacity-70">
            {theme === "dark" ? "Dark" : "Light"}
          </span>
        </button>

        {/* 2. Kill switch pill (Variant A: OFF = subtle red pill, ACTIVE = solid #E24B4A + glow ring) */}
        <button
          onClick={toggleSystemHalt}
          className={`w-full text-left text-[11px] px-2.5 py-1.5 rounded-md transition-all flex items-center justify-between ${
            isSystemHalted
              ? "bg-[#E24B4A] border border-[#E24B4A] text-white font-bold shadow-[0_0_0_3px_rgba(226,75,74,0.25)]"
              : "bg-[rgba(226,75,74,0.08)] border border-[rgba(226,75,74,0.25)] text-[#e24b4a] hover:bg-[rgba(226,75,74,0.15)]"
          }`}
          title="Toggle Emergency System Kill Switch"
        >
          <span className="flex items-center gap-1.5">
            <span>🚨</span>
            <span className={isSystemHalted ? "font-bold text-white" : ""}>
              {isSystemHalted ? "Kill switch: on" : "Kill switch: off"}
            </span>
          </span>
          <span
            className={`text-[10px] tracking-wider ${
              isSystemHalted
                ? "bg-white text-[#E24B4A] px-1.5 py-0.2 rounded font-black text-[9px]"
                : "opacity-75 font-semibold"
            }`}
          >
            {isSystemHalted ? "FROZEN" : "OFF"}
          </span>
        </button>

        {/* 3. API online status badge */}
        <div className="font-mono text-[10px] text-[#0f8a5f] dark:text-[#5dcaa5] flex items-center gap-1.5 px-0.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#0f8a5f] dark:bg-[#5dcaa5] animate-pulse"></span>
          <span>online :8000</span>
        </div>
      </div>
    </aside>
  );
}
