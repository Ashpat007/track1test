# 🍵 Agentic Commerce & Bounded M2M Payments
> **Razorpay AI Buildathon — Track 01 Submission: AI Growth & Agentic Commerce**

A production-grade, end-to-end implementation of an **Agent-Transactable Merchant** and an **Independent AI Buyer Agent**. Built on top of FastAPI, Gemini LLM, Razorpay Test API, and a deterministic Guardrails/Audit Layer.

---

## 📌 Problem Statement & Core Philosophy

Most AI commerce hackathon projects build a **chat UI for humans** (e.g. a chatbot where a user asks for product recommendations and clicks a payment link). 

This project proves **genuine Agentic Commerce**:
1. **Agent-Readable Merchant API**: Exposes strict schema contracts (`GET /agent-spec`), price standards (INR), stock reservation rules, and variant metadata so external autonomous software agents can browse, filter, and transact without human UI scraping.
2. **Independent Buyer Agent**: A standalone script with **zero internal access or database privileges**. It communicates purely via REST API calls over HTTP.
3. **Deterministic Guardrails & Gating Layer**: Confines the LLM strictly to intent parsing and catalog reasoning. The LLM **cannot** execute money-moving calls directly. All payments require passing a code-enforced spending cap and a human-in-the-loop gating gate.
4. **Durable Audit Log**: Captures every decision step, reasoning trace, guardrail check, and Razorpay Order ID into PostgreSQL/SQLite for 100% inspectability.

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[Natural Language Goal e.g. 'Caffeine-free tea under ₹500'] --> B[Buyer Agent Orchestrator]
    B -->|1. GET /catalog & /agent-spec| C[Merchant API - FastAPI]
    B -->|2. Goal + Raw Catalog JSON| D[Gemini LLM Reasoner]
    D -->|3. Structured Choice JSON| B
    B -->|4. Submit Proposal| E[Guardrails Engine]
    E -->|5. Check Spending Cap & Unit Limits| F{Within Budget & Valid?}
    F -->|No| G[Block Action & Record Audit Log]
    F -->|Yes| H[Human / Code Gating Checkpoint]
    H -->|Rejected| I[Halt & Record Rejection Audit Log]
    H -->|Approved| J[Execute Checkout POST /checkout/create-order]
    J -->|6. Order Creation| K[Razorpay Test API]
    K -->|7. HMAC Payment Signature Verification| L[Merchant Stock Decremented]
    L -->|8. Log Complete Chain| M[(PostgreSQL / SQLite Audit Log)]
    J -->|On Stockout Error| N[Failure Recovery: Select Next Best In-Stock Fit]
```

---

## 📁 Repository Structure

```
Track1/
├── merchant_api/           # Merchant REST API (FastAPI)
│   ├── app.py              # Server endpoints (/catalog, /cart, /checkout, /agent-spec)
│   ├── catalog.py          # Seed catalog ("Aura Artisan Teas & Botanicals")
│   ├── models.py           # Pydantic request/response schemas
│   └── razorpay_client.py  # Razorpay SDK integration for test orders & payment signatures
├── guardrails/             # Security Circuit-Breaker & Gating Layer
│   ├── engine.py           # Hard spending cap & unit quantity validator
│   ├── gating.py           # Human-in-the-loop approval checkpoint (CLI & Auto modes)
│   └── audit.py            # Durable Audit Logger (SQLAlchemy DB models)
├── buyer_agent/            # Autonomous Buyer Agent
│   ├── agent.py            # Buyer agent core orchestrator & stockout recovery
│   ├── llm_reasoner.py     # Gemini LLM intent parsing & catalog reasoner
│   └── client.py           # Independent HTTP client for Merchant API
├── tests/                  # Automated integration test suite
│   ├── test_happy_path.py  # End-to-end successful purchase test
│   ├── test_guardrails.py # Spending cap breach rejection test
│   └── test_stockout.py    # Mid-checkout stockout recovery test
├── run_demo.py             # Rich CLI Interactive Demo Runner
├── requirements.txt        # Python package dependencies
└── README.md               # Architecture documentation & pitch talking points
```

---

## 🔒 How Guardrails & Gating Work

1. **Spending Cap Enforcer (`guardrails/engine.py`)**:
   - Enforces a deterministic code cap (e.g. `₹500.0` max single action).
   - If an LLM recommends an item exceeding the cap (e.g. Ceremonial Matcha for ₹950), the Guardrail Engine instantly blocks execution with `BLOCKED_GUARDRAIL`.
2. **Human-in-the-Loop Gating Checkpoint (`guardrails/gating.py`)**:
   - Intercepts all authorized purchase proposals before any Razorpay API calls are made.
   - Displays a review panel showing product name, category, origin, flavor notes, price, variant, and LLM reasoning.
   - Prompts for explicit approval (`[y/n]` in CLI mode).
3. **Durable Audit Trail (`guardrails/audit.py`)**:
   - Stores every transaction step in `agentic_commerce.db` (or PostgreSQL).
   - Logged fields: `session_id`, `step_type`, `agent_goal`, `llm_reasoning`, `spending_cap_inr`, `proposed_amount_inr`, `guardrail_passed`, `gate_status`, `razorpay_order_id`, `outcome_status`.

---

## ⚡ Failure Handling & Resiliency

1. **Mid-Purchase Stockout Recovery**:
   - If a product sells out between catalog browsing and checkout, the Merchant API returns `409 STOCKOUT_ERROR`.
   - The Buyer Agent catches the error, logs `STOCKOUT_RECOVERED`, excludes the depleted item, queries the catalog again for the next best matching item under budget, and completes checkout gracefully.
2. **Razorpay Payment Verification Failure**:
   - If payment signature verification fails or a decline occurs, the system logs `PAYMENT_FAILED` without crashing or hanging.

---

## 🚀 Quickstart & Running the Demo

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file (or use existing):
```ini
GEMINI_API_KEY=your_gemini_api_key
RAZORPAY_KEY_ID=rzp_test_TUF4spVuaFk2g5
RAZORPAY_KEY_SECRET=sr5phj3GIj2gWBIRTmunq8Nh
DATABASE_URL=sqlite:///./agentic_commerce.db
SPENDING_CAP_INR=500.0
GATING_MODE=CLI
```

### 3. Launch Interactive CLI Demo
```bash
python run_demo.py
```
The CLI will display the **Merchant Catalog**, **Agent Spec Discovery**, prompt for a demo scenario, render the **Gating Panel**, issue a real **Razorpay Test Order**, and output the **Audit Trail**.

### 4. Run Automated Test Suite
```bash
python -m pytest tests/
```

---

## 📽️ Pitch Video Talking Points (5-Minute Video Script)

1. **The Vision (0:00 - 1:00)**:
   - *"Most AI commerce projects build a chatbot for humans. We built a machine-transactable merchant and an independent AI agent that can buy products safely without human intervention."*
2. **Agent-Readable API (`/agent-spec`) (1:00 - 2:00)**:
   - *"Our merchant API exposes `/agent-spec` which tells autonomous agents currency standards (INR), pricing units, stock reservation limits, and required security gates."*
3. **The Differentiator: Guardrails & Gating (2:00 - 3:15)**:
   - *"LLMs are great at reasoning, but terrible at holding financial state. We strictly confine the Gemini LLM to intent parsing. The actual payment call can ONLY happen if code-level spending caps pass and explicit clearance is granted at our Gating Checkpoint."*
4. **Real Problem Hit During Build & Solution (3:15 - 4:00)**:
   - **Problem Encountered**: *"During testing, if a product sold out between catalog selection and checkout, the LLM initially got stuck repeating the same invalid order call."*
   - **Fix Implemented**: *"We engineered an automatic stockout fallback loop in `buyer_agent/agent.py`. When the API returns a 409 stockout error, the agent logs `STOCKOUT_RECOVERED`, excludes the depleted item, re-runs catalog reasoning for the next best in-stock alternative under budget, and completes the purchase."*
5. **Razorpay Test Order & Audit Trail (4:00 - 5:00)**:
   - *"Demonstrate `run_demo.py` showing real Razorpay Order creation (`rzp_test_...`), payment signature verification, and the durable SQL audit log."*
