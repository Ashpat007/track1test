"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import AgentStudio from "@/components/sections/AgentStudio";
import CatalogAPI from "@/components/sections/CatalogAPI";
import AuditTrail from "@/components/sections/AuditTrail";
import Docs from "@/components/sections/Docs";
import { fetchSystemStatus, haltSystem, resumeSystem } from "@/lib/api";

export default function Home() {
  const [activeNav, setActiveNav] = useState("Agent Studio");
  const [spendingCap, setSpendingCap] = useState(500.0);
  const [gatingMode, setGatingMode] = useState("Human Review Gate");
  const [isSystemHalted, setIsSystemHalted] = useState(false);

  useEffect(() => {
    async function checkStatus() {
      try {
        const s = await fetchSystemStatus();
        setIsSystemHalted(s.system_halted);
      } catch (e) {
        console.error("Failed to check status:", e);
      }
    }
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleSystemHalt = async () => {
    try {
      if (isSystemHalted) {
        await resumeSystem();
        setIsSystemHalted(false);
      } else {
        await haltSystem();
        setIsSystemHalted(true);
      }
    } catch (e) {
      console.error("Failed to toggle kill switch:", e);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#090a0f]">
      {/* Sidebar Component matching reference image exactly */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        spendingCap={spendingCap}
        setSpendingCap={setSpendingCap}
        gatingMode={gatingMode}
        setGatingMode={setGatingMode}
        isSystemHalted={isSystemHalted}
        toggleSystemHalt={toggleSystemHalt}
      />

      {/* Main Content Area */}
      <main className="flex-1 ml-[210px] p-6 min-h-screen overflow-y-auto">
        {activeNav === "Agent Studio" && (
          <AgentStudio
            spendingCap={spendingCap}
            setSpendingCap={setSpendingCap}
            gatingMode={gatingMode}
            isSystemHalted={isSystemHalted}
          />
        )}
        {activeNav === "Catalog API" && <CatalogAPI />}
        {activeNav === "Audit Trail" && <AuditTrail />}
        {activeNav === "Docs" && <Docs />}
      </main>
    </div>
  );
}
