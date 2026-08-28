"""
Pydantic and SQLAlchemy Data Models for Merchant Catalog, Cart, and Checkout.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Pydantic Schemas for API Requests/Responses ---

class VariantSchema(BaseModel):
    id: str
    name: str
    price_modifier_inr: float = 0.0
    stock_qty: int

class ProductSchema(BaseModel):
    id: str
    name: str
    category: str
    price_inr: float
    stock_qty: int
    description: str
    image_url: Optional[str] = None
    tags: List[str]
    attributes: Dict[str, Any]
    variants: List[VariantSchema] = []

class CatalogResponse(BaseModel):
    merchant_name: str = "Aura Artisan Teas & Botanicals"
    currency: str = "INR"
    total_products: int
    products: List[ProductSchema]

class CartItemInput(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(gt=0, default=1)

class CartCreateInput(BaseModel):
    items: List[CartItemInput]

class CartItemDetail(BaseModel):
    product_id: str
    product_name: str
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    unit_price_inr: float
    quantity: int
    subtotal_inr: float

class CartResponse(BaseModel):
    cart_id: str
    items: List[CartItemDetail]
    total_amount_inr: float
    currency: str = "INR"
    is_valid_for_checkout: bool
    validation_message: str
    created_at_timestamp: Optional[float] = None
    expires_at_timestamp: Optional[float] = None

class CheckoutCreateOrderInput(BaseModel):
    cart_id: str
    buyer_name: str = "AI Buyer Agent"
    idempotency_key: Optional[str] = None
    delivery_notes: Optional[str] = None

class CheckoutOrderResponse(BaseModel):
    order_id: str
    razorpay_order_id: str
    amount_inr: float
    amount_paise: int
    currency: str = "INR"
    status: str
    items: List[CartItemDetail]
    idempotency_key: Optional[str] = None

class PaymentVerificationInput(BaseModel):
    order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentVerificationResponse(BaseModel):
    success: bool
    order_id: str
    status: str
    message: str

class AgentSpecResponse(BaseModel):
    api_version: str = "1.0.0"
    merchant_name: str = "Aura Artisan Teas & Botanicals"
    agent_readability: str = "FULL_DECISION_BOUNDED"
    supported_actions: List[str] = [
        "GET /catalog", "GET /agent-spec", "POST /cart", "POST /cart/{cart_id}/expire",
        "POST /checkout/create-order", "POST /checkout/verify-payment",
        "POST /api/agent-halt", "POST /api/agent-resume", "GET /api/agent-status"
    ]
    currency: str = "INR"
    price_unit: str = "RUPEES"
    stock_reservation_minutes: int = 15
    gating_required: bool = True
    idempotency_supported: bool = True
    kill_switch_enabled: bool = True
