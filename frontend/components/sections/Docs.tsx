import React from "react";

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
          <div className="bg-[var(--code-bg)] border border-[var(--border-color)] p-3 rounded-lg font-mono text-[11px] text-[#00baf2] shadow-[var(--card-shadow)]">
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
            • <strong>Real Order Creation</strong>: Calls <code>client.order.create()</code> to generate genuine Razorpay test order IDs (<code>order_...</code>) in paise (₹1 = 100 paise).
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
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">
          System Architecture & Technical Specifications
        </h2>
        <p className="text-xs text-[var(--text-secondary)]">
          Comprehensive end-to-end reference guide for judges and technical evaluation.
        </p>
      </div>

      <div className="space-y-3">
        {sections.map((sec, idx) => (
          <details
            key={idx}
            open={sec.defaultOpen}
            className="group bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl overflow-hidden shadow-[var(--card-shadow)] transition-colors"
          >
            <summary className="px-4 py-3 cursor-pointer text-xs font-semibold text-[var(--text-primary)] hover:text-blue-500 transition flex items-center justify-between select-none">
              <span>{sec.title}</span>
              <span className="text-[var(--text-muted)] group-open:rotate-180 transition-transform text-[10px]">
                ▼
              </span>
            </summary>
            <div className="px-4 pb-4 pt-1 border-t border-[var(--border-color)]/60 text-[var(--text-secondary)]">{sec.content}</div>
          </details>
        ))}
      </div>
    </div>
  );
}
