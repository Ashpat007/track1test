import React from "react";

export default function MetaStrip() {
  return (
    <div className="bg-[var(--meta-bg)] border border-[var(--meta-border)] px-4 py-2 rounded-lg text-xs text-[var(--meta-text)] font-mono mb-2 flex items-center gap-3 w-fit shadow-[var(--card-shadow)] transition-colors">
      <span>INR</span>
      <span className="opacity-40">·</span>
      <span>15 min reservation</span>
      <span className="opacity-40">·</span>
      <span className="text-[var(--success-text)] font-medium">Guardrails active</span>
    </div>
  );
}
