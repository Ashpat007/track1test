"""
Independent Merchant API HTTP Client.
Interacts with Merchant A (Aura Artisan Teas) and Federated Merchant B (Botanical Leaf Co.) over REST APIs.
"""

import requests
from typing import Dict, Any, Optional

class MerchantClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def get_agent_spec(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/agent-spec", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def get_catalog(
        self,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = True,
        tag: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"in_stock_only": str(in_stock_only).lower()}
        if category:
            params["category"] = category
        if max_price is not None:
            params["max_price"] = max_price
        if tag:
            params["tag"] = tag

        resp = requests.get(f"{self.base_url}/catalog", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def get_product(self, product_id: str) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/catalog/{product_id}", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def create_cart(self, items: list) -> Dict[str, Any]:
        payload = {"items": items}
        resp = requests.post(f"{self.base_url}/cart", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def create_checkout_order(self, cart_id: str, buyer_name: str = "AI Buyer Agent") -> Dict[str, Any]:
        payload = {"cart_id": cart_id, "buyer_name": buyer_name}
        resp = requests.post(f"{self.base_url}/checkout/create-order", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def verify_payment(self, order_id: str, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> Dict[str, Any]:
        payload = {
            "order_id": order_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }
        resp = requests.post(f"{self.base_url}/checkout/verify-payment", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def simulate_stockout(self, product_id: str, variant_id: Optional[str] = None) -> Dict[str, Any]:
        params = {"product_id": product_id}
        if variant_id:
            params["variant_id"] = variant_id
        resp = requests.post(f"{self.base_url}/simulate-stockout", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()

    # --- Federated Merchant B (Botanical Leaf Co.) Methods ---

    def get_merchant_b_catalog(self, in_stock_only: bool = True) -> Dict[str, Any]:
        params = {"in_stock_only": str(in_stock_only).lower()}
        resp = requests.get(f"{self.base_url}/merchant-b/catalog", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def create_merchant_b_cart(self, items: list) -> Dict[str, Any]:
        payload = {"items": items}
        resp = requests.post(f"{self.base_url}/merchant-b/cart", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def create_merchant_b_checkout_order(self, cart_id: str, buyer_name: str = "AI Buyer Agent") -> Dict[str, Any]:
        payload = {"cart_id": cart_id, "buyer_name": buyer_name}
        resp = requests.post(f"{self.base_url}/merchant-b/checkout/create-order", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def verify_merchant_b_payment(self, order_id: str, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> Dict[str, Any]:
        payload = {
            "order_id": order_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }
        resp = requests.post(f"{self.base_url}/merchant-b/checkout/verify-payment", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
