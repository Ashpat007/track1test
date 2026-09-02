"use client";

import React, { useState, useRef, useEffect } from "react";
import MetaStrip from "@/components/MetaStrip";
import GatingCard from "@/components/GatingCard";
import ReceiptCard from "@/components/ReceiptCard";
import UpsellCard from "@/components/UpsellCard";
import FailoverCard from "@/components/FailoverCard";
import LiveReasoningTrace from "@/components/LiveReasoningTrace";
import FormattedChatMessage from "@/components/FormattedChatMessage";
import {
  sendAgentStudioChat,
  confirmGatingProposal,
  executeUpsellOption,
  simulateStockout,
  resetCatalog,
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
      const cleanHistory = messages.map((m) => ({ role: m.role, content: m.content }));
      const resp = await sendAgentStudioChat(promptText, spendingCap, gatingMode, cleanHistory);

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

  const handleResetSession = async () => {
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
    try {
      await resetCatalog();
    } catch {}
  };

  const handleFailoverSim = async () => {
    setSpendingCap(500);
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
              <FormattedChatMessage content={msg.content} role={msg.role} />

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
          <div>
            {pendingGating.is_federated && (
              <FailoverCard
                storeAProduct={pendingGating.store_a_product}
                storeBProduct={pendingGating.store_b_product}
                amount={pendingGating.total_amount_inr}
              />
            )}
            <GatingCard
              summaryNames={pendingGating.summary_names}
              totalAmount={pendingGating.total_amount_inr}
              spendingCap={pendingGating.spending_cap_inr}
              itemsDetail={pendingGating.items_detail}
              reasoning={pendingGating.reasoning}
              onApprove={handleApproveGating}
              onDeny={handleDenyGating}
              isLoading={isProcessing}
            />
          </div>
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
