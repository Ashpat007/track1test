import os

base = "frontend/components"
os.makedirs(base, exist_ok=True)

# 1. UpsellCard.tsx
with open(os.path.join(base, "UpsellCard.tsx"), "w", encoding="utf-8") as f:
    f.write('''"use client";

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
    <div className="bg-[#11131c] border border-amber-500/30 rounded-2xl p-5 my-4 space-y-4 shadow-xl">
      {/* Top Header Row with Amber Accent Token */}
      <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs tracking-wide uppercase">
        <span className="text-base leading-none">🛍️</span>
        <span>{breachedName.toUpperCase()} EXCEEDS ₹{spendingCap.toFixed(0)} CAP — AGENT SUGGESTS</span>
      </div>

      {/* Explanation text */}
      <p className="text-xs text-[#d4d4d8] leading-relaxed">
        {upsellData.recommendation_reasoning ||
          `The requested item exceeds your current ₹${spendingCap.toFixed(0)} single-action cap. Here is the agent's recommended in-budget alternative:`}
      </p>

      {/* PROMINENT HERO CARD: Recommended in-budget alternative pulled forward */}
      <div className="bg-amber-500/10 border border-amber-500/40 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-block bg-amber-500/20 border border-amber-500/30 text-amber-300 text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider mb-1">
            Recommended in-budget swap
          </div>
          <div className="text-sm font-semibold text-white">{altName}</div>
          <div className="text-xs text-amber-400 font-medium font-mono">
            ₹{altPrice.toFixed(2)}{" "}
            <span className="text-[#a1a1aa] font-normal">(under your ₹{spendingCap.toFixed(0)} cap)</span>
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
      <div className="pt-2 border-t border-[#1e2230] flex flex-col sm:flex-row items-stretch sm:items-center gap-2 text-xs">
        <button
          onClick={() => onSelectOption("B")}
          disabled={isLoading}
          className="flex-1 bg-transparent hover:bg-[#1c1c2e] border border-[#2a2e42] hover:border-[#3b3f58] text-[#a1a1aa] hover:text-white px-3 py-2 rounded-lg transition text-left sm:text-center text-[11px] disabled:opacity-50 flex items-center justify-between sm:justify-center gap-2"
        >
          <span>Upgrade cap to ₹{newCap.toFixed(0)} & buy {breachedName}</span>
          <span className="text-emerald-400 font-mono text-[10px]">↗</span>
        </button>

        <button
          onClick={() => onSelectOption("C")}
          disabled={isLoading}
          className="bg-transparent hover:bg-red-500/10 border border-[#2a2e42] hover:border-red-500/30 text-[#a1a1aa] hover:text-red-400 px-3 py-2 rounded-lg transition text-center text-[11px] disabled:opacity-50 whitespace-nowrap"
        >
          Decline / Abort
        </button>
      </div>
    </div>
  );
}
''')

# 2. FailoverCard.tsx
with open(os.path.join(base, "FailoverCard.tsx"), "w", encoding="utf-8") as f:
    f.write('''"use client";

import React from "react";

interface FailoverCardProps {
  storeAProduct?: string;
  storeBProduct?: string;
  amount?: number;
}

export default function FailoverCard({
  storeAProduct = "Kashmir Kahwa Saffron Blend",
  storeBProduct = "Pashmina Kashmiri Kahwa (Whole Spices)",
  amount = 360,
}: FailoverCardProps) {
  return (
    <div className="bg-[#0f172a]/90 border border-[#00baf2]/40 rounded-xl p-4 my-3 text-xs space-y-3 shadow-lg">
      {/* Header Row */}
      <div className="flex items-center gap-2 text-[#00baf2] font-semibold text-xs tracking-wide uppercase">
        <span className="text-base leading-none">🌐</span>
        <span>FEDERATED CROSS-STORE FAILOVER TRIGGERED</span>
      </div>

      {/* Two side-by-side panels connected by an arrow */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr] items-center gap-3">
        {/* Left: Store A (Depleted / Out of Stock) */}
        <div className="bg-red-500/10 border border-red-500/30 p-3 rounded-lg flex flex-col justify-between h-full">
          <div className="text-red-400 font-semibold text-[10px] uppercase tracking-wider">
            Store A (Aura Artisan Teas)
          </div>
          <div className="text-white font-medium text-xs my-1">{storeAProduct}</div>
          <div className="text-red-400 text-[11px] font-medium flex items-center gap-1">
            <span>✕</span>
            <span>0 units — out of stock</span>
          </div>
        </div>

        {/* Center connector arrow */}
        <div className="flex justify-center text-center text-[#64748b] text-base font-bold select-none py-1 md:py-0">
          ➔
        </div>

        {/* Right: Store B (In Stock Partner Failover) */}
        <div className="bg-emerald-500/10 border border-emerald-500/30 p-3 rounded-lg flex flex-col justify-between h-full">
          <div className="text-emerald-400 font-semibold text-[10px] uppercase tracking-wider">
            Store B (Botanical Leaf Co.)
          </div>
          <div className="text-white font-medium text-xs my-1">{storeBProduct}</div>
          <div className="text-emerald-400 text-[11px] font-medium flex items-center gap-1 font-mono">
            <span>✓</span>
            <span>15 units in stock — ₹{amount.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Bottom Explanatory Caption */}
      <p className="text-[11px] text-[#94a3b8] italic border-t border-[#1e2230] pt-2.5 leading-snug">
        Agent automatically discovered an in-stock match at a federated partner store and re-routed checkout — no user intervention required.
      </p>
    </div>
  );
}
''')

# 3. LiveReasoningTrace.tsx
with open(os.path.join(base, "LiveReasoningTrace.tsx"), "w", encoding="utf-8") as f:
    f.write('''"use client";

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
''')

with open("frontend/components/sections/AgentStudio.tsx", "w", encoding="utf-8") as f:
    f.write(r'''"use client";

import React, { useState, useRef, useEffect } from "react";
import MetaStrip from "@/components/MetaStrip";
import GatingCard from "@/components/GatingCard";
import ReceiptCard from "@/components/ReceiptCard";
import UpsellCard from "@/components/UpsellCard";
import FailoverCard from "@/components/FailoverCard";
import LiveReasoningTrace from "@/components/LiveReasoningTrace";
import {
  sendAgentStudioChat,
  confirmGatingProposal,
  executeUpsellOption,
  simulateStockout,
} from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  failoverData?: {
    storeAProduct: string;
    storeBProduct: string;
    amount: number;
  };
  razorpayData?: {
    orderId: string;
    paymentId?: string;
    amount: number;
    items?: string;
  };
}

interface AgentStudioProps {
  spendingCap: number;
  setSpendingCap: (cap: number) => void;
  gatingMode: string;
  isSystemHalted: boolean;
}

export default function AgentStudio({
  spendingCap,
  setSpendingCap,
  gatingMode,
  isSystemHalted,
}: AgentStudioProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Welcome — ask me about the catalog or make a purchase within your cap.",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelineStepIndex, setPipelineStepIndex] = useState<number | null>(null);

  // Active Pending Proposals
  const [pendingGating, setPendingGating] = useState<any>(null);
  const [pendingUpsell, setPendingUpsell] = useState<any>(null);
  const [declineFeedback, setDeclineFeedback] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, pendingGating, pendingUpsell, pipelineStepIndex]);

  const handleSendPrompt = async (promptText: string) => {
    if (!promptText.trim() || isProcessing || pendingGating || pendingUpsell) return;

    setDeclineFeedback(null);
    const userMsg: Message = { role: "user", content: promptText };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsProcessing(true);
    setPipelineStepIndex(0); // Step 1: Catalog search

    const t1 = setTimeout(() => {
      setPipelineStepIndex(1); // Step 2: Gemini reasoning
    }, 350);

    const t2 = setTimeout(() => {
      setPipelineStepIndex(2); // Step 3: Evaluating guardrail cap
    }, 1400);

    try {
      const resp = await sendAgentStudioChat(promptText, spendingCap, gatingMode, messages);

      clearTimeout(t1);
      clearTimeout(t2);
      setPipelineStepIndex(3); // Step 4: Awaiting human gate / complete
      setTimeout(() => setPipelineStepIndex(null), 400);

      if (resp.type === "chat_reply") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `🧠 **Agent LLM Reasoning**: ${resp.content}` },
        ]);
      } else if (resp.type === "upsell") {
        setPendingUpsell(resp);
      } else if (resp.type === "gating") {
        setPendingGating(resp);
      } else if (resp.type === "execution_result") {
        const r = resp.result;
        if (r?.success) {
          const replyText = `Purchase Completed: Purchased **${r.summary_names}** for **₹${r.amount_inr?.toFixed(2)}**.`;
          const msg: Message = {
            role: "assistant",
            content: replyText,
            razorpayData: {
              orderId: r.razorpay_order_id,
              paymentId: r.razorpay_payment_id,
              amount: r.amount_inr,
            },
          };
          if (r.federated_failover) {
            msg.failoverData = {
              storeAProduct: "Kashmir Kahwa Saffron Blend",
              storeBProduct: r.summary_names,
              amount: r.amount_inr,
            };
          }
          setMessages((prev) => [...prev, msg]);
        } else {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: `Action Blocked: ${r?.reason || r?.message || "Failed to complete purchase"}` },
          ]);
        }
      } else if (resp.type === "error") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `⚠️ ${resp.message}` },
        ]);
      }
    } catch (err: any) {
      clearTimeout(t1);
      clearTimeout(t2);
      setPipelineStepIndex(null);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Failed to connect to backend: ${err.message}` },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApproveGating = async () => {
    if (!pendingGating) return;
    setIsProcessing(true);
    try {
      const res = await confirmGatingProposal(pendingGating.session_id, true);
      if (res.success) {
        const replyText = `Purchase Completed: Purchased **${res.summary_names}** for **₹${res.amount_inr?.toFixed(2)}** under your cap.`;
        const msg: Message = {
          role: "assistant",
          content: replyText,
          razorpayData: {
            orderId: res.razorpay_order_id,
            paymentId: res.razorpay_payment_id,
            amount: res.amount_inr,
          },
        };
        if (res.federated_failover) {
          msg.failoverData = {
            storeAProduct: "Kashmir Kahwa Saffron Blend",
            storeBProduct: res.summary_names,
            amount: res.amount_inr,
          };
        }
        setMessages((prev) => [...prev, msg]);
        setPendingGating(null);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Action Failed: ${res.message}` },
        ]);
        setPendingGating(null);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error executing payment: ${err.message}` },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDenyGating = async () => {
    if (!pendingGating) return;
    try {
      await confirmGatingProposal(pendingGating.session_id, false);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Action Denied: User rejected gating clearance." },
      ]);
      setDeclineFeedback("Transaction declined — no charge made, cart reservation released.");
    } catch {
      // fallback
    }
    setPendingGating(null);
  };

  const handleUpsellOption = async (opt: "A" | "B" | "C") => {
    if (!pendingUpsell) return;
    setIsProcessing(true);
    try {
      const res = await executeUpsellOption(pendingUpsell.user_prompt, opt, pendingUpsell.upsell);
      if (opt === "C") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Action Aborted: User declined recommendation." },
        ]);
        setDeclineFeedback("Recommendation declined — transaction aborted.");
      } else if (res.success) {
        const r = res.result;
        if (opt === "B" && res.new_cap) {
          setSpendingCap(res.new_cap);
        }
        const replyText =
          opt === "B"
            ? `Revenue Upsell Successful: Upgraded cap to **₹${res.new_cap?.toFixed(2)}** and purchased **${r.summary_names}** for **₹${r.amount_inr?.toFixed(2)}**.`
            : `Purchase Completed: Purchased **${r.summary_names}** for **₹${r.amount_inr?.toFixed(2)}** under your cap.`;

        const msg: Message = {
          role: "assistant",
          content: replyText,
          razorpayData: {
            orderId: r.razorpay_order_id,
            paymentId: r.razorpay_payment_id,
            amount: r.amount_inr,
          },
        };
        setMessages((prev) => [...prev, msg]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message}` },
      ]);
    } finally {
      setPendingUpsell(null);
      setIsProcessing(false);
    }
  };

  const handleResetSession = () => {
    setMessages([
      {
        role: "assistant",
        content: "Welcome — ask me about the catalog or make a purchase within your cap.",
      },
    ]);
    setPendingGating(null);
    setPendingUpsell(null);
    setDeclineFeedback(null);
    setPipelineStepIndex(null);
  };

  const handleFailoverSim = async () => {
    await simulateStockout("tea-001");
    handleSendPrompt("Buy Kashmir Kahwa Saffron Blend");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] max-w-[1000px]">
      {/* Top Header Bar with MetaStrip & New Session Button */}
      <div className="flex items-center justify-between mb-2">
        <MetaStrip />
        <button
          onClick={handleResetSession}
          disabled={isProcessing}
          className="text-xs text-[#94a3b8] hover:text-white bg-[#11131c] hover:bg-[#1c1c2e] border border-[#1e2230] px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 shadow-sm"
          title="Reset conversation and start fresh session"
        >
          <span>↺</span>
          <span>New Session</span>
        </button>
      </div>

      {/* Emergency Halt Banner */}
      {isSystemHalted && (
        <div className="bg-red-500/15 border border-red-500/40 text-red-400 px-4 py-2.5 rounded-lg text-xs mb-3">
          🚨 EMERGENCY SYSTEM HALT ACTIVE — ALL AUTONOMOUS PAYMENTS & CART RESERVATIONS FROZEN (POST /api/agent-halt).
        </div>
      )}

      {/* Scenario Quick Action Chips (Always accessible) */}
      <div className="flex flex-wrap items-center gap-2 mb-3 pb-2 border-b border-[#1e2230]/50">
        <span className="text-[10px] uppercase font-semibold text-[#6b6f85] tracking-wider mr-1">
          Scenarios:
        </span>
        <button
          onClick={() => handleSendPrompt("Get a caffeine-free herbal tea for sleep under ₹500")}
          disabled={isProcessing || pendingGating !== null || pendingUpsell !== null || isSystemHalted}
          className="bg-[#11131c] border border-[#1e2230] hover:border-[#00baf2]/60 hover:bg-[#161926] text-[11px] text-[#d4d4d8] py-1 px-2.5 rounded-md transition disabled:opacity-40"
        >
          1. Sleep tea (₹380)
        </button>
        <button
          onClick={() => {
            setSpendingCap(500);
            handleSendPrompt("Buy Japanese Ceremonial Matcha Grade-A");
          }}
          disabled={isProcessing || pendingGating !== null || pendingUpsell !== null || isSystemHalted}
          className="bg-[#11131c] border border-amber-500/30 hover:border-amber-500 hover:bg-[#161926] text-[11px] text-amber-400 py-1 px-2.5 rounded-md transition disabled:opacity-40"
        >
          2. Matcha Upsell (₹950 vs ₹500 cap)
        </button>
        <button
          onClick={() => {
            setSpendingCap(1500);
            handleSendPrompt("Buy 1 Kahwa and 1 Darjeeling");
          }}
          disabled={isProcessing || pendingGating !== null || pendingUpsell !== null || isSystemHalted}
          className="bg-[#11131c] border border-[#1e2230] hover:border-[#00baf2]/60 hover:bg-[#161926] text-[11px] text-[#d4d4d8] py-1 px-2.5 rounded-md transition disabled:opacity-40"
        >
          3. Multi-Item (₹1500 cap)
        </button>
        <button
          onClick={handleFailoverSim}
          disabled={isProcessing || pendingGating !== null || pendingUpsell !== null || isSystemHalted}
          className="bg-[#11131c] border border-[#00baf2]/30 hover:border-[#00baf2] hover:bg-[#161926] text-[11px] text-[#00baf2] py-1 px-2.5 rounded-md transition disabled:opacity-40"
        >
          4. Cross-Store Failover
        </button>
      </div>

      {/* Chat Messages Scroll Container */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 pb-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-[#1c1c2e] text-white border border-[#2a2e42]"
                  : "bg-[#11131c] text-[#d4d4d8] border border-[#1e2230]"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* Component 2: Dedicated Cross-Store Failover Card */}
              {msg.failoverData && (
                <FailoverCard
                  storeAProduct={msg.failoverData.storeAProduct}
                  storeBProduct={msg.failoverData.storeBProduct}
                  amount={msg.failoverData.amount}
                />
              )}

              {/* Razorpay Receipt */}
              {msg.razorpayData && <ReceiptCard orderId={msg.razorpayData.orderId} />}
            </div>
          </div>
        ))}

        {/* Component 3: Live Agent Reasoning Trace */}
        {pipelineStepIndex !== null && (
          <LiveReasoningTrace currentStepIndex={pipelineStepIndex} />
        )}

        {/* Decline Feedback Banner */}
        {declineFeedback && (
          <div className="bg-red-500/10 border-l-4 border-red-500 text-red-400 text-xs px-4 py-2.5 rounded-r-lg animate-decline-slide">
            ⚠️ {declineFeedback}
          </div>
        )}

        {/* Pending Gating Checkpoint Card (Navy Electric Accent) */}
        {pendingGating && (
          <GatingCard
            summaryNames={pendingGating.summary_names}
            totalAmount={pendingGating.total_amount_inr}
            spendingCap={pendingGating.spending_cap_inr}
            onApprove={handleApproveGating}
            onDeny={handleDenyGating}
            isLoading={isProcessing}
          />
        )}

        {/* Component 1: Redesigned Upsell Recommendation Card (Amber Token) */}
        {pendingUpsell && (
          <UpsellCard
            upsellData={pendingUpsell.upsell}
            spendingCap={spendingCap}
            onSelectOption={handleUpsellOption}
            isLoading={isProcessing}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Pinned Chat Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendPrompt(inputValue);
        }}
        className="pt-2"
      >
        <div className="relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isProcessing || pendingGating !== null || pendingUpsell !== null || isSystemHalted}
            placeholder={
              pendingGating || pendingUpsell
                ? "Please respond to the active proposal above..."
                : isSystemHalted
                ? "System halted — resume kill switch in sidebar to chat..."
                : "Enter purchase goal or ask why a decision was made..."
            }
            className="w-full bg-[#11131c] border border-[#1e2230] rounded-xl px-4 py-3.5 text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-[#00baf2] disabled:opacity-50 disabled:cursor-not-allowed transition pr-12"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isProcessing || pendingGating !== null || pendingUpsell !== null || isSystemHalted}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 bg-[#1c1c2e] hover:bg-[#25253e] disabled:opacity-30 disabled:hover:bg-[#1c1c2e] text-white p-2 rounded-lg transition"
          >
            ↑
          </button>
        </div>
      </form>
    </div>
  );
}
''')

print("All components and AgentStudio.tsx written successfully.")

