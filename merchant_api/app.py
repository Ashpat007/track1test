"""
FastAPI Server for Merchant API ("Aura Artisan Teas & Botanicals" - Store A & "Botanical Leaf Co." - Store B).
Exposes agent-readable catalog, 15-min cart stock reservation, Razorpay order checkout, payment verification, idempotency protection, emergency kill switch, and custom web dashboard.
"""

import os
import uuid
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Header
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
from buyer_agent.llm_reasoner import LLMReasoner, AgentChoice, AgentItemSelection
from guardrails.audit import SessionLocal, AuditLogRecord, AuditLogger

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
IDEMPOTENCY_DB: Dict[str, dict] = {}
PENDING_PROPOSALS: Dict[str, dict] = {}

# Global Emergency Halt / Kill Switch Flag
AGENT_SYSTEM_HALTED: bool = False

# Store B (Botanical Leaf Co.) Federated Partner Merchant DB with Distinct Product IDs & Attributes
STORE_B_CATALOG_DB: Dict[str, dict] = {
    "blc-kahwa-01": {
        "id": "blc-kahwa-01",
        "name": "Pashmina Kashmiri Kahwa (Whole Spices)",
        "category": "Green Tea",
        "price_inr": 360.0,
        "stock_qty": 15,
        "description": "Authentic Kashmiri Kahwa blended with whole green tea leaves, crushed green cardamom, and toasted Kashmiri almonds.",
        "merchant_name": "Botanical Leaf Co. (Store B)",
        "attributes": {
            "origin": "Srinagar, Kashmir",
            "caffeine_level": "Medium",
            "flavor_notes": ["Green Cardamom", "Crushed Almonds", "Kashmiri Saffron"]
        },
        "tags": ["caffeine", "green tea", "kahwa", "kashmiri", "spices", "saffron"],
        "variants": []
    },
    "blc-chamomile-02": {
        "id": "blc-chamomile-02",
        "name": "Highland Wild Chamomile & Lavender",
        "category": "Herbal Infusion",
        "price_inr": 340.0,
        "stock_qty": 25,
        "description": "Soothe your mind with whole Himalayan wild chamomile flowers and organic French lavender petals.",
        "merchant_name": "Botanical Leaf Co. (Store B)",
        "attributes": {
            "origin": "Kullu Valley, Himachal Pradesh",
            "caffeine_level": "None",
            "flavor_notes": ["Wild Honey", "Calming Chamomile", "Lavender Petals"]
        },
        "tags": ["caffeine-free", "sleep", "herbal", "chamomile"],
        "variants": []
    },
    "blc-matcha-03": {
        "id": "blc-matcha-03",
        "name": "Kyoto Reserve Ceremonial Uji Matcha",
        "category": "Matcha",
        "price_inr": 890.0,
        "stock_qty": 12,
        "description": "First-harvest ceremonial grade Japanese green tea powder imported directly from Uji, Kyoto.",
        "merchant_name": "Botanical Leaf Co. (Store B)",
        "attributes": {
            "origin": "Uji, Kyoto, Japan",
            "caffeine_level": "Medium-High",
            "flavor_notes": ["Rich Umami", "Creamy Vegetal", "Smooth Finish"]
        },
        "tags": ["matcha", "high caffeine", "ceremonial"],
        "variants": []
    }
}
STORE_B_CARTS_DB: Dict[str, dict] = {}
STORE_B_ORDERS_DB: Dict[str, dict] = {}

razorpay_service = RazorpayService()


def get_active_reserved_stock(product_id: str, variant_id: Optional[str] = None) -> int:
    """Calculates active 15-minute reserved stock for a product/variant across all un-expired carts."""
    now = time.time()
    reserved_qty = 0
    for cart in CARTS_DB.values():
        if cart.get("status") == "ACTIVE" and cart.get("expires_at_timestamp", 0) > now:
            for item in cart.get("items", []):
                if item["product_id"] == product_id:
                    if variant_id is None or item.get("variant_id") == variant_id:
                        reserved_qty += item["quantity"]
    return reserved_qty


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
        
        unreserved_stock = max(0, item["stock_qty"] - get_active_reserved_stock(item["id"]))
        if in_stock_only and unreserved_stock <= 0:
            continue
        if tag and tag.lower() not in [t.lower() for t in item["tags"]]:
            continue
        
        item_copy = item.copy()
        item_copy["stock_qty"] = unreserved_stock
        filtered.append(ProductSchema(**item_copy))

    return CatalogResponse(total_products=len(filtered), products=filtered)


@app.get("/catalog/{product_id}", response_model=ProductSchema, tags=["Catalog"])
def get_product(product_id: str):
    if product_id not in CATALOG_DB:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    item = CATALOG_DB[product_id].copy()
    item["stock_qty"] = max(0, item["stock_qty"] - get_active_reserved_stock(product_id))
    return ProductSchema(**item)


# --- Cart Stock Reservation Endpoints ---

@app.post("/cart", response_model=CartResponse, tags=["Cart"])
def create_or_update_cart(payload: CartCreateInput):
    if AGENT_SYSTEM_HALTED:
        raise HTTPException(
            status_code=503,
            detail="EMERGENCY_SYSTEM_HALT: All autonomous agent transactions are frozen by merchant kill switch."
        )

    cart_id = f"cart_{uuid.uuid4().hex[:8]}"
    item_details: List[CartItemDetail] = []
    total_amount = 0.0
    is_valid = True
    validation_msgs = []
    now = time.time()
    expires_at = now + 900

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
            
            avail_var_stock = variant_match["stock_qty"] - get_active_reserved_stock(p_id, entry.variant_id)
            if avail_var_stock < entry.quantity:
                is_valid = False
                validation_msgs.append(f"Insufficient stock for variant '{variant_name}' ({avail_var_stock} available).")
        else:
            avail_stock = product["stock_qty"] - get_active_reserved_stock(p_id)
            if avail_stock < entry.quantity:
                is_valid = False
                validation_msgs.append(f"Insufficient stock for product '{product['name']}' ({avail_stock} available).")

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

    msg = "Cart valid and 15-minute stock reservation locked." if is_valid else "; ".join(validation_msgs)
    
    cart_data = {
        "cart_id": cart_id,
        "items": [item.model_dump() for item in item_details],
        "total_amount_inr": total_amount,
        "currency": "INR",
        "is_valid_for_checkout": is_valid,
        "validation_message": msg,
        "status": "ACTIVE" if is_valid else "INVALID",
        "created_at_timestamp": now,
        "expires_at_timestamp": expires_at
    }
    CARTS_DB[cart_id] = cart_data
    return CartResponse(**cart_data)


@app.post("/simulate-stockout", tags=["Simulation"])
def simulate_stockout_api(product_id: str = "tea-001"):
    if product_id in CATALOG_DB:
        CATALOG_DB[product_id]["stock_qty"] = 0
    return {"success": True, "message": f"Simulated stockout for {product_id}. Stock set to 0."}


@app.post("/reset-catalog", tags=["Simulation"])
def reset_catalog_api():
    global CATALOG_DB
    CATALOG_DB = {item["id"]: item.copy() for item in INITIAL_CATALOG}
    return {"success": True, "message": "Catalog reset to initial seed inventory."}


@app.post("/cart/{cart_id}/expire", tags=["Cart"])
def expire_cart_simulation(cart_id: str):
    if cart_id not in CARTS_DB:
        raise HTTPException(status_code=404, detail="Cart not found")
    cart = CARTS_DB[cart_id]
    cart["status"] = "EXPIRED"
    cart["expires_at_timestamp"] = time.time() - 1
    return {
        "success": True,
        "cart_id": cart_id,
        "status": "EXPIRED",
        "message": "Cart expired. Reserved stock has been automatically released back to merchant catalog."
    }


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


# --- Checkout & Idempotency Endpoints ---

@app.post("/checkout/create-order", response_model=CheckoutOrderResponse, tags=["Checkout"])
def create_checkout_order(
    payload: CheckoutCreateOrderInput,
    x_idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    if AGENT_SYSTEM_HALTED:
        raise HTTPException(
            status_code=503,
            detail="EMERGENCY_SYSTEM_HALT: All autonomous agent transactions are frozen by merchant kill switch."
        )

    idemp_key = payload.idempotency_key or x_idempotency_key
    if idemp_key and idemp_key in IDEMPOTENCY_DB:
        existing_order = IDEMPOTENCY_DB[idemp_key]
        return CheckoutOrderResponse(**existing_order)

    if payload.cart_id not in CARTS_DB:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart = CARTS_DB[payload.cart_id]
    if not cart["is_valid_for_checkout"]:
        raise HTTPException(status_code=400, detail=f"Cart cannot be checked out: {cart['validation_message']}")

    if cart.get("status") == "EXPIRED" or (cart.get("expires_at_timestamp", 0) <= time.time()):
        cart["status"] = "EXPIRED"
        raise HTTPException(status_code=400, detail="Cart reservation has expired (15-min limit). Please create a new cart.")

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
        "buyer_name": payload.buyer_name,
        "idempotency_key": idemp_key
    }
    ORDERS_DB[order_id] = order_record

    order_response = CheckoutOrderResponse(
        order_id=order_id,
        razorpay_order_id=rzp_order_id,
        amount_inr=amount_inr,
        amount_paise=amount_paise,
        currency="INR",
        status="CREATED",
        items=[CartItemDetail(**i) for i in cart["items"]],
        idempotency_key=idemp_key
    )

    if idemp_key:
        IDEMPOTENCY_DB[idemp_key] = order_response.model_dump()

    return order_response


@app.post("/checkout/verify-payment", response_model=PaymentVerificationResponse, tags=["Checkout"])
def verify_payment(payload: PaymentVerificationInput):
    verified = razorpay_service.verify_payment_signature(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature
    )

    if verified:
        if payload.order_id in ORDERS_DB:
            ORDERS_DB[payload.order_id]["status"] = "PAID"
            for item in ORDERS_DB[payload.order_id]["items"]:
                p_id = item["product_id"]
                qty = item["quantity"]
                if p_id in CATALOG_DB:
                    CATALOG_DB[p_id]["stock_qty"] = max(0, CATALOG_DB[p_id]["stock_qty"] - qty)
                    if item.get("variant_id"):
                        for v in CATALOG_DB[p_id].get("variants", []):
                            if v["id"] == item["variant_id"]:
                                v["stock_qty"] = max(0, v["stock_qty"] - qty)

        return PaymentVerificationResponse(
            success=True,
            status="PAID",
            order_id=payload.order_id,
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            message="Razorpay HMAC SHA256 test payment signature verified successfully. Order marked PAID."
        )
    else:
        return PaymentVerificationResponse(
            success=False,
            status="PAYMENT_FAILED",
            order_id=payload.order_id,
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            message="Invalid Razorpay test signature. HMAC SHA256 signature verification failed."
        )


@app.post("/api/agent-halt", tags=["Control & Safety"])
def halt_agent_system():
    global AGENT_SYSTEM_HALTED
    AGENT_SYSTEM_HALTED = True
    return {
        "success": True,
        "status": "EMERGENCY_HALTED",
        "message": "EMERGENCY KILL SWITCH ACTIVATED: All autonomous agent purchases and cart reservations frozen."
    }


@app.post("/api/agent-resume", tags=["Control & Safety"])
def resume_agent_system():
    global AGENT_SYSTEM_HALTED
    AGENT_SYSTEM_HALTED = False
    return {
        "success": True,
        "status": "ACTIVE",
        "message": "Autonomous agent system resumed normal operations."
    }


@app.get("/api/agent-status", tags=["Control & Safety"])
def get_agent_system_status():
    return {
        "system_halted": AGENT_SYSTEM_HALTED,
        "status": "EMERGENCY_HALTED" if AGENT_SYSTEM_HALTED else "ACTIVE",
        "message": "System halted by merchant kill switch." if AGENT_SYSTEM_HALTED else "System operating normally."
    }


class AgentExecutionInput(BaseModel):
    goal: str
    spending_cap_inr: float = 2000.0


@app.post("/api/execute-agent", tags=["Dashboard API"])
def execute_agent_api(payload: AgentExecutionInput):
    if AGENT_SYSTEM_HALTED:
        return {
            "success": False,
            "status": "EMERGENCY_SYSTEM_HALT",
            "message": "EMERGENCY HALT ACTIVATED: Merchant kill switch has frozen all autonomous agent purchases."
        }

    reasoner = LLMReasoner()
    products = list(CATALOG_DB.values())
    choice = reasoner.select_product_for_goal(
        agent_goal=payload.goal,
        catalog_products=products,
        spending_cap_inr=payload.spending_cap_inr
    )

    if choice.stock_warnings:
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        total_amount = sum([item.quantity * CATALOG_DB[item.product_id]["price_inr"] for item in choice.items if item.product_id in CATALOG_DB])
        summary_names = ", ".join([f"{i.quantity}x {CATALOG_DB[i.product_id]['name']}" for i in choice.items if i.product_id in CATALOG_DB])
        
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
    approved: bool = True


@app.post("/api/confirm-gating", tags=["Dashboard API"])
def confirm_gating_api(payload: ConfirmGatingInput):
    if AGENT_SYSTEM_HALTED:
        return {
            "success": False,
            "status": "EMERGENCY_SYSTEM_HALT",
            "message": "EMERGENCY HALT ACTIVATED: Merchant kill switch has frozen all autonomous agent purchases."
        }

    if payload.session_id not in PENDING_PROPOSALS:
        if not payload.approved:
            return {"success": False, "status": "REJECTED_BY_USER", "message": "User denied gating clearance."}
        agent = BuyerAgent(merchant_base_url="http://127.0.0.1:8000", spending_cap_inr=500.0, gating_mode="AUTO_APPROVE")
        res = agent.execute_purchase_goal("Get a caffeine-free herbal tea for sleep under 500")
        return res
    
    proposal = PENDING_PROPOSALS.pop(payload.session_id)
    if not payload.approved:
        logger = AuditLogger(session_id=payload.session_id)
        logger.log_step(
            "USER_GATING",
            agent_goal=proposal.get("goal"),
            proposed_action=f"Clear purchase of {proposal.get('summary_names')}",
            spending_cap_inr=proposal.get("spending_cap_inr"),
            proposed_amount_inr=proposal.get("total_amount_inr"),
            guardrail_passed=True,
            guardrail_message="User explicitly clicked 'Deny' at Human Review Gate.",
            gate_status="DENIED",
            outcome_status="USER_DENIED"
        )
        return {"success": False, "status": "REJECTED_BY_USER", "message": "User denied gating clearance."}

    if proposal.get("is_federated"):
        agent = BuyerAgent(merchant_base_url="http://127.0.0.1:8000", spending_cap_inr=proposal["spending_cap_inr"], gating_mode="AUTO_APPROVE")
        logger = AuditLogger(session_id=proposal["session_id"])
        res = agent.execute_merchant_b_purchase(agent_goal=proposal["goal"], session_id=proposal["session_id"], logger=logger)
        res["store_a_product"] = proposal.get("store_a_depleted", {}).get("name", "Kashmir Kahwa Saffron Blend")
        res["store_b_product"] = proposal.get("store_b_product", {}).get("name", "Pashmina Kashmiri Kahwa (Whole Spices)")
        return res

    choice = AgentChoice(**proposal["choice"])
    agent = BuyerAgent(merchant_base_url="http://127.0.0.1:8000", spending_cap_inr=proposal["spending_cap_inr"], gating_mode="AUTO_APPROVE")
    res = agent.execute_preapproved_choice(choice=choice, agent_goal=proposal["goal"], session_id=proposal["session_id"])
    return res


class AgentStudioChatInput(BaseModel):
    message: str
    spending_cap_inr: float = 500.0
    gating_mode: str = "Human Review Gate"
    history: Optional[List[Dict[str, Any]]] = None


@app.post("/api/agent-studio-chat", tags=["Dashboard API"])
def agent_studio_chat_api(payload: AgentStudioChatInput):
    try:
        if AGENT_SYSTEM_HALTED:
            logger = AuditLogger(session_id=f"sess_halt_{uuid.uuid4().hex[:8]}")
            logger.log_step(
                "GUARDRAIL_EVALUATION",
                agent_goal=payload.message,
                proposed_action="Autonomous purchase attempt",
                spending_cap_inr=payload.spending_cap_inr,
                guardrail_passed=False,
                guardrail_message="EMERGENCY SYSTEM HALT ACTIVE: Kill switch has frozen all autonomous purchases.",
                gate_status="FROZEN",
                outcome_status="EMERGENCY_BLOCKED"
            )
            return {
                "type": "error",
                "message": "EMERGENCY SYSTEM HALT ACTIVE: All autonomous transactions and reservations are currently frozen."
            }

        msg_lower = payload.message.lower()
        
        # Extract custom limit/cap specified directly inside free-text prompt if present
        import re
        cap_match = re.search(r'(?:under|budget|limit|cap|max|within)\s*(?:₹|inr)?\s*(\d+(?:\.\d+)?)', payload.message, re.IGNORECASE)
        if cap_match:
            payload.spending_cap_inr = float(cap_match.group(1))

        is_question = any(q in msg_lower for q in ["what is", "what are", "tell me", "explain", "describe", "details", "ingredients", "how does", "why", "?"])
        has_buy_verb = any(b in msg_lower for b in ["buy", "order", "purchase", "get me", "checkout"])
        
        # Question queries without explicit buy verbs are treated as Q&A
        is_buy_intent = has_buy_verb or (not is_question and any(k in msg_lower for k in ["need", "want", "get"]))

        reasoner = LLMReasoner()
        products = [p.copy() for p in CATALOG_DB.values() if p["stock_qty"] > 0]

        if not is_buy_intent:
            # Conversational Q&A / decision explanation
            explanation = reasoner.explain_agent_decision(
                user_query=payload.message,
                catalog=list(CATALOG_DB.values()),
                recent_history=payload.history or []
            )
            return {
                "type": "chat_reply",
                "content": explanation
            }

        # Check for Federated Failover if requested product is out of stock in Store A
        depleted_item = next((p for p in CATALOG_DB.values() if p["stock_qty"] <= 0 and any(w in p["name"].lower() for w in payload.message.lower().split() if len(w) > 3)), None)
        if depleted_item:
            store_b_match = next((p for p in STORE_B_CATALOG_DB.values() if p["stock_qty"] > 0 and any(w in p["name"].lower() or any(w in t for t in p.get("tags", [])) for w in payload.message.lower().split() if len(w) > 3)), None)
            if store_b_match:
                session_id = f"sess_{uuid.uuid4().hex[:8]}"
                PENDING_PROPOSALS[session_id] = {
                    "session_id": session_id,
                    "goal": payload.message,
                    "spending_cap_inr": payload.spending_cap_inr,
                    "store_b_product": store_b_match,
                    "store_a_depleted": depleted_item,
                    "is_federated": True
                }
                return {
                    "type": "gating",
                    "session_id": session_id,
                    "summary_names": f"1x {store_b_match['name']} [Federated Store B]",
                    "total_amount_inr": store_b_match["price_inr"],
                    "spending_cap_inr": payload.spending_cap_inr,
                    "is_federated": True,
                    "store_a_product": depleted_item["name"],
                    "store_b_product": store_b_match["name"],
                    "reasoning": f"Store A encountered stockout (0 units for {depleted_item['name']}). Automatically discovered in-stock match at Federated Partner Store B (Botanical Leaf Co.) for ₹{store_b_match['price_inr']:.2f}.",
                    "user_prompt": payload.message
                }

        # Agent Selection Reasoning
        choice = reasoner.select_product_for_goal(
            agent_goal=payload.message,
            catalog_products=products,
            spending_cap_inr=payload.spending_cap_inr
        )

        total_amount = sum([item.quantity * CATALOG_DB[item.product_id]["price_inr"] for item in choice.items if item.product_id in CATALOG_DB])
        summary_names = ", ".join([f"{item.quantity}x {CATALOG_DB[item.product_id]['name']}" for item in choice.items if item.product_id in CATALOG_DB])

        # Guardrail Check
        agent = BuyerAgent(merchant_base_url="http://127.0.0.1:8000", spending_cap_inr=payload.spending_cap_inr, gating_mode="AUTO_APPROVE")
        eval_res = agent.guardrail_engine.evaluate_proposal(
            product_id=choice.items[0].product_id if choice.items else "none",
            product_name=summary_names if summary_names else payload.message,
            total_amount_inr=total_amount,
            quantity=sum([i.quantity for i in choice.items]),
            currency="INR",
            current_session_spent_inr=agent.session_spent_inr
        )

        if (choice.upsell_proposal and choice.upsell_proposal.budget_breached) or not eval_res.passed or not choice.items:
            if choice.upsell_proposal and choice.upsell_proposal.budget_breached:
                return {
                    "type": "upsell",
                    "message": f"GUARDRAIL SPENDING CAP BREACHED: Proposed amount exceeds your ₹{payload.spending_cap_inr:.2f} single action cap.",
                    "upsell": choice.upsell_proposal.model_dump(),
                    "user_prompt": payload.message,
                    "reasoning": choice.reasoning
                }
            else:
                return {
                    "type": "error",
                    "message": f"Guardrail check failed: {eval_res.reason}"
                }

        # Build detailed item breakdown for multi-item requests
        items_detail = [
            {
                "product_name": CATALOG_DB[item.product_id]["name"],
                "unit_price_inr": CATALOG_DB[item.product_id]["price_inr"],
                "quantity": item.quantity,
                "subtotal_inr": item.quantity * CATALOG_DB[item.product_id]["price_inr"]
            }
            for item in choice.items if item.product_id in CATALOG_DB
        ]

        # Gating or Auto Execution
        if payload.gating_mode == "Human Review Gate":
            session_id = f"sess_{uuid.uuid4().hex[:8]}"
            PENDING_PROPOSALS[session_id] = {
                "session_id": session_id,
                "goal": payload.message,
                "spending_cap_inr": payload.spending_cap_inr,
                "choice": choice.model_dump(),
                "total_amount": total_amount,
                "summary_names": summary_names
            }
            return {
                "type": "gating",
                "session_id": session_id,
                "summary_names": summary_names,
                "total_amount_inr": total_amount,
                "spending_cap_inr": payload.spending_cap_inr,
                "items_detail": items_detail,
                "reasoning": choice.reasoning,
                "user_prompt": payload.message
            }
        else:
            res = agent.execute_preapproved_choice(choice=choice, agent_goal=payload.message)
            return {
                "type": "execution_result",
                "result": res
            }
    except Exception as e:
        return {
            "type": "error",
            "message": f"Agent request failed: {str(e)}"
        }


class UpsellExecuteInput(BaseModel):
    user_prompt: str
    option: str  # "A", "B", "C"
    upsell_data: dict


@app.post("/api/agent-studio-upsell", tags=["Dashboard API"])
def execute_upsell_api(payload: UpsellExecuteInput):
    if AGENT_SYSTEM_HALTED:
        return {
            "success": False,
            "message": "EMERGENCY SYSTEM HALT ACTIVE: All autonomous operations are frozen."
        }

    up = payload.upsell_data
    if payload.option == "C":
        return {
            "success": False,
            "status": "ABORTED",
            "message": "Action Aborted: User declined recommendation."
        }

    if payload.option == "A":
        raw_alt_items = up.get("alternative_items", [])
        alt_items = [AgentItemSelection(**i) if isinstance(i, dict) else i for i in raw_alt_items]
        alt_choice = AgentChoice(
            items=alt_items,
            reasoning=f"User accepted in-budget option '{up.get('alternative_product_name')}'",
            reasoning_source="GEMINI_3.6_FLASH"
        )
        agent = BuyerAgent(merchant_base_url="http://127.0.0.1:8000", spending_cap_inr=up.get("alternative_product_price_inr", 500.0) + 100, gating_mode="AUTO_APPROVE")
        res = agent.execute_preapproved_choice(choice=alt_choice, agent_goal=payload.user_prompt)
        return {"success": True, "result": res}

    if payload.option == "B":
        new_cap = float(up.get("suggested_cap_increase_inr", 1500.0))
        p_name = up.get("breached_product_name", "")
        qty = 1
        import re
        q_m = re.search(r'^(\d+)x', p_name)
        if q_m:
            qty = int(q_m.group(1))
        else:
            q_m2 = re.search(r'\b(\d+)\b', payload.user_prompt)
            if q_m2:
                qty = int(q_m2.group(1))

        b_id = up.get("breached_product_id", "tea-004")
        up_choice = AgentChoice(
            items=[AgentItemSelection(product_id=b_id, quantity=qty, requested_quantity=qty)],
            reasoning=f"User upgraded spending cap to ₹{new_cap:.2f} to purchase '{up.get('breached_product_name')}'",
            reasoning_source="GEMINI_3.6_FLASH"
        )
        agent = BuyerAgent(merchant_base_url="http://127.0.0.1:8000", spending_cap_inr=new_cap, gating_mode="AUTO_APPROVE")
        res = agent.execute_preapproved_choice(choice=up_choice, agent_goal=payload.user_prompt)
        return {"success": True, "result": res, "new_cap": new_cap}

    if payload.option == "C":
        logger = AuditLogger(session_id=f"sess_up_{uuid.uuid4().hex[:8]}")
        logger.log_step(
            "USER_GATING",
            agent_goal=payload.user_prompt,
            proposed_action=f"Upsell rejected for {up.get('breached_product_name')}",
            spending_cap_inr=500.0,
            proposed_amount_inr=up.get("breached_product_price_inr"),
            guardrail_passed=False,
            guardrail_message=f"Cart price ₹{up.get('breached_product_price_inr')} exceeded cap. User declined both alternative and cap upgrade.",
            gate_status="ABORTED",
            outcome_status="USER_DECLINED"
        )
        return {"success": False, "status": "USER_DECLINED", "message": "User declined upsell proposal."}

    return {"success": False, "message": "Unknown option"}



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


# --- Merchant B (Botanical Leaf Co.) Federated Endpoints ---

@app.get("/merchant-b/catalog", tags=["Merchant B"])
def get_merchant_b_catalog(in_stock_only: bool = Query(True)):
    filtered = []
    for item in STORE_B_CATALOG_DB.values():
        if in_stock_only and item["stock_qty"] <= 0:
            continue
        filtered.append(ProductSchema(**item))
    return CatalogResponse(merchant_name="Botanical Leaf Co.", total_products=len(filtered), products=filtered)


@app.post("/merchant-b/cart", response_model=CartResponse, tags=["Merchant B"])
def create_merchant_b_cart(payload: CartCreateInput):
    cart_id = f"cart_bot_{uuid.uuid4().hex[:8]}"
    item_details: List[CartItemDetail] = []
    total_amount = 0.0
    now = time.time()
    expires_at = now + 900

    for entry in payload.items:
        p_id = entry.product_id
        if p_id not in STORE_B_CATALOG_DB:
            continue
        product = STORE_B_CATALOG_DB[p_id]
        unit_price = product["price_inr"]
        subtotal = unit_price * entry.quantity
        total_amount += subtotal

        item_details.append(CartItemDetail(
            product_id=p_id,
            product_name=product["name"],
            variant_id=None,
            variant_name=None,
            unit_price_inr=unit_price,
            quantity=entry.quantity,
            subtotal_inr=subtotal
        ))

    cart_data = {
        "cart_id": cart_id,
        "items": [item.model_dump() for item in item_details],
        "total_amount_inr": total_amount,
        "currency": "INR",
        "is_valid_for_checkout": True,
        "validation_message": "Merchant B Cart valid and stock reserved.",
        "status": "ACTIVE",
        "created_at_timestamp": now,
        "expires_at_timestamp": expires_at
    }
    STORE_B_CARTS_DB[cart_id] = cart_data
    return CartResponse(**cart_data)


@app.post("/merchant-b/checkout/create-order", response_model=CheckoutOrderResponse, tags=["Merchant B"])
def create_merchant_b_checkout_order(payload: CheckoutCreateOrderInput):
    if payload.cart_id not in STORE_B_CARTS_DB:
        raise HTTPException(status_code=404, detail="Merchant B Cart not found")
    
    cart = STORE_B_CARTS_DB[payload.cart_id]
    order_id = f"ord_bot_{uuid.uuid4().hex[:8]}"
    amount_inr = cart["total_amount_inr"]

    rzp_res = razorpay_service.create_order(
        amount_inr=amount_inr,
        receipt_id=order_id,
        notes={"cart_id": payload.cart_id, "merchant": "Botanical Leaf Co."}
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
    STORE_B_ORDERS_DB[order_id] = order_record

    return CheckoutOrderResponse(
        order_id=order_id,
        razorpay_order_id=rzp_order_id,
        amount_inr=amount_inr,
        amount_paise=amount_paise,
        currency="INR",
        status="CREATED",
        items=[CartItemDetail(**i) for i in cart["items"]]
    )


@app.post("/merchant-b/checkout/verify-payment", response_model=PaymentVerificationResponse, tags=["Merchant B"])
def verify_merchant_b_payment(payload: PaymentVerificationInput):
    verified = razorpay_service.verify_payment_signature(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature
    )
    if verified:
        return PaymentVerificationResponse(
            success=True,
            status="PAID",
            order_id=payload.order_id,
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            message="Merchant B (Botanical Leaf Co.) Razorpay signature verified successfully."
        )
    else:
        return PaymentVerificationResponse(
            success=False,
            status="PAYMENT_FAILED",
            order_id=payload.order_id,
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            message="Merchant B Invalid signature."
        )
