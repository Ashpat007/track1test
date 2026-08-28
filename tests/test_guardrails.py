"""
Automated Integration Test Suite: Guardrails, Stock Reservation, Kill Switch & Idempotency.
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
from buyer_agent.client import MerchantClient
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
    res1 = engine.evaluate_proposal(
        product_id="tea-001",
        product_name="Kahwa",
        total_amount_inr=400.0,
        quantity=1,
        current_session_spent_inr=0.0
    )
    assert res1.passed is True

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
    agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=500.0, gating_mode="AUTO_APPROVE")
    agent.guardrail_engine.max_session_spend_inr = 600.0

    res1 = agent.execute_purchase_goal("Buy 1 Kahwa")
    assert res1["success"] is True
    assert agent.session_spent_inr == 420.0

    res2 = agent.execute_purchase_goal("Buy 1 Chamomile")
    assert res2["success"] is False
    assert res2["status"] == "BLOCKED_GUARDRAIL"
    assert "exceeds session cap of ₹" in res2["reason"]

def test_cart_stock_reservation_and_expiration():
    client = MerchantClient(base_url=SERVER_URL)
    cat_before = client.get_catalog()
    tea1_stock_before = next(p["stock_qty"] for p in cat_before["products"] if p["id"] == "tea-001")

    # Reserve 2 units in cart
    cart_res = client.create_cart([{"product_id": "tea-001", "quantity": 2}])
    assert cart_res["is_valid_for_checkout"] is True
    cart_id = cart_res["cart_id"]

    # Verify catalog unreserved stock decreased by 2
    cat_during = client.get_catalog()
    tea1_stock_during = next(p["stock_qty"] for p in cat_during["products"] if p["id"] == "tea-001")
    assert tea1_stock_during == tea1_stock_before - 2

    # Expire cart simulation
    import requests
    exp_res = requests.post(f"{SERVER_URL}/cart/{cart_id}/expire").json()
    assert exp_res["success"] is True

    # Verify reserved stock was released back to catalog
    cat_after = client.get_catalog()
    tea1_stock_after = next(p["stock_qty"] for p in cat_after["products"] if p["id"] == "tea-001")
    assert tea1_stock_after == tea1_stock_before

def test_global_emergency_halt_kill_switch():
    import requests
    # Halt system
    halt_res = requests.post(f"{SERVER_URL}/api/agent-halt").json()
    assert halt_res["halted"] is True

    # Attempt cart creation -> Should return 503 Emergency Halt
    cart_req = requests.post(f"{SERVER_URL}/cart", json={"items": [{"product_id": "tea-001", "quantity": 1}]})
    assert cart_req.status_code == 503
    assert "EMERGENCY_SYSTEM_HALT" in cart_req.json()["detail"]

    # Resume system
    resume_res = requests.post(f"{SERVER_URL}/api/agent-resume").json()
    assert resume_res["halted"] is False

    # Verify normal operations restored
    cart_req2 = requests.post(f"{SERVER_URL}/cart", json={"items": [{"product_id": "tea-001", "quantity": 1}]})
    assert cart_req2.status_code == 200

def test_checkout_idempotency_protection():
    client = MerchantClient(base_url=SERVER_URL)
    cart = client.create_cart([{"product_id": "tea-002", "quantity": 1}])
    cart_id = cart["cart_id"]

    idemp_key = f"idemp_test_{time.time()}"

    # First checkout call
    order1 = client.create_checkout_order(cart_id=cart_id, buyer_name="Agent 1")
    
    # Second checkout call with same cart / idempotency key via direct requests
    import requests
    resp1 = requests.post(f"{SERVER_URL}/checkout/create-order", json={"cart_id": cart_id, "buyer_name": "Agent 1", "idempotency_key": idemp_key}).json()
    resp2 = requests.post(f"{SERVER_URL}/checkout/create-order", json={"cart_id": cart_id, "buyer_name": "Agent 1", "idempotency_key": idemp_key}).json()

    assert resp1["order_id"] == resp2["order_id"]
    assert resp1["razorpay_order_id"] == resp2["razorpay_order_id"]
