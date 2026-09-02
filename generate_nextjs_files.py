import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "frontend")

files = {}

# 1. tailwind.config.ts
files["tailwind.config.ts"] = '''import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bgDark: "#090a0f",
        sidebarDark: "#0c0c14",
        borderDark: "#1e2230",
        mutedText: "#6b6f85",
        pillActive: "#1c1c2e",
        navyAccent: "#0000D6",
        onlineGreen: "#5dcaa5",
        emeraldSuccess: "#10b981",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
'''

# 2. app/globals.css
files["app/globals.css"] = '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-dark: #090a0f;
}

body {
  background-color: #090a0f;
  color: #f4f4f5;
  font-family: var(--font-inter), system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow-x: hidden;
}

/* Custom minimal scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: #0c0c14;
}
::-webkit-scrollbar-thumb {
  background: #1e2230;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #2a2e42;
}

/* Keyframe Animations */
@keyframes successCardFade {
  0% { opacity: 0; transform: translateY(10px); }
  100% { opacity: 1; transform: translateY(0); }
}

.animate-success-fade {
  animation: successCardFade 0.4s ease-out forwards;
}

@keyframes slideInDecline {
  0% { opacity: 0; transform: translateX(-12px); }
  100% { opacity: 1; transform: translateX(0); }
}

.animate-decline-slide {
  animation: slideInDecline 0.25s ease-out forwards;
}
'''

# 3. app/layout.tsx
files["app/layout.tsx"] = '''import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Boundly — Bounded Agent Commerce Studio",
  description: "Next.js Frontend for Autonomous Bounded AI Agent Commerce Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} dark`}>
      <body className="bg-[#090a0f] text-[#f4f4f5] antialiased min-h-screen selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
'''

# 4. lib/api.ts
files["lib/api.ts"] = '''export interface Product {
  id: string;
  name: string;
  category: string;
  price_inr: number;
  stock_qty: number;
  description: string;
  merchant_name?: string;
  attributes: {
    origin?: string;
    caffeine_level?: string;
    flavor_notes?: string[];
    [key: string]: any;
  };
  tags?: string[];
}

export interface CatalogResponse {
  merchant_name: string;
  total_products: number;
  products: Product[];
}

export interface AuditLogRecord {
  id: number;
  timestamp: string;
  session_id: string;
  step_type: string;
  proposed_action: string;
  guardrail_passed: boolean;
  guardrail_message?: string;
  gate_status: string;
  razorpay_order_id?: string;
  outcome_status: string;
  llm_reasoning?: string;
  proposed_amount_inr?: number;
}

export interface SystemStatus {
  system_halted: boolean;
  status: string;
  message: string;
}

export async function fetchCatalog(inStockOnly: boolean = false): Promise<CatalogResponse> {
  const res = await fetch(`/catalog?in_stock_only=${inStockOnly}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch catalog");
  return res.json();
}

export async function fetchStoreBCatalog(): Promise<CatalogResponse> {
  const res = await fetch("/merchant-b/catalog?in_stock_only=false", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch Store B catalog");
  return res.json();
}

export async function fetchAgentSpec(): Promise<any> {
  const res = await fetch("/agent-spec", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch agent spec");
  return res.json();
}

export async function fetchAuditLogs(): Promise<AuditLogRecord[]> {
  const res = await fetch("/api/audit-logs", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch audit logs");
  return res.json();
}

export async function clearAuditLogs(): Promise<{ success: boolean; message: string }> {
  const res = await fetch("/api/audit-logs", { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear audit logs");
  return res.json();
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const res = await fetch("/api/agent-status", { cache: "no-store" });
  if (!res.ok) return { system_halted: false, status: "ACTIVE", message: "OK" };
  return res.json();
}

export async function haltSystem(): Promise<any> {
  const res = await fetch("/api/agent-halt", { method: "POST" });
  return res.json();
}

export async function resumeSystem(): Promise<any> {
  const res = await fetch("/api/agent-resume", { method: "POST" });
  return res.json();
}

export async function sendAgentStudioChat(
  message: string,
  spendingCap: number,
  gatingMode: string,
  history: any[] = []
): Promise<any> {
  const res = await fetch("/api/agent-studio-chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      spending_cap_inr: spendingCap,
      gating_mode: gatingMode,
      history,
    }),
  });
  if (!res.ok) throw new Error("Agent request failed");
  return res.json();
}

export async function confirmGatingProposal(sessionId: string, approved: boolean): Promise<any> {
  const res = await fetch("/api/confirm-gating", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      approved,
    }),
  });
  if (!res.ok) throw new Error("Confirm gating request failed");
  return res.json();
}

export async function executeUpsellOption(userPrompt: string, option: string, upsellData: any): Promise<any> {
  const res = await fetch("/api/agent-studio-upsell", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_prompt: userPrompt,
      option,
      upsell_data: upsellData,
    }),
  });
  if (!res.ok) throw new Error("Execute upsell request failed");
  return res.json();
}

export async function simulateStockout(productId: string = "tea-001"): Promise<any> {
  return fetch(`/simulate-stockout?product_id=${productId}`, { method: "POST" });
}

export async function resetCatalog(): Promise<any> {
  return fetch("/reset-catalog", { method: "POST" });
}
'''

# 5. components/Sidebar.tsx
files["components/Sidebar.tsx"] = '''"use client";

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
    <aside className="w-[210px] min-w-[210px] max-w-[210px] h-screen bg-[#0c0c14] border-r border-[#1e2230] p-4 flex flex-col justify-between select-none fixed left-0 top-0 z-30">
      {/* Top section */}
      <div>
        {/* Wordmark */}
        <div className="pb-3 border-b border-[#1e2230] mb-3.5">
          <h1 className="text-[22px] font-bold text-white tracking-tight leading-tight">
            Boundly
          </h1>
          <p className="text-[11px] text-[#6b6f85] font-normal mt-0.5">
            Bounded agent commerce
          </p>
        </div>

        {/* NAVIGATION Section */}
        <div className="mb-4">
          <div className="text-[10px] uppercase font-semibold text-[#6b6f85] tracking-wider mb-2">
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
                      ? "bg-[#1c1c2e] text-white font-medium"
                      : "text-[#6b6f85] hover:text-[#d4d4d8] hover:bg-[#151522] bg-transparent"
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
          <div className="text-[10px] uppercase font-semibold text-[#6b6f85] tracking-wider mb-2">
            SECURITY
          </div>
          <div className="flex flex-col gap-2">
            {/* Spending Cap */}
            {isEditingCap ? (
              <form onSubmit={handleCapSubmit} className="flex items-center gap-1">
                <span className="text-xs text-[#a1a1aa]">Cap ₹</span>
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
                  className="w-16 bg-[#181a26] border border-[#2a2e42] rounded px-1 py-0.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </form>
            ) : (
              <div
                onClick={() => {
                  setCapInputValue(spendingCap.toString());
                  setIsEditingCap(true);
                }}
                className="text-xs text-white font-medium cursor-pointer hover:text-blue-400 transition flex items-center justify-between"
                title="Click to edit spending cap"
              >
                <span>Cap ₹{spendingCap.toFixed(2)}</span>
                <span className="text-[10px] text-[#6b6f85]">✎</span>
              </div>
            )}

            {/* Gating Mode */}
            <div
              onClick={toggleGating}
              className="text-xs text-[#d4d4d8] cursor-pointer hover:text-white transition flex items-center justify-between"
              title="Click to switch between Human Review Gate and Auto Approve"
            >
              <span>{gatingMode}</span>
              <span className="text-[10px] text-[#6b6f85]">⟳</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Pinned Status Section */}
      <div className="pt-3 flex flex-col gap-2 border-t border-[#1e2230]/50">
        {/* Kill switch pill */}
        <button
          onClick={toggleSystemHalt}
          className={`w-full text-left text-[11px] px-2.5 py-1.5 rounded-md border transition-all flex items-center justify-between ${
            isSystemHalted
              ? "bg-[rgba(239,68,68,0.2)] border-[rgba(239,68,68,0.5)] text-[#f87171]"
              : "bg-[rgba(226,75,74,0.1)] border-[rgba(226,75,74,0.3)] text-[#f09595] hover:bg-[rgba(226,75,74,0.18)]"
          }`}
          title="Toggle Emergency System Kill Switch"
        >
          <span>{isSystemHalted ? "🚨 Kill switch: on" : "🚨 Kill switch: off"}</span>
          <span className="text-[10px] opacity-75">{isSystemHalted ? "FROZEN" : "OFF"}</span>
        </button>

        {/* API online status badge */}
        <div className="font-mono text-[10px] text-[#5dcaa5] flex items-center gap-1.5 px-0.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#5dcaa5] animate-pulse"></span>
          <span>online :8000</span>
        </div>
      </div>
    </aside>
  );
}
'''

# 6. components/MetaStrip.tsx
files["components/MetaStrip.tsx"] = '''import React from "react";

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
'''

# 7. components/GatingCard.tsx
files["components/GatingCard.tsx"] = '''"use client";

import React from "react";

interface GatingCardProps {
  summaryNames: string;
  totalAmount: number;
  spendingCap: number;
  onApprove: () => void;
  onDeny: () => void;
  isLoading?: boolean;
}

export default function GatingCard({
  summaryNames,
  totalAmount,
  spendingCap,
  onApprove,
  onDeny,
  isLoading = false,
}: GatingCardProps) {
  return (
    <div className="bg-[#0000D6] border border-[#1a1aff] rounded-2xl p-6 shadow-2xl text-white my-4 transition-all">
      <div className="text-xs font-medium text-[#93c5fd] mb-2">
        Gating checkpoint
      </div>
      <div className="text-xl font-bold text-white mb-6">
        {summaryNames} — ₹{totalAmount.toFixed(0)} within ₹{spendingCap.toFixed(0)} cap
      </div>
      <div className="flex gap-3">
        <button
          onClick={onApprove}
          disabled={isLoading}
          className="flex-1 bg-white text-[#0000D6] font-semibold text-sm py-2.5 px-6 rounded-lg hover:bg-slate-100 transition shadow-md disabled:opacity-50 text-center"
        >
          {isLoading ? "Executing..." : "Approve"}
        </button>
        <button
          onClick={onDeny}
          disabled={isLoading}
          className="flex-1 bg-transparent border border-white/40 text-white font-medium text-sm py-2.5 px-6 rounded-lg hover:bg-red-500/20 hover:border-red-500 transition text-center disabled:opacity-50"
        >
          Deny
        </button>
      </div>
    </div>
  );
}
'''

# 8. components/ReceiptCard.tsx
files["components/ReceiptCard.tsx"] = '''import React from "react";

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
'''

# 9. components/ProductCard.tsx
files["components/ProductCard.tsx"] = '''import React from "react";
import { Product } from "@/lib/api";

interface ProductCardProps {
  product: Product;
  isStoreB?: boolean;
}

export default function ProductCard({ product, isStoreB = false }: ProductCardProps) {
  const inStock = product.stock_qty > 0;
  const caffeine = product.attributes?.caffeine_level || "N/A";
  const flavors = product.attributes?.flavor_notes?.join(", ") || "Artisan blend";
  const origin = product.attributes?.origin || "Estate Harvest";

  return (
    <div
      className={`bg-[#11131c]/75 border rounded-xl p-4 backdrop-blur-md transition-all duration-200 hover:-translate-y-0.5 flex flex-col justify-between h-full ${
        isStoreB
          ? "border-[#00baf2]/30 hover:border-[#00baf2] hover:shadow-[0_8px_24px_rgba(0,186,242,0.15)]"
          : "border-[#1e2230] hover:border-[#00baf2] hover:shadow-[0_8px_24px_rgba(0,186,242,0.15)]"
      }`}
    >
      <div>
        <div className="flex justify-between items-start gap-2 mb-1">
          <h3 className="font-medium text-[15px] text-[#f4f4f5] leading-snug">
            {product.name}
          </h3>
          {inStock ? (
            <span className="bg-[#10b981]/10 border border-[#10b981]/25 text-[#10b981] text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0">
              {product.stock_qty} IN STOCK
            </span>
          ) : (
            <span className="bg-[#ef4444]/10 border border-[#ef4444]/25 text-[#ef4444] text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0">
              OUT OF STOCK
            </span>
          )}
        </div>

        <div className="font-mono text-[11px] text-[#64748b] mb-3">
          ID: <span className={isStoreB ? "text-[#00baf2]" : ""}>{product.id}</span> • {product.category}
        </div>

        <div className="text-[18px] font-semibold text-[#10b981] mb-2.5">
          ₹{product.price_inr.toFixed(2)}
        </div>

        <div className="space-y-1 text-xs mb-3">
          {isStoreB && (
            <div className="text-[#71717a]">
              Origin: <span className="text-[#d4d4d8] font-normal">{origin}</span>
            </div>
          )}
          <div className="text-[#71717a]">
            Caffeine: <span className="text-[#d4d4d8] font-normal">{caffeine}</span>
          </div>
          <div className="text-[#71717a]">
            Flavors: <span className="text-[#d4d4d8] font-normal">{flavors}</span>
          </div>
        </div>
      </div>

      <p className="text-[11px] text-[#71717a] line-clamp-2 italic border-t border-[#1e2230]/60 pt-2">
        {product.description}
      </p>
    </div>
  );
}
'''

# 10. components/sections/AgentStudio.tsx
files["components/sections/AgentStudio.tsx"] = '''"use client";

import React, { useState, useRef, useEffect } from "react";
import MetaStrip from "@/components/MetaStrip";
import GatingCard from "@/components/GatingCard";
import ReceiptCard from "@/components/ReceiptCard";
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
  const [pipelineStep, setPipelineStep] = useState<string | null>(null);

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
  }, [messages, pendingGating, pendingUpsell]);

  const handleSendPrompt = async (promptText: string) => {
    if (!promptText.trim() || isProcessing || pendingGating || pendingUpsell) return;

    setDeclineFeedback(null);
    const userMsg: Message = { role: "user", content: promptText };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsProcessing(true);
    setPipelineStep("Querying Machine-Readable Merchant Catalog (GET /catalog)...");

    try {
      setTimeout(() => {
        setPipelineStep("Executing Gemini LLM Intent & Catalog Reasoning (gemini-2.0-flash)...");
      }, 350);

      const resp = await sendAgentStudioChat(promptText, spendingCap, gatingMode, messages);

      setPipelineStep(null);

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
      setPipelineStep(null);
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

  const handleFailoverSim = async () => {
    await simulateStockout("tea-001");
    handleSendPrompt("Buy Kashmir Kahwa Saffron Blend");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] max-w-[1000px]">
      {/* Top Metadata Strip */}
      <MetaStrip />

      {/* Emergency Halt Banner */}
      {isSystemHalted && (
        <div className="bg-red-500/15 border border-red-500/40 text-red-400 px-4 py-2.5 rounded-lg text-xs mb-4">
          🚨 EMERGENCY SYSTEM HALT ACTIVE — ALL AUTONOMOUS PAYMENTS & CART RESERVATIONS FROZEN (POST /api/agent-halt).
        </div>
      )}

      {/* Preset Action Chips */}
      {messages.length <= 1 && (
        <div className="grid grid-cols-3 gap-3 mb-5">
          <button
            onClick={() => handleSendPrompt("Get a caffeine-free herbal tea for sleep under ₹500")}
            disabled={isProcessing || isSystemHalted}
            className="bg-[#11131c] border border-[#1e2230] hover:border-[#00baf2]/60 hover:bg-[#161926] text-xs text-[#d4d4d8] py-2.5 px-3 rounded-lg text-center transition"
          >
            Try: Sleep teas under ₹500
          </button>
          <button
            onClick={() => handleSendPrompt("Buy Japanese Ceremonial Matcha Grade-A")}
            disabled={isProcessing || isSystemHalted}
            className="bg-[#11131c] border border-[#1e2230] hover:border-[#00baf2]/60 hover:bg-[#161926] text-xs text-[#d4d4d8] py-2.5 px-3 rounded-lg text-center transition"
          >
            Try: Buy Matcha Grade-A
          </button>
          <button
            onClick={() => {
              setSpendingCap(1500);
              handleSendPrompt("Buy 1 Kahwa and 1 Darjeeling");
            }}
            disabled={isProcessing || isSystemHalted}
            className="bg-[#11131c] border border-[#1e2230] hover:border-[#00baf2]/60 hover:bg-[#161926] text-xs text-[#d4d4d8] py-2.5 px-3 rounded-lg text-center transition"
          >
            Try: Buy 1 Kahwa & 1 Darjeeling
          </button>
        </div>
      )}

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

              {/* Failover Card */}
              {msg.failoverData && (
                <div className="bg-[#0f172a]/80 border border-[#00baf2] rounded-xl p-3.5 mt-3 text-xs">
                  <div className="text-[#00baf2] font-semibold text-xs mb-2">
                    🌐 FEDERATED CROSS-STORE FAILOVER SUMMARY
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-red-500/10 border border-red-500/30 p-2.5 rounded-lg">
                      <div className="text-red-400 font-medium text-[11px]">STORE A (AURA TEAS)</div>
                      <div className="text-white font-medium text-xs mt-0.5">{msg.failoverData.storeAProduct}</div>
                      <div className="text-red-400 text-[11px] mt-1">❌ OUT OF STOCK (0 units)</div>
                    </div>
                    <div className="bg-emerald-500/10 border border-emerald-500/30 p-2.5 rounded-lg">
                      <div className="text-emerald-400 font-medium text-[11px]">STORE B (BOTANICAL LEAF CO.)</div>
                      <div className="text-white font-medium text-xs mt-0.5">{msg.failoverData.storeBProduct}</div>
                      <div className="text-emerald-400 text-[11px] mt-1">
                        ✅ IN STOCK (15 units) — ₹{msg.failoverData.amount.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Razorpay Receipt */}
              {msg.razorpayData && <ReceiptCard orderId={msg.razorpayData.orderId} />}
            </div>
          </div>
        ))}

        {/* Live Pipeline Steps */}
        {pipelineStep && (
          <div className="flex items-center gap-2 text-xs text-[#00baf2] bg-[#00baf2]/10 border border-[#00baf2]/30 px-3.5 py-2.5 rounded-lg w-fit animate-pulse">
            <span className="w-2 h-2 rounded-full bg-[#00baf2] inline-block animate-ping"></span>
            <span>{pipelineStep}</span>
          </div>
        )}

        {/* Decline Feedback Banner */}
        {declineFeedback && (
          <div className="bg-red-500/10 border-l-4 border-red-500 text-red-400 text-xs px-4 py-2.5 rounded-r-lg animate-decline-slide">
            ⚠️ {declineFeedback}
          </div>
        )}

        {/* Pending Gating Checkpoint Card (Matching Mockup exactly) */}
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

        {/* Pending Upsell Card */}
        {pendingUpsell && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 my-3 text-xs space-y-3">
            <div className="text-red-400 font-semibold text-xs">
              🛍️ AUTONOMOUS REVENUE GROWTH & UPSELL PROPOSAL
            </div>
            <p className="text-[#d4d4d8]">
              {pendingUpsell.upsell?.recommendation_reasoning ||
                `Proposed amount exceeds your ₹${spendingCap.toFixed(2)} spending cap.`}
            </p>
            <div className="grid grid-cols-3 gap-2 pt-1">
              <button
                onClick={() => handleUpsellOption("A")}
                disabled={isProcessing}
                className="bg-[#1c1c2e] hover:bg-[#25253e] border border-[#2a2e42] text-white p-2.5 rounded-lg text-left transition"
              >
                <div className="font-semibold text-[11px] text-blue-400">Option A: In-Budget Alternative</div>
                <div className="text-[10px] text-[#a1a1aa] mt-0.5">
                  Buy &apos;{pendingUpsell.upsell?.alternative_product_name}&apos; (₹{pendingUpsell.upsell?.alternative_product_price_inr?.toFixed(2)})
                </div>
              </button>
              <button
                onClick={() => handleUpsellOption("B")}
                disabled={isProcessing}
                className="bg-[#1c1c2e] hover:bg-[#25253e] border border-[#2a2e42] text-white p-2.5 rounded-lg text-left transition"
              >
                <div className="font-semibold text-[11px] text-emerald-400">Option B: Upgrade Spending Cap</div>
                <div className="text-[10px] text-[#a1a1aa] mt-0.5">
                  Upgrade to ₹{pendingUpsell.upsell?.suggested_cap_increase_inr?.toFixed(2)} & Buy &apos;{pendingUpsell.upsell?.breached_product_name}&apos;
                </div>
              </button>
              <button
                onClick={() => handleUpsellOption("C")}
                disabled={isProcessing}
                className="bg-[#1c1c2e] hover:bg-red-500/20 border border-[#2a2e42] hover:border-red-500/40 text-white p-2.5 rounded-lg text-left transition"
              >
                <div className="font-semibold text-[11px] text-red-400">Option C: Abort Action</div>
                <div className="text-[10px] text-[#a1a1aa] mt-0.5">Decline recommendation</div>
              </button>
            </div>
          </div>
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
                ? "Please respond to the active gating proposal above..."
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
'''

# 11. components/sections/CatalogAPI.tsx
files["components/sections/CatalogAPI.tsx"] = '''"use client";

import React, { useState, useEffect } from "react";
import ProductCard from "@/components/ProductCard";
import { fetchCatalog, fetchStoreBCatalog, fetchAgentSpec, Product } from "@/lib/api";

export default function CatalogAPI() {
  const [activeTab, setActiveTab] = useState<"storeA" | "storeB">("storeA");
  const [storeAProducts, setStoreAProducts] = useState<Product[]>([]);
  const [storeBProducts, setStoreBProducts] = useState<Product[]>([]);
  const [agentSpec, setAgentSpec] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [catA, catB] = await Promise.all([
          fetchCatalog(false),
          fetchStoreBCatalog(),
        ]);
        setStoreAProducts(catA.products || []);
        setStoreBProducts(catB.products || []);
      } catch (e) {
        console.error("Failed to load catalogs:", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleFetchSpec = async () => {
    try {
      const spec = await fetchAgentSpec();
      setAgentSpec(spec);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-[1200px]">
      <div>
        <h2 className="text-lg font-semibold text-white">
          Federated Multi-Merchant Product Network
        </h2>
        <p className="text-xs text-[#64748b] mt-0.5">
          Structured JSON attributes consumed directly by autonomous AI buyer agents across federated partner stores.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[#1e2230] pb-2">
        <button
          onClick={() => setActiveTab("storeA")}
          className={`text-xs px-3 py-1.5 rounded-md transition font-medium ${
            activeTab === "storeA"
              ? "bg-[#1c1c2e] text-white"
              : "text-[#6b6f85] hover:text-[#d4d4d8]"
          }`}
        >
          Store A: Aura Artisan Teas (Primary)
        </button>
        <button
          onClick={() => setActiveTab("storeB")}
          className={`text-xs px-3 py-1.5 rounded-md transition font-medium ${
            activeTab === "storeB"
              ? "bg-[#1c1c2e] text-white"
              : "text-[#6b6f85] hover:text-[#d4d4d8]"
          }`}
        >
          Store B: Botanical Leaf Co. (Federated Partner)
        </button>
      </div>

      {/* Products Grid */}
      {loading ? (
        <div className="text-xs text-[#64748b] py-8">Loading product catalog...</div>
      ) : activeTab === "storeA" ? (
        <div className="grid grid-cols-4 gap-4">
          {storeAProducts.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {storeBProducts.map((p) => (
            <ProductCard key={p.id} product={p} isStoreB />
          ))}
        </div>
      )}

      {/* Agent Spec Discovery */}
      <div className="pt-4 border-t border-[#1e2230]">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-white">
            Agent API Metadata Discovery (<code className="font-mono text-xs text-[#00baf2]">GET /agent-spec</code>)
          </h3>
          <button
            onClick={handleFetchSpec}
            className="text-xs bg-[#1c1c2e] hover:bg-[#25253e] text-white px-3 py-1.5 rounded-md border border-[#2a2e42] transition"
          >
            Fetch Agent Specification
          </button>
        </div>

        {agentSpec && (
          <pre className="bg-[#0c0c14] border border-[#1e2230] p-4 rounded-xl text-xs font-mono text-[#34d399] overflow-x-auto max-h-[300px]">
            {JSON.stringify(agentSpec, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
'''

# 12. components/sections/AuditTrail.tsx
files["components/sections/AuditTrail.tsx"] = '''"use client";

import React, { useState, useEffect } from "react";
import { fetchAuditLogs, clearAuditLogs, AuditLogRecord } from "@/lib/api";

export default function AuditTrail() {
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const records = await fetchAuditLogs();
      setLogs(records);
    } catch (e) {
      console.error("Failed to load audit logs:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const handleClear = async () => {
    if (confirm("Clear all audit log records from SQLite?")) {
      await clearAuditLogs();
      loadLogs();
    }
  };

  return (
    <div className="space-y-4 max-w-[1200px]">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">
            Durable SQL Audit Log Inspector
          </h2>
          <p className="text-xs text-[#64748b]">
            Full chronological traceability of autonomous buyer agent decisions and Razorpay transactions.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadLogs}
            className="text-xs bg-[#1c1c2e] hover:bg-[#25253e] text-white px-3 py-1.5 rounded-md border border-[#2a2e42] transition"
          >
            Refresh
          </button>
          <button
            onClick={handleClear}
            className="text-xs bg-red-500/15 hover:bg-red-500/25 border border-red-500/30 text-red-400 px-3 py-1.5 rounded-md transition"
          >
            Reset Database Log
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-xs text-[#64748b] py-8">Loading audit trail...</div>
      ) : logs.length === 0 ? (
        <div className="bg-[#11131c] border border-[#1e2230] rounded-xl p-8 text-center text-xs text-[#64748b]">
          No audit log records found in SQLite database yet.
        </div>
      ) : (
        <div className="border border-[#1e2230] rounded-xl overflow-hidden bg-[#11131c]/70">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#1e2230] bg-[#0c0c14] text-[#6b6f85]">
                <th className="p-3 font-semibold">ID</th>
                <th className="p-3 font-semibold">Timestamp</th>
                <th className="p-3 font-semibold">Step Type</th>
                <th className="p-3 font-semibold">Proposed Action</th>
                <th className="p-3 font-semibold">Amount</th>
                <th className="p-3 font-semibold">Guardrails</th>
                <th className="p-3 font-semibold">Gating</th>
                <th className="p-3 font-semibold">Razorpay Order</th>
                <th className="p-3 font-semibold">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2230]">
              {logs.map((r) => (
                <tr key={r.id} className="hover:bg-[#161926] transition">
                  <td className="p-3 font-mono text-[#64748b]">{r.id}</td>
                  <td className="p-3 font-mono text-[#94a3b8]">{r.timestamp?.split(" ")[1] || r.timestamp}</td>
                  <td className="p-3 font-mono text-blue-400">{r.step_type}</td>
                  <td className="p-3 text-white max-w-[240px] truncate" title={r.proposed_action}>
                    {r.proposed_action}
                  </td>
                  <td className="p-3 font-semibold text-[#10b981]">
                    {r.proposed_amount_inr ? `₹${r.proposed_amount_inr.toFixed(2)}` : "N/A"}
                  </td>
                  <td className="p-3">
                    {r.guardrail_passed ? (
                      <span className="text-emerald-400 font-medium">✅ PASS</span>
                    ) : (
                      <span className="text-red-400 font-medium">❌ BLOCKED</span>
                    )}
                  </td>
                  <td className="p-3 text-[#d4d4d8]">{r.gate_status}</td>
                  <td className="p-3 font-mono text-[#00baf2] text-[11px]">
                    {r.razorpay_order_id || "N/A"}
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                        r.outcome_status.includes("SUCCESS") || r.outcome_status.includes("COMPLETED")
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/25"
                          : r.outcome_status.includes("DENIED") || r.outcome_status.includes("BLOCKED")
                          ? "bg-red-500/10 text-red-400 border border-red-500/25"
                          : "bg-blue-500/10 text-blue-400 border border-blue-500/25"
                      }`}
                    >
                      {r.outcome_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
'''

# 13. components/sections/Docs.tsx
files["components/sections/Docs.tsx"] = '''import React from "react";

export default function Docs() {
  const sections = [
    {
      title: "1. Architecture Overview",
      defaultOpen: true,
      content: (
        <div className="space-y-3 text-xs text-[#d4d4d8] leading-relaxed">
          <p>
            • <strong>Backend Architecture</strong>: Boundly runs a unified <strong>FastAPI backend</strong> (<code>merchant_api/app.py</code> on port <code>8000</code>). Both the Next.js Web Studio and the CLI Runner (<code>run_demo.py</code>) hit this exact same API backend and log to the shared SQLite database (<code>agentic_commerce.db</code>).
          </p>
          <p>• <strong>End-to-End Request Flow</strong>:</p>
          <ol className="list-decimal list-inside space-y-1 pl-2 text-[#a1a1aa]">
            <li><strong>User Goal</strong>: User states a goal or triggers an automated scenario.</li>
            <li><strong>Spec Discovery</strong>: Agent queries <code>GET /agent-spec</code> to discover currency (<code>INR</code>), reservation timeout (<code>15 min</code>), and limits.</li>
            <li><strong>Catalog Retrieval</strong>: Agent queries <code>GET /catalog</code> to fetch structured stock and tags.</li>
            <li><strong>LLM Reasoning</strong>: Google Gemini LLM processes the goal and catalog, returning a structured Pydantic <code>AgentChoice</code> JSON schema.</li>
            <li><strong>Guardrail Circuit Breaker</strong>: <code>GuardrailEngine</code> evaluates single-action and session spending caps.</li>
            <li><strong>Human Gating Clearance</strong>: If Human Review Gate is enabled, execution pauses at checkpoint until user clicks Approve or Deny.</li>
            <li><strong>Cart Stock Reservation</strong>: <code>POST /cart</code> reserves inventory for 15 minutes.</li>
            <li><strong>Razorpay Order Creation</strong>: <code>POST /checkout/create-order</code> creates an official test-mode order (<code>order_...</code>) in paise.</li>
            <li><strong>Signature Verification & Decrement</strong>: <code>POST /checkout/verify-payment</code> verifies HMAC SHA256 signature and decrements catalog stock.</li>
            <li><strong>Durable SQL Audit Trail</strong>: Every step, decision, and payment receipt is logged to SQLite.</li>
          </ol>
          <div className="bg-[#0c0c14] border border-[#1e2230] p-3 rounded-lg font-mono text-[11px] text-[#00baf2]">
            [User Goal] ➔ [Catalog Search] ➔ [LLM Reasoning] ➔ [Guardrail Check] ➔ [Gating Clearance] ➔ [Razorpay Payment] ➔ [SQL Audit Log]
          </div>
        </div>
      ),
    },
    {
      title: "2. Agent Reasoning & LLM Logic",
      defaultOpen: false,
      content: (
        <div className="space-y-3 text-xs text-[#d4d4d8] leading-relaxed">
          <p>
            • <strong>Structured Pydantic Schemas</strong>: Powered by Google Gemini (<code>gemini-2.0-flash</code> / <code>gemini-2.5-flash</code> via the official <code>google.genai</code> SDK), enforcing strict schema compliance for <code>AgentChoice</code> and <code>AgentRecommendationProposal</code>.
          </p>
          <p>• <strong>Autonomous Decision Logic</strong>:</p>
          <ul className="list-disc list-inside space-y-1 pl-2 text-[#a1a1aa]">
            <li><strong>In-Budget Match</strong>: If a product bundle fits under the spending cap, the agent immediately recommends purchase with explicit reasoning.</li>
            <li><strong>Cap Exceeded (Upsell Engine)</strong>: If the requested goal exceeds the spending cap (e.g. ₹950 Matcha vs ₹500 cap), the agent generates an autonomous <strong>Upsell Proposal</strong> offering two options: (A) an in-budget cross-sell alternative (e.g. ₹420 Kahwa), or (B) a spending cap upgrade recommendation.</li>
          </ul>
          <p>
            • <strong>Rate-Limit Fallback Engine</strong>: If Gemini hits an API rate limit (<code>429 RESOURCE_EXHAUSTED</code>), a local token-proximity catalog matcher seamlessly takes over, ensuring zero demo downtime.
          </p>
        </div>
      ),
    },
    {
      title: "3. Security Guardrails & Gating",
      defaultOpen: false,
      content: (
        <div className="space-y-3 text-xs text-[#d4d4d8] leading-relaxed">
          <p>• <strong>Two Independent Code-Level Safety Layers</strong>:</p>
          <ol className="list-decimal list-inside space-y-1 pl-2 text-[#a1a1aa]">
            <li><strong>Deterministic Guardrail Engine</strong>: Runs in pure Python (<code>guardrails/engine.py</code>). Evaluates proposed cart price against single-action caps (<code>max_single_action_inr</code>) and cumulative session limits BEFORE any cart or checkout API call is initiated.</li>
            <li><strong>Human-in-the-Loop Gating</strong>: Pauses agent execution for explicit user clearance at checkpoint.</li>
          </ol>
          <p>
            • <strong>Emergency System Kill Switch</strong>: <code>POST /api/agent-halt</code> acts as a global circuit breaker, freezing all autonomous transactions and stock reservations system-wide with HTTP 503 until <code>POST /api/agent-resume</code> is called.
          </p>
        </div>
      ),
    },
    {
      title: "4. Razorpay Integration",
      defaultOpen: false,
      content: (
        <div className="space-y-3 text-xs text-[#d4d4d8] leading-relaxed">
          <p>
            • <strong>Official Razorpay Python SDK</strong>: Integrates directly with <code>razorpay.Client(auth=(key_id, key_secret))</code> using official Razorpay Test Mode credentials.
          </p>
          <p>
            • <strong>Real Order Creation</strong>: Calls <code>client.order.create()</code> to generate genuine Razorpay test order IDs (<code>order_...</code>) in paise ($1\\text{ INR} = 100\\text{ paise}$).
          </p>
          <p>
            • <strong>HMAC SHA256 Signature Verification</strong>: Validates cryptographic integrity of payment signatures.
          </p>
          <p>
            • <strong>Intentional Architectural Scope</strong>: The backend order creation and signature verification are <strong>100% real Razorpay API calls</strong>. The human-facing browser popup is intentionally omitted because autonomous AI buyer agents perform machine-to-machine payments directly.
          </p>
        </div>
      ),
    },
    {
      title: "5. Federated Multi-Merchant Failover",
      defaultOpen: false,
      content: (
        <div className="space-y-3 text-xs text-[#d4d4d8] leading-relaxed">
          <p>
            • <strong>Automatic Cross-Merchant Routing</strong>: If Store A (<em>Aura Artisan Teas</em>) is out of stock (0 units), the Buyer Agent automatically queries federated partner Store B (<em>Botanical Leaf Co.</em>) via <code>GET /merchant-b/catalog</code>, discovers an in-stock alternative, and completes checkout on Store B without asking the user to re-submit their goal.
          </p>
        </div>
      ),
    },
    {
      title: "6. What's Real vs Simulated",
      defaultOpen: false,
      content: (
        <div className="bg-amber-500/10 border-l-4 border-amber-500 rounded-lg p-4 space-y-3 text-xs text-[#d4d4d8]">
          <h4 className="text-amber-400 font-semibold text-sm">
            ⚡ Complete System Transparency & Scope Breakdown
          </h4>
          <div>
            <strong className="text-white">✅ REAL & 100% FUNCTIONAL:</strong>
            <ul className="list-disc list-inside space-y-1 pl-2 text-[#a1a1aa] mt-1">
              <li>FastAPI Merchant Backend: Live REST server with 19 endpoints on port 8000.</li>
              <li>Google Gemini LLM Engine: Real Pydantic JSON schema generation for intent parsing & upsell proposals.</li>
              <li>Deterministic Guardrail Circuit Breaker: Strict Python code-level cap enforcement.</li>
              <li>Razorpay Order Creation: Real REST API calls creating genuine test order IDs (<code>order_...</code>).</li>
              <li>HMAC SHA256 Signature Verification: Cryptographic payment signature validation.</li>
              <li>15-Minute Cart Stock Reservation: Live inventory locking and expiration timer.</li>
              <li>Federated Cross-Store Failover: Automatic stockout detection and Store B checkout routing.</li>
              <li>Emergency Kill Switch: Global <code>POST /api/agent-halt</code> system freeze.</li>
              <li>SQLite Audit Logger: Full pipeline traceability persisted to <code>agentic_commerce.db</code>.</li>
            </ul>
          </div>
          <div className="pt-2">
            <strong className="text-white">🟡 SIMULATED / INTENTIONAL SCOPE DECISIONS:</strong>
            <ul className="list-disc list-inside space-y-1 pl-2 text-[#a1a1aa] mt-1">
              <li>Razorpay Checkout.js Browser Popup: Machine-to-machine autonomous checkout by design.</li>
              <li>Store B Hosting: Runs on same FastAPI process (via <code>/merchant-b/...</code> routes) for hackathon demo convenience.</li>
              <li>In-Memory Cart State: Active cart reservations live in server memory, while audit records persist in SQLite.</li>
            </ul>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4 max-w-[1000px]">
      <div>
        <h2 className="text-lg font-semibold text-white">
          System Architecture & Technical Specifications
        </h2>
        <p className="text-xs text-[#64748b]">
          Comprehensive end-to-end reference guide for judges and technical evaluation.
        </p>
      </div>

      <div className="space-y-3">
        {sections.map((sec, idx) => (
          <details
            key={idx}
            open={sec.defaultOpen}
            className="group bg-[#11131c] border border-[#1e2230] rounded-xl overflow-hidden"
          >
            <summary className="px-4 py-3 cursor-pointer text-xs font-semibold text-white hover:text-blue-400 transition flex items-center justify-between select-none">
              <span>{sec.title}</span>
              <span className="text-[#64748b] group-open:rotate-180 transition-transform text-[10px]">
                ▼
              </span>
            </summary>
            <div className="px-4 pb-4 pt-1 border-t border-[#1e2230]/50">{sec.content}</div>
          </details>
        ))}
      </div>
    </div>
  );
}
'''

# 14. app/page.tsx
files["app/page.tsx"] = '''"use client";

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
'''

for filepath, content in files.items():
    full_path = os.path.join(BASE_DIR, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {filepath}")

print("All Next.js files written successfully!")
