export interface Product {
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

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

export async function fetchCatalog(inStockOnly: boolean = false): Promise<CatalogResponse> {
  const res = await fetch(`${BASE_URL}/catalog?in_stock_only=${inStockOnly}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch catalog");
  return res.json();
}

export async function fetchStoreBCatalog(): Promise<CatalogResponse> {
  const res = await fetch(`${BASE_URL}/merchant-b/catalog?in_stock_only=false`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch Store B catalog");
  return res.json();
}

export async function fetchAgentSpec(): Promise<any> {
  const res = await fetch(`${BASE_URL}/agent-spec`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch agent spec");
  return res.json();
}

export async function fetchAuditLogs(): Promise<AuditLogRecord[]> {
  const res = await fetch(`${BASE_URL}/api/audit-logs`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch audit logs");
  return res.json();
}

export async function clearAuditLogs(): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${BASE_URL}/api/audit-logs`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear audit logs");
  return res.json();
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const res = await fetch(`${BASE_URL}/api/agent-status`, { cache: "no-store" });
  if (!res.ok) return { system_halted: false, status: "ACTIVE", message: "OK" };
  return res.json();
}

export async function haltSystem(): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/agent-halt`, { method: "POST" });
  return res.json();
}

export async function resumeSystem(): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/agent-resume`, { method: "POST" });
  return res.json();
}

export async function sendAgentStudioChat(
  message: string,
  spendingCap: number,
  gatingMode: string,
  history: any[] = []
): Promise<any> {
  let res = await fetch(`${BASE_URL}/api/agent-studio-chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      spending_cap_inr: spendingCap,
      gating_mode: gatingMode,
      history,
    }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Server returned ${res.status}: ${errText || "Agent request failed"}`);
  }
  return res.json();
}

export async function confirmGatingProposal(sessionId: string, approved: boolean): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/confirm-gating`, {
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
  const res = await fetch(`${BASE_URL}/api/agent-studio-upsell`, {
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
  return fetch(`${BASE_URL}/simulate-stockout?product_id=${productId}`, { method: "POST" });
}

export async function resetCatalog(): Promise<any> {
  return fetch(`${BASE_URL}/reset-catalog`, { method: "POST" });
}
