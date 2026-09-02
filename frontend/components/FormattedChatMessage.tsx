"use client";

import React from "react";

interface FormattedChatMessageProps {
  content: string;
  role: "user" | "assistant";
}

export default function FormattedChatMessage({ content, role }: FormattedChatMessageProps) {
  if (role === "user") {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  // Check if content starts with Agent LLM Reasoning header
  let rawText = content;
  let hasReasoningHeader = false;

  if (rawText.includes("Agent LLM Reasoning")) {
    hasReasoningHeader = true;
    rawText = rawText.replace(/🧠\s*\*\*Agent LLM Reasoning\*\*:\s*/g, "").replace(/🧠\s*Agent LLM Reasoning:\s*/g, "");
  }

  // Parse markdown bold (**text**) and price formatting (₹XXX)
  const parseMarkdown = (text: string) => {
    // Split by ** for bold
    const parts = text.split(/(\*\*[^*]+\*\*)/g);

    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        const boldText = part.slice(2, -2);
        return (
          <strong key={index} className="font-semibold text-white">
            {boldText}
          </strong>
        );
      }

      // Format currency occurrences (e.g. ₹650.0 or ₹480.00)
      const currencyParts = part.split(/(₹\d+(?:\.\d+)?)/g);

      return (
        <React.Fragment key={index}>
          {currencyParts.map((cPart, cIndex) => {
            if (cPart.startsWith("₹")) {
              const numStr = cPart.slice(1);
              const val = parseFloat(numStr);
              const formattedPrice = isNaN(val) ? cPart : `₹${val.toFixed(2)}`;
              return (
                <span
                  key={cIndex}
                  className="font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-1.5 py-0.5 rounded text-xs font-semibold inline-block mx-0.5"
                >
                  {formattedPrice}
                </span>
              );
            }
            return cPart;
          })}
        </React.Fragment>
      );
    });
  };

  const lines = rawText.split("\n");

  return (
    <div className="space-y-2">
      {hasReasoningHeader && (
        <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-[#00baf2] bg-[#00baf2]/10 border border-[#00baf2]/30 px-2.5 py-1 rounded-md mb-1 shadow-sm">
          <span>🧠</span>
          <span className="uppercase tracking-wider">Agent LLM Reasoning</span>
        </div>
      )}

      <div className="text-sm leading-relaxed text-[#d4d4d8] space-y-1.5">
        {lines.map((line, lIdx) => (
          <div key={lIdx}>
            {line.trim().startsWith("•") || line.trim().startsWith("-") ? (
              <div className="flex items-start gap-2 pl-2 my-1">
                <span className="text-[#00baf2] mt-1 text-xs">•</span>
                <div>{parseMarkdown(line.replace(/^[•\-]\s*/, ""))}</div>
              </div>
            ) : (
              <div>{parseMarkdown(line)}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
