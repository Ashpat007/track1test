import React from "react";

export default function MetaStrip() {
  return (
    <div className="bg-[#0f172a]/60 border border-[#1e2230] px-4 py-2 rounded-lg text-xs text-[#94a3b8] font-mono mb-5 flex items-center gap-3 w-fit">
      <span>INR</span>
      <span className="text-[#334155]">·</span>
      <span>15 min reservation</span>
      <span className="text-[#334155]">·</span>
      <span className="text-[#10b981] font-medium">Guardrails active</span>
    </div>
  );
}
