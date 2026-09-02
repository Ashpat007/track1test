import React from "react";

interface ReceiptCardProps {
  orderId: string;
}

export default function ReceiptCard({ orderId }: ReceiptCardProps) {
  return (
    <div className="bg-[#10b981]/10 border border-[#10b981]/30 rounded-xl px-4 py-3 my-2.5 flex items-center gap-3 animate-success-fade">
      <div className="w-5 h-5 rounded-full bg-[#10b981] text-[#090a0f] flex items-center justify-center font-bold text-xs">
        ✓
      </div>
      <div className="text-sm font-medium text-[#34d399]">
        Payment confirmed · <code className="font-mono text-[#34d399] font-normal">{orderId}</code>
      </div>
    </div>
  );
}
