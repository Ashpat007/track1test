"""
Streamlit Visual Web Dashboard for Razorpay Buildathon Track 01 Submission.
Features: Interactive Agent-Readable Catalog, Agent Spec Discovery, Conversational Shopping Chatbot with Catalog RAG,
Live Human Gating Checkpoint, Razorpay Payment Success Animation, Real-Time Stock Updates, and SQL Audit Log Inspector.
"""

import sys
import os
import re
import time
import threading
import uvicorn
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from merchant_api.app import app as merchant_app, CATALOG_DB
from buyer_agent.agent import BuyerAgent
from buyer_agent.client import MerchantClient
from guardrails.audit import AuditLogger, SessionLocal, AuditLogRecord

SERVER_PORT = 8000
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"


@st.cache_resource
def start_merchant_server():
    """Starts FastAPI merchant server once in background."""
    config = uvicorn.Config(merchant_app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5)
    return True


start_merchant_server()

st.set_page_config(
    page_title="Agentic Commerce — Razorpay Buildathon Track 01",
    page_icon="🍵",
    layout="wide"
)

# Custom CSS for Razorpay Payment Success Card
st.markdown("""
<style>
.razorpay-success-card {
    background: #0b192c;
    border: 2px solid #00baf2;
    border-radius: 14px;
    padding: 24px;
    text-align: center;
    color: #ffffff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    box-shadow: 0 12px 32px rgba(0, 186, 242, 0.25);
    margin-top: 15px;
    margin-bottom: 25px;
}
.razorpay-checkmark-circle {
    width: 72px;
    height: 72px;
    background: #10b981;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px auto;
    box-shadow: 0 0 24px rgba(16, 185, 129, 0.6);
    animation: pop 0.4s ease-in-out;
}
.razorpay-checkmark {
    color: #ffffff;
    font-size: 36px;
    font-weight: bold;
}
.razorpay-badge {
    background: rgba(0, 186, 242, 0.15);
    border: 1px solid #00baf2;
    color: #00baf2;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    display: inline-block;
    margin-bottom: 12px;
}
@keyframes pop {
    0% { transform: scale(0.5); opacity: 0; }
    80% { transform: scale(1.15); }
    100% { transform: scale(1); opacity: 1; }
}
</style>
""", unsafe_allow_html=True)


st.title("🍵 Aura Artisan Teas & Botanicals")
st.subheader("Agent-Readable Commerce API & Machine-to-Machine Bounded Payments")
st.caption("Razorpay AI Buildathon — Track 01: AI Growth & Agentic Commerce")

tab1, tab2, tab3 = st.tabs(["🏪 Agent-Readable Catalog", "💬 Conversational Buyer Chatbot", "📋 Durable SQL Audit Trail"])

# --- TAB 1: Merchant Catalog & Agent Spec ---
with tab1:
    st.markdown("### Agent-Readable Product Catalog (`GET /catalog`)")
    st.caption("Structured JSON dataset consumed directly by autonomous AI buyer agents for reasoning.")
    cols = st.columns(4)
    
    for idx, (p_id, p) in enumerate(CATALOG_DB.items()):
        with cols[idx % 4]:
            st.info(f"**{p['name']}** (`{p['id']}`)")
            st.write(f"**Category:** {p['category']}")
            st.write(f"**Base Price:** ₹{p['price_inr']:.2f}")
            
            if p['stock_qty'] > 0:
                st.markdown(f"**Stock Level:** :green[{p['stock_qty']} in stock]")
            else:
                st.markdown(f"**Stock Level:** :red[0 OUT OF STOCK]")

            st.write(f"**Caffeine:** {p['attributes'].get('caffeine_level', 'N/A')}")
            st.write(f"**Flavors:** {', '.join(p['attributes'].get('flavor_notes', []))}")
            st.write(f"**Tags:** `{', '.join(p['tags'])}`")
            st.divider()

    st.markdown("### Agent API Metadata Discovery (`GET /agent-spec`)")
    if st.button("Fetch Agent Spec"):
        client = MerchantClient(base_url=SERVER_URL)
        try:
            spec = client.get_agent_spec()
            st.json(spec)
        except Exception as e:
            st.error(f"Failed to reach server: {e}")

# --- TAB 2: Conversational Shopping Chatbot + RAG + Razorpay Success ---
with tab2:
    st.markdown("### 💬 Conversational Shopping Assistant & Autonomous Agent")
    st.caption("Ask questions about the catalog or instruct the agent to make a purchase under a spending cap.")

    col_config, col_chat = st.columns([1, 2.5])

    with col_config:
        st.markdown("#### 🛡️ Agent Security Guardrails")
        spending_cap_input = st.number_input(
            "Max Spending Limit (₹ INR)",
            min_value=100.0,
            max_value=10000.0,
            value=2000.0,
            step=100.0
        )
        gating_mode = st.radio("Gating Mode", ["Human Review Gate", "Auto Approve"], index=0)
        
        st.markdown("#### 💡 Quick Prompts")
        if st.button("What teas do you have for sleep?"):
            st.session_state.preset_prompt = "What teas do you have for sleep?"
        if st.button("Buy 1 Kahwa and 1 Darjeeling"):
            st.session_state.preset_prompt = "Buy 1 Kahwa and 1 Darjeeling"
        if st.button("Buy 2 Masala Chai and 1 Matcha"):
            st.session_state.preset_prompt = "Buy 2 Masala Chai and 1 Matcha"

    with col_chat:
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Welcome to Aura Artisan Teas! I am your AI Buyer Agent. Ask me about our teas or tell me what to purchase under your budget!"}
            ]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "razorpay_data" in msg:
                    rzp = msg["razorpay_data"]
                    st.markdown(f"""
                    <div class="razorpay-success-card">
                        <div class="razorpay-badge">RAZORPAY TEST PAYMENT CAPTURED</div>
                        <div class="razorpay-checkmark-circle">
                            <span class="razorpay-checkmark">✓</span>
                        </div>
                        <h3 style="color: #00baf2; margin-bottom: 4px;">Order Confirmed!</h3>
                        <p style="font-size: 20px; font-weight: bold; color: #10b981; margin-bottom: 12px;">₹{rzp['amount']:.2f} Paid</p>
                        <p style="font-size: 13px; color: #94a3b8; margin: 2px 0;"><strong>Razorpay Order ID:</strong> {rzp['order_id']}</p>
                        <p style="font-size: 13px; color: #94a3b8; margin: 2px 0;"><strong>Razorpay Payment ID:</strong> {rzp['payment_id']}</p>
                        <p style="font-size: 13px; color: #94a3b8; margin: 2px 0;"><strong>Items Purchased:</strong> {rzp['items']}</p>
                        <p style="font-size: 12px; color: #64748b; margin-top: 10px;">Merchant: Aura Artisan Teas & Botanicals</p>
                    </div>
                    """, unsafe_allow_html=True)

        user_prompt = st.chat_input("Ask a question or enter a purchase goal...")
        if getattr(st.session_state, "preset_prompt", None):
            user_prompt = st.session_state.preset_prompt
            st.session_state.preset_prompt = None

        if user_prompt:
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.write(user_prompt)

            prompt_lower = user_prompt.lower()
            is_buy_intent = any(k in prompt_lower for k in ["buy", "get", "purchase", "order", "need"])

            if is_buy_intent:
                agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=spending_cap_input, gating_mode="AUTO_APPROVE")

                with st.chat_message("assistant"):
                    if gating_mode == "Human Review Gate":
                        with st.spinner("Agent evaluating catalog & security guardrails..."):
                            catalog_data = agent.client.get_catalog(in_stock_only=True)
                            products = catalog_data.get("products", [])
                            choice = agent.llm_reasoner.select_product_for_goal(user_prompt, products, spending_cap_input)

                        total_amount = sum([item.quantity * CATALOG_DB[item.product_id]["price_inr"] for item in choice.items if item.product_id in CATALOG_DB])
                        summary_names = ", ".join([f"{i.quantity}x {CATALOG_DB[i.product_id]['name']}" for i in choice.items if i.product_id in CATALOG_DB])

                        eval_res = agent.guardrail_engine.evaluate_proposal(
                            product_id=choice.items[0].product_id if choice.items else "none",
                            product_name=summary_names if summary_names else user_prompt,
                            total_amount_inr=total_amount,
                            quantity=sum([i.quantity for i in choice.items]),
                            currency="INR",
                            current_session_spent_inr=agent.session_spent_inr
                        )

                        if not eval_res.passed or not choice.items:
                            reply = f"⛔ **GUARDRAIL BLOCKED TRANSACTION:** {eval_res.rejection_reason if not eval_res.passed else choice.reasoning}"
                            st.error(reply)
                            st.session_state.messages.append({"role": "assistant", "content": reply})
                        else:
                            st.warning("🛑 **HUMAN REVIEW GATING CHECKPOINT — CLEARANCE REQUIRED**")
                            st.info(f"**Selected Items:** {summary_names}\n\n**Total Amount:** ₹{total_amount:.2f} (Cap: ₹{spending_cap_input:.2f})\n\n**LLM Reasoning:** {choice.reasoning}")
                            
                            if choice.stock_warnings:
                                for w in choice.stock_warnings:
                                    st.warning(w)

                            col_approve, col_reject = st.columns(2)
                            if col_approve.button("✅ Approve & Execute Payment", key="btn_approve"):
                                res = agent.execute_preapproved_choice(choice=choice, agent_goal=user_prompt)
                                if res.get("success"):
                                    st.balloons()
                                    bot_reply = f"✅ **Purchase Completed!** Purchased **{res.get('summary_names')}** for **₹{res['amount_inr']:.2f}** under your ₹{spending_cap_input:.2f} cap."
                                    st.success(bot_reply)
                                    rzp_data = {
                                        "amount": res['amount_inr'],
                                        "order_id": res.get('razorpay_order_id'),
                                        "payment_id": res.get('razorpay_payment_id'),
                                        "items": res.get('summary_names')
                                    }
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": bot_reply,
                                        "razorpay_data": rzp_data
                                    })
                            if col_reject.button("❌ Deny / Reject Payment", key="btn_reject"):
                                reply = "⛔ **Action Denied:** User rejected gating clearance."
                                st.error(reply)
                                st.session_state.messages.append({"role": "assistant", "content": reply})
                    else:
                        with st.spinner("Agent executing purchase goal..."):
                            res = agent.execute_purchase_goal(user_prompt)

                        if res.get("success"):
                            st.balloons()
                            bot_reply = f"✅ **Purchase Completed!** Purchased **{res.get('summary_names')}** for **₹{res['amount_inr']:.2f}** under your ₹{spending_cap_input:.2f} cap. Remaining balance: **₹{res['remaining_balance_inr']:.2f}**."
                            st.write(bot_reply)

                            rzp_data = {
                                "amount": res['amount_inr'],
                                "order_id": res.get('razorpay_order_id'),
                                "payment_id": res.get('razorpay_payment_id'),
                                "items": res.get('summary_names')
                            }

                            st.markdown(f"""
                            <div class="razorpay-success-card">
                                <div class="razorpay-badge">RAZORPAY TEST PAYMENT CAPTURED</div>
                                <div class="razorpay-checkmark-circle">
                                    <span class="razorpay-checkmark">✓</span>
                                </div>
                                <h3 style="color: #00baf2; margin-bottom: 4px;">Order Confirmed!</h3>
                                <p style="font-size: 20px; font-weight: bold; color: #10b981; margin-bottom: 12px;">₹{rzp_data['amount']:.2f} Paid</p>
                                <p style="font-size: 13px; color: #94a3b8; margin: 2px 0;"><strong>Razorpay Order ID:</strong> {rzp_data['order_id']}</p>
                                <p style="font-size: 13px; color: #94a3b8; margin: 2px 0;"><strong>Razorpay Payment ID:</strong> {rzp_data['payment_id']}</p>
                                <p style="font-size: 13px; color: #94a3b8; margin: 2px 0;"><strong>Items Purchased:</strong> {rzp_data['items']}</p>
                                <p style="font-size: 12px; color: #64748b; margin-top: 10px;">Merchant: Aura Artisan Teas & Botanicals</p>
                            </div>
                            """, unsafe_allow_html=True)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": bot_reply,
                                "razorpay_data": rzp_data
                            })
                        else:
                            reply = f"⛔ **Action Blocked / Failed:** {res.get('reason') or res.get('message')}"
                            st.write(reply)
                            st.session_state.messages.append({"role": "assistant", "content": reply})

            else:
                matched_products = []
                for p in CATALOG_DB.values():
                    keywords = [p["name"].lower(), p["category"].lower()] + [t.lower() for t in p.get("tags", [])]
                    if any(kw in prompt_lower for kw in keywords) or "all" in prompt_lower or "tea" in prompt_lower:
                        matched_products.append(p)

                with st.chat_message("assistant"):
                    if matched_products:
                        reply = f"Here are the matching teas from our catalog:\n\n"
                        for p in matched_products[:4]:
                            reply += f"• **{p['name']}** (`{p['id']}`) — **₹{p['price_inr']:.2f}** ({p['category']}, {p['attributes'].get('caffeine_level', 'N/A')} caffeine, **{p['stock_qty']} in stock**)\n  *Flavors:* {', '.join(p['attributes'].get('flavor_notes', []))}\n\n"
                        reply += "\nTo purchase any of these, simply say *'Buy 1 Kahwa'* or *'Order tea-001 and tea-003'*!"
                    else:
                        reply = "We offer artisanal teas including Kashmiri Kahwa, Himalayan Chamomile, Imperial Darjeeling, Masala Chai, Ceremonial Matcha, Tulsi Ginger, and Saffron. Let me know what you'd like to explore or buy!"

                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- TAB 3: SQL Audit Trail ---
with tab3:
    c_head, c_btn = st.columns([3, 1])
    c_head.markdown("### Durable SQL Audit Log Inspector")
    if c_btn.button("🗑️ Reset Audit Log Database"):
        db = SessionLocal()
        try:
            cnt = db.query(AuditLogRecord).delete()
            db.commit()
            st.success(f"Cleared {cnt} audit records!")
        finally:
            db.close()

    db = SessionLocal()
    try:
        records = db.query(AuditLogRecord).order_by(AuditLogRecord.id.desc()).all()
        if records:
            data = []
            for r in records:
                data.append({
                    "ID": r.id,
                    "Timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "",
                    "Session ID": r.session_id,
                    "Step Type": r.step_type,
                    "Action / Details": r.proposed_action or r.guardrail_message,
                    "Guardrail": "PASS" if r.guardrail_passed else "BLOCKED",
                    "Gate": r.gate_status,
                    "Razorpay Order ID": r.razorpay_order_id,
                    "Outcome": r.outcome_status
                })
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.info("Database is clean. 0 audit records.")
    finally:
        db.close()
