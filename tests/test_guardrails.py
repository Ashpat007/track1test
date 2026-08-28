"""
Automated Integration Test: Guardrails Spending Cap & Cumulative Session Spend Enforcement.
"""

import sys
import os
import time
import threading
import uvicorn
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from merchant_api.app import app as merchant_app
from buyer_agent.agent import BuyerAgent
from guardrails.engine import GuardrailEngine

SERVER_PORT = 8002
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"

@pytest.fixture(scope="module", autouse=True)
def merchant_server():
    config = uvicorn.Config(merchant_app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5)
    yield
    server.should_exit = True

def test_guardrail_engine_direct_spending_cap_breach():
    engine = GuardrailEngine(max_single_action_inr=300.0)
    res = engine.evaluate_proposal(
        product_id="tea-005",
        product_name="Japanese Ceremonial Matcha Grade-A",
        total_amount_inr=950.0,
        quantity=1,
        currency="INR"
    )
    
    assert res.passed is False
    assert "exceeds single action spending cap" in res.rejection_reason

def test_cumulative_session_spend_engine():
    engine = GuardrailEngine(max_single_action_inr=500.0, max_session_spend_inr=600.0)
    # First purchase under budget (₹400)
    res1 = engine.evaluate_proposal(
        product_id="tea-001",
        product_name="Kahwa",
        total_amount_inr=400.0,
        quantity=1,
        current_session_spent_inr=0.0
    )
    assert res1.passed is True

    # Second purchase (₹300), bringing cumulative spend to ₹700 (exceeds ₹600 cap)
    res2 = engine.evaluate_proposal(
        product_id="tea-002",
        product_name="Chamomile",
        total_amount_inr=300.0,
        quantity=1,
        current_session_spent_inr=400.0
    )
    assert res2.passed is False
    assert "exceeds session cap of ₹" in res2.rejection_reason

def test_agent_cumulative_session_spend_integration():
    """
    Integration Test: Asserts that BuyerAgent instance accumulates spend across consecutive purchase calls
    and blocks the second purchase when cumulative spend breaches session cap.
    """
    agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=500.0, gating_mode="AUTO_APPROVE")
    agent.guardrail_engine.max_session_spend_inr = 600.0

    # 1st purchase: 1x Kahwa (₹420.0) -> Passes
    res1 = agent.execute_purchase_goal("Buy 1 Kahwa")
    assert res1["success"] is True
    assert agent.session_spent_inr == 420.0

    # 2nd purchase in same session instance: 1x Chamomile (₹380.0) -> Projected total = ₹800.0 (exceeds ₹600 cap)
    res2 = agent.execute_purchase_goal("Buy 1 Chamomile")
    assert res2["success"] is False
    assert res2["status"] == "BLOCKED_GUARDRAIL"
    assert "exceeds session cap of ₹" in res2["reason"]

def test_agent_spending_cap_breach():
    agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=100.0, gating_mode="AUTO_APPROVE")
    goal = "Buy any tea"
    
    res = agent.execute_purchase_goal(goal)
    
    assert res["success"] is False
    assert res["status"] in ["BLOCKED_GUARDRAIL", "REASONING_FAILED", "INVALID_SELECTION"]
