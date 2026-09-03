import React from "react";

interface ReceiptCardProps {
  orderId: string;
}

export default function ReceiptCard({ orderId }: ReceiptCardProps) {
  return (
    <div className="bg-[var(--success-bg)] border border-[var(--success-border)] rounded-xl px-4 py-3 my-2.5 flex items-center gap-3 animate-success-fade shadow-[var(--card-shadow)] transition-colors">
      <div className="w-5 h-5 rounded-full bg-[var(--success-text)] text-white flex items-center justify-center font-bold text-xs">
        ✓
      </div>
      <div className="text-sm font-medium text-[var(--success-text)]">
        Payment confirmed · <code className="font-mono text-[var(--success-text)] font-semibold">{orderId}</code>
      </div>
    </div>
  );
}
