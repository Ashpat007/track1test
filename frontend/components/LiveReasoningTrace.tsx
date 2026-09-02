"use client";

import React from "react";

export interface LiveReasoningTraceProps {
  currentStepIndex: number; // 0: Catalog search, 1: Gemini reasoning, 2: Evaluating guardrail cap, 3: Awaiting human gate
}

export default function LiveReasoningTrace({ currentStepIndex }: LiveReasoningTraceProps) {
  const steps = [
    { title: "Catalog search", subtitle: "GET /catalog & GET /agent-spec discovery" },
    { title: "Gemini reasoning", subtitle: "gemini-3.6-flash intent parsing & schema generation" },
    { title: "Evaluating guardrail cap", subtitle: "Deterministic budget & circuit-breaker check" },
    { title: "Awaiting human gate", subtitle: "Awaiting clearance or payment verification" },
  ];

  return (
    <div className="bg-[#11131c] border border-[#1e2230] rounded-xl p-4 my-3 max-w-[540px] shadow-lg space-y-3">
      <div className="flex items-center justify-between border-b border-[#1e2230] pb-2">
        <span className="text-[11px] uppercase font-semibold text-[#00baf2] tracking-wider flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00baf2] animate-ping"></span>
          <span>Live Agent Reasoning Trace</span>
        </span>
        <span className="text-[10px] font-mono text-[#64748b]">
          Step {Math.min(currentStepIndex + 1, steps.length)} of {steps.length}
        </span>
      </div>

      <div className="space-y-2.5">
        {steps.map((step, idx) => {
          const isCompleted = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;
          const isPending = idx > currentStepIndex;

          return (
            <div
              key={step.title}
              className={`flex items-start gap-3 transition-opacity duration-200 ${
                isPending ? "opacity-35 text-[#6b6f85]" : "opacity-100 text-[#f4f4f5]"
              }`}
            >
              {/* Icon container */}
              <div className="mt-0.5 shrink-0">
                {isCompleted && (
                  <div className="w-4 h-4 rounded-full bg-[#10b981]/20 border border-[#10b981] text-[#10b981] flex items-center justify-center text-[10px] font-bold">
                    ✓
                  </div>
                )}
                {isCurrent && (
                  <div className="w-4 h-4 rounded-full border-2 border-[#00baf2] border-t-transparent animate-spin"></div>
                )}
                {isPending && (
                  <div className="w-4 h-4 rounded-full border border-[#2a2e42] flex items-center justify-center text-[8px] text-[#6b6f85]">
                    ○
                  </div>
                )}
              </div>

              {/* Text info */}
              <div className="flex-1 leading-tight">
                <div className={`text-xs font-medium ${isCurrent ? "text-[#00baf2] font-semibold" : ""}`}>
                  {step.title}
                </div>
                <div className="text-[10px] text-[#64748b] mt-0.5 font-mono">
                  {step.subtitle}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
