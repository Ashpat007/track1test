"""
Automated Integration Test: Multi-Merchant Federated Commerce & Cross-Store Stockout Recovery.
Verifies that when Store A stock is depleted (0 units), the agent automatically executes a federated purchase on Store B (Botanical Leaf Co.).
"""

import sys
import os
import time
import threading
import uvicorn
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from merchant_api.app import app as merchant_app, CATALOG_DB
from buyer_agent.agent import BuyerAgent
from buyer_agent.client import MerchantClient

SERVER_PORT = 8004
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
    # Restore stock
    CATALOG_DB["tea-001"]["stock_qty"] = 15


def test_federated_cross_merchant_stockout_failover():
    client = MerchantClient(base_url=SERVER_URL)
    # Simulate Store A Kashmiri Kahwa stockout
    client.simulate_stockout("tea-001")

    try:
        agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=500.0, gating_mode="AUTO_APPROVE")
        goal = "Buy Kashmiri Kahwa Saffron Blend"

        res = agent.execute_purchase_goal(goal)

        assert res["success"] is True
        assert res["status"] == "SUCCESS"
        assert res["federated_failover"] is True
        assert res["store_name"] == "Botanical Leaf Co. (Store B)"
        assert "Kashmiri Kahwa" in res["summary_names"]
        assert res["amount_inr"] == 360.0
        assert res["razorpay_order_id"].startswith("order_") or res["razorpay_order_id"].startswith("ord_")
    finally:
        CATALOG_DB["tea-001"]["stock_qty"] = 15
