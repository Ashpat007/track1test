"""
Razorpay Integration Client for Order Creation and Payment Verification (Test Mode).
"""

import os
import hmac
import hashlib
import razorpay
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TUF4spVuaFk2g5")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "sr5phj3GIj2gWBIRTmunq8Nh")

class RazorpayService:
    def __init__(self, key_id: str = RAZORPAY_KEY_ID, key_secret: str = RAZORPAY_KEY_SECRET):
        self.key_id = key_id
        self.key_secret = key_secret
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount_inr: float, receipt_id: str, notes: dict = None) -> dict:
        """
        Creates an order in Razorpay Test Mode.
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
                "razorpay_order_id": rzp_order["id"],
                "amount": rzp_order["amount"],
                "currency": rzp_order["currency"],
                "status": rzp_order["status"],
                "raw": rzp_order
            }
        except Exception as e:
            # Fallback for offline/test simulation if credentials hit network issue
            fake_rzp_id = f"order_mock_{receipt_id[:8]}"
            return {
                "success": False,
                "error": str(e),
                "razorpay_order_id": fake_rzp_id,
                "amount": amount_paise,
                "currency": "INR",
                "status": "created"
            }

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Verifies the HMAC SHA256 signature returned by Razorpay.
        """
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception:
            # Manual calculation fallback
            generated_signature = hmac.new(
                bytes(self.key_secret, 'utf-8'),
                bytes(f"{razorpay_order_id}|{razorpay_payment_id}", 'utf-8'),
                hashlib.sha256
            ).hexdigest()
            return generated_signature == razorpay_signature
