"""
Automated Integration Test: Happy Path Purchase Flow.
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

SERVER_PORT = 8001
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

def test_happy_path_purchase():
    agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=500.0, gating_mode="AUTO_APPROVE")
    goal = "Get a caffeine-free tea under ₹500"
    
    res = agent.execute_purchase_goal(goal)
    
    assert res["success"] is True
    assert res["status"] == "SUCCESS"
    assert res["amount_inr"] <= 500.0
    assert "razorpay_order_id" in res
    assert "razorpay_payment_id" in res
