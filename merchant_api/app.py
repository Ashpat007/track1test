"""
FastAPI Server for Merchant API ("Aura Artisan Teas & Botanicals").
Exposes agent-readable catalog, cart management, Razorpay order checkout, payment verification, and custom web dashboard.
"""

import os
import uuid
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from merchant_api.catalog import INITIAL_CATALOG
from merchant_api.models import (
    CatalogResponse, ProductSchema, VariantSchema, CartCreateInput, CartResponse,
    CartItemDetail, CheckoutCreateOrderInput, CheckoutOrderResponse,
    PaymentVerificationInput, PaymentVerificationResponse, AgentSpecResponse
)
from merchant_api.razorpay_client import RazorpayService
from buyer_agent.agent import BuyerAgent
from buyer_agent.llm_reasoner import LLMReasoner
from guardrails.audit import SessionLocal, AuditLogRecord

app = FastAPI(
    title="Aura Artisan Teas - Merchant Agentic API",
    description="Agent-Readable Commerce API for browsing catalog, managing cart, and initiating Razorpay test checkouts.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATALOG_DB: Dict[str, dict] = {item["id"]: item.copy() for item in INITIAL_CATALOG}
CARTS_DB: Dict[str, dict] = {}
ORDERS_DB: Dict[str, dict] = {}
PENDING_PROPOSALS: Dict[str, dict] = {}

razorpay_service = RazorpayService()


@app.get("/", response_class=HTMLResponse, tags=["Web Dashboard"])
def serve_dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Aura Artisan Teas Merchant API</h1>")


@app.get("/agent-spec", response_model=AgentSpecResponse, tags=["Agent Metadata"])
def get_agent_spec():
    return AgentSpecResponse()


@app.get("/catalog", response_model=CatalogResponse, tags=["Catalog"])
def get_catalog(
    category: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    in_stock_only: bool = Query(True),
    tag: Optional[str] = Query(None)
):
    filtered = []
    for item in CATALOG_DB.values():
        if category and item["category"].lower() != category.lower():
            continue
        if max_price is not None and item["price_inr"] > max_price:
            continue
        if in_stock_only and item["stock_qty"] <= 0:
            continue
        if tag and tag.lower() not in [t.lower() for t in item["tags"]]:
            continue
        filtered.append(ProductSchema(**item))

    return CatalogResponse(total_products=len(filtered), products=filtered)


@app.get("/catalog/{product_id}", response_model=ProductSchema, tags=["Catalog"])
def get_product(product_id: str):
    if product_id not in CATALOG_DB:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return ProductSchema(**CATALOG_DB[product_id])


@app.post("/cart", response_model=CartResponse, tags=["Cart"])
def create_or_update_cart(payload: CartCreateInput):
    cart_id = f"cart_{uuid.uuid4().hex[:8]}"
    item_details: List[CartItemDetail] = []
    total_amount = 0.0
    is_valid = True
    validation_msgs = []

    for entry in payload.items:
        p_id = entry.product_id
        if p_id not in CATALOG_DB:
            is_valid = False
            validation_msgs.append(f"Product ID '{p_id}' does not exist.")
            continue
        
        product = CATALOG_DB[p_id]
        unit_price = product["price_inr"]
        variant_name = None

        if entry.variant_id:
            variant_match = next((v for v in product.get("variants", []) if v["id"] == entry.variant_id), None)
            if not variant_match:
                is_valid = False
                validation_msgs.append(f"Variant '{entry.variant_id}' not found for product '{p_id}'.")
                continue
            unit_price += variant_match["price_modifier_inr"]
            variant_name = variant_match["name"]
            
            if variant_match["stock_qty"] < entry.quantity:
                is_valid = False
                validation_msgs.append(f"Insufficient stock for variant '{variant_name}'.")
        else:
            if product["stock_qty"] < entry.quantity:
                is_valid = False
                validation_msgs.append(f"Insufficient stock for product '{product['name']}'.")

        subtotal = unit_price * entry.quantity
        total_amount += subtotal

        item_details.append(CartItemDetail(
            product_id=p_id,
            product_name=product["name"],
            variant_id=entry.variant_id,
            variant_name=variant_name,
            unit_price_inr=unit_price,
            quantity=entry.quantity,
            subtotal_inr=subtotal
        ))

    msg = "Cart valid and ready for checkout." if is_valid else "; ".join(validation_msgs)
    
    cart_data = {
        "cart_id": cart_id,
        "items": [item.model_dump() for item in item_details],
        "total_amount_inr": total_amount,
        "currency": "INR",
        "is_valid_for_checkout": is_valid,
        "validation_message": msg
    }
    CARTS_DB[cart_id] = cart_data
    return CartResponse(**cart_data)


@app.post("/simulate-stockout", tags=["Simulation"])
def simulate_stockout(product_id: str = Query(...), variant_id: Optional[str] = Query(None)):
    if product_id not in CATALOG_DB:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = CATALOG_DB[product_id]
    if variant_id:
        for v in product.get("variants", []):
            if v["id"] == variant_id:
                v["stock_qty"] = 0
                return {"message": f"Simulated stockout for variant {variant_id}"}
        raise HTTPException(status_code=404, detail="Variant not found")
    else:
        product["stock_qty"] = 0
        return {"message": f"Simulated stockout for product {product_id}"}


@app.post("/checkout/create-order", response_model=CheckoutOrderResponse, tags=["Checkout"])
def create_checkout_order(payload: CheckoutCreateOrderInput):
    if payload.cart_id not in CARTS_DB:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart = CARTS_DB[payload.cart_id]
    if not cart["is_valid_for_checkout"]:
        raise HTTPException(status_code=400, detail=f"Cart cannot be checked out: {cart['validation_message']}")

    order_id = f"ord_{uuid.uuid4().hex[:8]}"
    amount_inr = cart["total_amount_inr"]

    rzp_res = razorpay_service.create_order(
        amount_inr=amount_inr,
        receipt_id=order_id,
        notes={"cart_id": payload.cart_id, "buyer": payload.buyer_name}
    )

    rzp_order_id = rzp_res["razorpay_order_id"]
    amount_paise = int(round(amount_inr * 100))

    order_record = {
        "order_id": order_id,
        "razorpay_order_id": rzp_order_id,
        "cart_id": payload.cart_id,
        "amount_inr": amount_inr,
        "amount_paise": amount_paise,
        "currency": "INR",
        "status": "CREATED",
        "items": cart["items"],
        "buyer_name": payload.buyer_name
    }
    ORDERS_DB[order_id] = order_record

    return CheckoutOrderResponse(
        order_id=order_id,
        razorpay_order_id=rzp_order_id,
        amount_inr=amount_inr,
        amount_paise=amount_paise,
        currency="INR",
        status="CREATED",
        items=[CartItemDetail(**i) for i in cart["items"]]
    )


@app.post("/checkout/verify-payment", response_model=PaymentVerificationResponse, tags=["Checkout"])
def verify_payment(payload: PaymentVerificationInput):
    if payload.order_id not in ORDERS_DB:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = ORDERS_DB[payload.order_id]
    
    is_valid_sig = razorpay_service.verify_payment_signature(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature
    )

    if not is_valid_sig:
        order["status"] = "PAYMENT_FAILED"
        return PaymentVerificationResponse(
            success=False,
            order_id=payload.order_id,
            status="PAYMENT_FAILED",
            message="Payment verification signature mismatch."
        )

    for item in order["items"]:
        p_id = item["product_id"]
        product = CATALOG_DB[p_id]
        qty = item["quantity"]
        product["stock_qty"] = max(0, product["stock_qty"] - qty)

        if item["variant_id"]:
            for v in product.get("variants", []):
                if v["id"] == item["variant_id"]:
                    v["stock_qty"] = max(0, v["stock_qty"] - qty)

    order["status"] = "PAID"
    order["razorpay_payment_id"] = payload.razorpay_payment_id

    return PaymentVerificationResponse(
        success=True,
        order_id=payload.order_id,
        status="PAID",
        message="Payment verified successfully. Order confirmed!"
    )


# --- Dashboard API Endpoints ---

class AgentExecutionInput(BaseModel):
    goal: str
    spending_cap_inr: float = 2000.0

@app.post("/api/execute-agent", tags=["Dashboard API"])
def execute_agent_api(payload: AgentExecutionInput):
    reasoner = LLMReasoner()
    products = list(CATALOG_DB.values())
    choice = reasoner.select_product_for_goal(
        agent_goal=payload.goal,
        catalog_products=products,
        spending_cap_inr=payload.spending_cap_inr
    )

    if choice.stock_warnings:
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        total_amount = sum([item.quantity * CATALOG_DB[item.product_id]["price_inr"] for item in choice.items])
        summary_names = ", ".join([f"{i.quantity}x {CATALOG_DB[i.product_id]['name']}" for i in choice.items])
        
        PENDING_PROPOSALS[session_id] = {
            "session_id": session_id,
            "goal": payload.goal,
            "spending_cap_inr": payload.spending_cap_inr,
            "choice": choice.model_dump(),
            "total_amount": total_amount,
            "summary_names": summary_names
        }

        return {
            "status": "GATED",
            "session_id": session_id,
            "summary_names": summary_names,
            "total_amount_inr": total_amount,
            "spending_cap_inr": payload.spending_cap_inr,
            "remaining_balance": payload.spending_cap_inr - total_amount,
            "llm_reasoning": choice.reasoning,
            "stock_warnings": choice.stock_warnings
        }

    agent = BuyerAgent(merchant_base_url="http://127.0.0.1:8000", spending_cap_inr=payload.spending_cap_inr, gating_mode="AUTO_APPROVE")
    res = agent.execute_purchase_goal(payload.goal)
    res["stock_warnings"] = choice.stock_warnings
    return res


class ConfirmGatingInput(BaseModel):
    session_id: str
    approved: bool

@app.post("/api/confirm-gating", tags=["Dashboard API"])
def confirm_gating_api(payload: ConfirmGatingInput):
    if payload.session_id not in PENDING_PROPOSALS:
        raise HTTPException(status_code=404, detail="Proposal session not found")
    
    proposal = PENDING_PROPOSALS.pop(payload.session_id)
    if not payload.approved:
        return {"success": False, "status": "REJECTED_BY_USER", "message": "User denied gating clearance."}

    agent = BuyerAgent(merchant_base_url="http://127.0.0.1:8000", spending_cap_inr=proposal["spending_cap_inr"], gating_mode="AUTO_APPROVE")
    res = agent.execute_purchase_goal(proposal["goal"], session_id=proposal["session_id"])
    return res


@app.get("/api/audit-logs", tags=["Dashboard API"])
def get_audit_logs_api():
    db = SessionLocal()
    try:
        records = db.query(AuditLogRecord).order_by(AuditLogRecord.id.desc()).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "",
                "session_id": r.session_id,
                "step_type": r.step_type,
                "proposed_action": r.proposed_action,
                "guardrail_passed": r.guardrail_passed,
                "guardrail_message": r.guardrail_message,
                "gate_status": r.gate_status,
                "razorpay_order_id": r.razorpay_order_id,
                "outcome_status": r.outcome_status,
                "llm_reasoning": r.llm_reasoning,
                "proposed_amount_inr": r.proposed_amount_inr
            }
            for r in records
        ]
    finally:
        db.close()


@app.delete("/api/audit-logs", tags=["Dashboard API"])
def clear_audit_logs_api():
    db = SessionLocal()
    try:
        deleted_count = db.query(AuditLogRecord).delete()
        db.commit()
        return {"success": True, "message": f"Cleared {deleted_count} audit records from database."}
    finally:
        db.close()
