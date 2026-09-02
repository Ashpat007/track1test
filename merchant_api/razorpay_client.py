"""
Razorpay Integration Client for Order Creation and Payment Verification (Test Mode).
Communicates with Razorpay Test Mode API for order creation.
"""

import os
import hmac
import hashlib
from typing import Optional
import razorpay
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


class RazorpayService:
    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        else:
            self.client = None

    def create_order(self, amount_inr: float, receipt_id: str, notes: dict = None) -> dict:
        """
        Creates an order in Razorpay Test Mode via REST API.
        Amount must be in paise (1 INR = 100 Paise).
        """
        amount_paise = int(round(amount_inr * 100))
        data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt_id,
            "notes": notes or {"created_by": "Agentic Commerce Pipeline"}
        }
        
        try:
            rzp_order = self.client.order.create(data=data)
            return {
                "success": True,
                "is_simulated_fallback": False,
                "razorpay_order_id": rzp_order["id"],
                "amount": rzp_order["amount"],
                "currency": rzp_order["currency"],
                "status": rzp_order["status"],
                "raw": rzp_order
            }
        except Exception as e:
            # Explicitly log fallback mock order if real API call fails
            fake_rzp_id = f"order_mock_{receipt_id[:8]}"
            print(f"[Razorpay API Notice] Real Order API call failed ({e}). Flagging MOCKED_FALLBACK.")
            return {
                "success": False,
                "is_simulated_fallback": True,
                "error": str(e),
                "razorpay_order_id": fake_rzp_id,
                "amount": amount_paise,
                "currency": "INR",
                "status": "MOCKED_FALLBACK"
            }

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Verifies Razorpay HMAC SHA256 test payment signature.
        """
        key_sec = self.key_secret or os.getenv("RAZORPAY_KEY_SECRET") or "dummy_secret_for_test_signature"
        generated_signature = hmac.new(
            bytes(key_sec, 'utf-8'),
            bytes(f"{razorpay_order_id}|{razorpay_payment_id}", 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(generated_signature, razorpay_signature)
