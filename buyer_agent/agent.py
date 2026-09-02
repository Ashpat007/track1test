"""
Autonomous Buyer Agent Core Orchestrator.
Orchestrates: Catalog Fetch -> LLM Reasoning -> Guardrail Evaluation -> Gating Clearance -> Cart & Checkout API execution -> Audit Logging.
Supports multi-product cart selections (e.g. 2x Kahwa + 1x Matcha).
Includes Multi-Merchant Federated Cross-Store Stockout Recovery (Store A ➔ Store B failover).
"""

import os
import uuid
import hmac
import hashlib
from typing import Dict, Any, Optional, List
from rich.console import Console
from dotenv import load_dotenv

from buyer_agent.client import MerchantClient
from buyer_agent.llm_reasoner import LLMReasoner, AgentChoice, AgentRecommendationProposal
from guardrails.engine import GuardrailEngine
from guardrails.gating import GatingCheckpoint
from guardrails.audit import AuditLogger

load_dotenv()
console = Console()


class BuyerAgent:
    def __init__(
        self,
        merchant_base_url: str = "http://127.0.0.1:8000",
        spending_cap_inr: float = 500.0,
        gating_mode: str = "CLI"
    ):
        self.client = MerchantClient(base_url=merchant_base_url)
        session_cap = max(spending_cap_inr * 2.0, 5000.0)
        self.guardrail_engine = GuardrailEngine(
            max_single_action_inr=spending_cap_inr,
            max_session_spend_inr=session_cap
        )
        self.gating = GatingCheckpoint(mode=gating_mode)
        self.llm_reasoner = LLMReasoner()
        self.spending_cap_inr = spending_cap_inr
        self.session_spent_inr = 0.0

    def execute_merchant_b_purchase(
        self,
        agent_goal: str,
        session_id: str,
        logger: AuditLogger
    ) -> Dict[str, Any]:
        """Executes Federated Cross-Merchant purchase on Store B (Botanical Leaf Co.) when Store A stock is 0."""
        try:
            console.print(f"\n[bold yellow][FEDERATED] Store A stockout detected. Routing to Store B (Botanical Leaf Co.)...[/bold yellow]")
        except Exception:
            pass
        
        try:
            b_catalog = self.client.get_merchant_b_catalog(in_stock_only=True)
            b_products = b_catalog.get("products", [])
        except Exception as e:
            err_msg = f"Failed to reach Store B Merchant Catalog: {str(e)}"
            return {"success": False, "status": "API_ERROR", "message": err_msg, "session_id": session_id}

        target_p = None
        for p in b_products:
            kw_match = any((w in p["name"].lower() or w in p["category"].lower() or any(w in t.lower() for t in p["tags"])) for w in agent_goal.lower().split() if len(w) > 2)
            if kw_match:
                target_p = p
                break
        
        if not target_p and b_products:
            target_p = b_products[0]

        if not target_p:
            return {"success": False, "status": "NO_STOCK_FEDERATED", "message": "No matching stock across Store A and Store B.", "session_id": session_id}

        u_price = target_p["price_inr"]
        summary_names = f"1x {target_p['name']}"

        # Evaluate Guardrails
        eval_res = self.guardrail_engine.evaluate_proposal(
            product_id=target_p["id"],
            product_name=summary_names,
            total_amount_inr=u_price,
            quantity=1,
            currency="INR",
            current_session_spent_inr=self.session_spent_inr
        )

        if not eval_res.passed:
            return {"success": False, "status": "BLOCKED_GUARDRAIL", "reason": eval_res.rejection_reason, "session_id": session_id}

        # Gating Clearance
        is_approved = self.gating.request_approval(
            product_summary=f"{summary_names} [STORE B: BOTANICAL LEAF CO.]",
            total_amount_inr=u_price,
            llm_reasoning=f"Store A encountered stockout (0 units). Automatically failing over to Federated Merchant B (Botanical Leaf Co.) for in-stock {target_p['name']} at ₹{u_price:.2f}.",
            spending_cap_inr=self.spending_cap_inr,
            items_detail=[{"product_id": target_p["id"], "product_name": target_p["name"], "unit_price_inr": u_price, "quantity": 1, "subtotal_inr": u_price}]
        )

        if not is_approved:
            return {"success": False, "status": "REJECTED_BY_USER", "message": "User denied gating clearance.", "session_id": session_id}

        # Checkout on Store B
        cart_res = self.client.create_merchant_b_cart([{"product_id": target_p["id"], "quantity": 1}])
        checkout_res = self.client.create_merchant_b_checkout_order(cart_id=cart_res["cart_id"])
        
        rzp_order_id = checkout_res["razorpay_order_id"]
        merchant_order_id = checkout_res["order_id"]
        simulated_payment_id = f"pay_bot_{uuid.uuid4().hex[:10]}"

        key_secret = os.getenv("RAZORPAY_KEY_SECRET", "sr5phj3GIj2gWBIRTmunq8Nh")
        sig = hmac.new(
            bytes(key_secret, 'utf-8'),
            bytes(f"{rzp_order_id}|{simulated_payment_id}", 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        pay_res = self.client.verify_merchant_b_payment(
            order_id=merchant_order_id,
            razorpay_order_id=rzp_order_id,
            razorpay_payment_id=simulated_payment_id,
            razorpay_signature=sig
        )

        if pay_res.get("success"):
            self.session_spent_inr += u_price
            logger.log_step(
                "FEDERATED_PAYMENT_EXECUTION",
                agent_goal=agent_goal,
                proposed_action=f"Purchased: {summary_names} (Store B: Botanical Leaf Co.)",
                llm_reasoning="Federated Cross-Merchant Failover to Botanical Leaf Co. (Store B) successful due to Store A stockout.",
                proposed_amount_inr=u_price,
                guardrail_passed=True,
                gate_status="APPROVED",
                razorpay_order_id=rzp_order_id,
                razorpay_payment_id=simulated_payment_id,
                outcome_status="FEDERATED_TEST_SUCCESS",
                details={"store": "Botanical Leaf Co. (Store B)", "order_details": pay_res}
            )

            return {
                "success": True,
                "status": "SUCCESS",
                "session_id": session_id,
                "summary_names": f"{summary_names} (Store B)",
                "amount_inr": u_price,
                "remaining_balance_inr": self.spending_cap_inr - u_price,
                "session_spent_inr": self.session_spent_inr,
                "razorpay_order_id": rzp_order_id,
                "razorpay_payment_id": simulated_payment_id,
                "store_name": "Botanical Leaf Co. (Store B)",
                "federated_failover": True,
                "audit_session_id": session_id
            }
        else:
            return {"success": False, "status": "PAYMENT_DECLINED", "message": pay_res.get("message"), "session_id": session_id}

    def execute_preapproved_choice(
        self,
        choice: AgentChoice,
        agent_goal: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        logger = AuditLogger(session_id=session_id)

        try:
            catalog_data = self.client.get_catalog(in_stock_only=True)
            products = catalog_data.get("products", [])
        except Exception as e:
            err_msg = f"Failed to reach Merchant Catalog API: {str(e)}"
            logger.log_step("CATALOG_SEARCH", agent_goal=agent_goal, outcome_status="FAILED", guardrail_message=err_msg)
            return {"success": False, "status": "API_ERROR", "message": err_msg, "session_id": session_id}

        cart_input_items = []
        item_details_list = []
        total_amount = 0.0

        for item_sel in choice.items:
            target_p = next((p for p in products if p["id"] == item_sel.product_id), None)
            if not target_p:
                raw_catalog = self.client.get_catalog(in_stock_only=False).get("products", [])
                target_p = next((p for p in raw_catalog if p["id"] == item_sel.product_id), None)
            
            if not target_p:
                continue

            u_price = target_p["price_inr"]
            v_name = None
            if item_sel.variant_id:
                v_match = next((v for v in target_p.get("variants", []) if v["id"] == item_sel.variant_id), None)
                if v_match:
                    u_price += v_match["price_modifier_inr"]
                    v_name = v_match["name"]

            subtotal = u_price * item_sel.quantity
            total_amount += subtotal

            cart_input_items.append({
                "product_id": item_sel.product_id,
                "variant_id": item_sel.variant_id,
                "quantity": item_sel.quantity
            })
            item_details_list.append({
                "product_id": item_sel.product_id,
                "product_name": target_p["name"],
                "variant_id": item_sel.variant_id,
                "variant_name": v_name,
                "unit_price_inr": u_price,
                "quantity": item_sel.quantity,
                "subtotal_inr": subtotal
            })

        if not cart_input_items:
            err_msg = "No valid products found in pre-approved selection."
            logger.log_step("LLM_REASONING", agent_goal=agent_goal, outcome_status="FAILED", guardrail_message=err_msg)
            return {"success": False, "status": "INVALID_SELECTION", "message": err_msg, "session_id": session_id}

        summary_names = ", ".join([f"{i['quantity']}x {i['product_name']}" for i in item_details_list])

        # Evaluate Deterministic Guardrails
        eval_res = self.guardrail_engine.evaluate_proposal(
            product_id=item_details_list[0]["product_id"],
            product_name=summary_names,
            total_amount_inr=total_amount,
            quantity=sum([i["quantity"] for i in item_details_list]),
            currency="INR",
            current_session_spent_inr=self.session_spent_inr
        )

        if not eval_res.passed:
            logger.log_step(
                "GUARDRAIL_EVALUATION",
                agent_goal=agent_goal,
                proposed_action=f"Purchase Bundle: {summary_names}",
                llm_reasoning=choice.reasoning,
                reasoning_source=choice.reasoning_source,
                spending_cap_inr=self.spending_cap_inr,
                proposed_amount_inr=total_amount,
                guardrail_passed=False,
                guardrail_message=eval_res.rejection_reason,
                outcome_status="BLOCKED_GUARDRAIL"
            )
            return {
                "success": False,
                "status": "BLOCKED_GUARDRAIL",
                "reason": eval_res.rejection_reason,
                "session_id": session_id,
                "upsell_proposal": choice.upsell_proposal.model_dump() if choice.upsell_proposal else None
            }

        logger.log_step(
            "USER_GATING",
            agent_goal=agent_goal,
            proposed_action=f"Purchase Bundle: {summary_names}",
            llm_reasoning=choice.reasoning,
            reasoning_source=choice.reasoning_source,
            proposed_amount_inr=total_amount,
            guardrail_passed=True,
            gate_status="APPROVED",
            outcome_status="APPROVED"
        )

        try:
            cart_res = self.client.create_cart(cart_input_items)
            cart_id = cart_res["cart_id"]

            checkout_res = self.client.create_checkout_order(cart_id=cart_id, buyer_name="Agentic Commerce Buyer")
            rzp_order_id = checkout_res["razorpay_order_id"]
            merchant_order_id = checkout_res["order_id"]
        except Exception as e:
            # Check if cart creation failed due to stockout during checkout
            if "Insufficient stock" in str(e) or "stock" in str(e).lower():
                console.print(f"[bold yellow]⚠️ Store A stockout during checkout: {e}. Attempting Federated Store B failover...[/bold yellow]")
                return self.execute_merchant_b_purchase(agent_goal=agent_goal, session_id=session_id, logger=logger)
            
            err_str = str(e)
            logger.log_step(
                "PAYMENT_EXECUTION",
                agent_goal=agent_goal,
                guardrail_passed=True,
                outcome_status="FAILED",
                guardrail_message=err_str
            )
            return {"success": False, "status": "CHECKOUT_FAILED", "error": err_str, "session_id": session_id}

        simulated_payment_id = f"pay_{uuid.uuid4().hex[:10]}"
        key_secret = os.getenv("RAZORPAY_KEY_SECRET", "sr5phj3GIj2gWBIRTmunq8Nh")
        sig = hmac.new(
            bytes(key_secret, 'utf-8'),
            bytes(f"{rzp_order_id}|{simulated_payment_id}", 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        pay_res = self.client.verify_payment(
            order_id=merchant_order_id,
            razorpay_order_id=rzp_order_id,
            razorpay_payment_id=simulated_payment_id,
            razorpay_signature=sig
        )

        if pay_res.get("success"):
            self.session_spent_inr += total_amount

            logger.log_step(
                "PAYMENT_EXECUTION",
                agent_goal=agent_goal,
                proposed_action=f"Purchased Bundle: {summary_names}",
                llm_reasoning=choice.reasoning,
                reasoning_source=choice.reasoning_source,
                proposed_amount_inr=total_amount,
                guardrail_passed=True,
                gate_status="APPROVED",
                razorpay_order_id=rzp_order_id,
                razorpay_payment_id=simulated_payment_id,
                outcome_status="SIMULATED_TEST_SUCCESS",
                details={"order_details": pay_res, "verification_mode": "SIMULATED_TEST_SIGNATURE"}
            )

            remaining_bal = self.spending_cap_inr - total_amount

            return {
                "success": True,
                "status": "SUCCESS",
                "session_id": session_id,
                "summary_names": summary_names,
                "amount_inr": total_amount,
                "remaining_balance_inr": remaining_bal,
                "session_spent_inr": self.session_spent_inr,
                "razorpay_order_id": rzp_order_id,
                "razorpay_payment_id": simulated_payment_id,
                "reasoning_source": choice.reasoning_source,
                "verification_mode": "SIMULATED_TEST_SIGNATURE",
                "audit_session_id": session_id
            }
        else:
            logger.log_step(
                "PAYMENT_EXECUTION",
                agent_goal=agent_goal,
                guardrail_passed=True,
                outcome_status="PAYMENT_FAILED",
                guardrail_message=pay_res.get("message")
            )
            return {"success": False, "status": "PAYMENT_DECLINED", "message": pay_res.get("message"), "session_id": session_id}

    def execute_purchase_goal(
        self,
        agent_goal: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        logger = AuditLogger(session_id=session_id)

        try:
            console.print(f"\n[bold green]Starting Buyer Agent Session:[/bold green] [bold cyan]{session_id}[/bold cyan]")
            console.print(f"[bold yellow]Goal:[/bold yellow] '{agent_goal}'")
        except Exception:
            pass

        excluded_product_ids: List[str] = []
        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                catalog_data = self.client.get_catalog(in_stock_only=True)
                products = catalog_data.get("products", [])
            except Exception as e:
                err_msg = f"Failed to reach Merchant Catalog API: {str(e)}"
                logger.log_step("CATALOG_SEARCH", agent_goal=agent_goal, outcome_status="FAILED", guardrail_message=err_msg)
                return {"success": False, "status": "API_ERROR", "message": err_msg, "session_id": session_id}

            # Check if Store A has 0 products or if goal specifically matches an out-of-stock item in Store A
            raw_catalog = self.client.get_catalog(in_stock_only=False).get("products", [])
            depleted_target = next((p for p in raw_catalog if p["stock_qty"] <= 0 and any(w in p["name"].lower() for w in agent_goal.lower().split() if len(w) > 2)), None)
            
            if depleted_target or not products:
                try:
                    console.print(f"[bold yellow]Store A Stockout Detected for '{depleted_target['name'] if depleted_target else agent_goal}'! Initiating Federated Store B Failover...[/bold yellow]")
                except Exception:
                    pass
                return self.execute_merchant_b_purchase(agent_goal=agent_goal, session_id=session_id, logger=logger)

            logger.log_step(
                "CATALOG_SEARCH",
                agent_goal=agent_goal,
                guardrail_passed=True,
                outcome_status="SUCCESS",
                details={"total_products": len(products), "excluded_products": excluded_product_ids}
            )

            try:
                choice = self.llm_reasoner.select_product_for_goal(
                    agent_goal=agent_goal,
                    catalog_products=products,
                    spending_cap_inr=self.spending_cap_inr,
                    exclude_product_ids=excluded_product_ids
                )
            except Exception as e:
                err_msg = f"LLM catalog reasoning failed: {str(e)}"
                logger.log_step("LLM_REASONING", agent_goal=agent_goal, outcome_status="FAILED", guardrail_message=err_msg)
                return {"success": False, "status": "REASONING_FAILED", "message": err_msg, "session_id": session_id}

            cart_input_items = []
            item_details_list = []
            total_amount = 0.0

            for item_sel in choice.items:
                target_p = next((p for p in products if p["id"] == item_sel.product_id), None)
                if not target_p:
                    target_p = next((p for p in raw_catalog if p["id"] == item_sel.product_id), None)
                
                if not target_p:
                    continue
                
                u_price = target_p["price_inr"]
                v_name = None
                if item_sel.variant_id:
                    v_match = next((v for v in target_p.get("variants", []) if v["id"] == item_sel.variant_id), None)
                    if v_match:
                        u_price += v_match["price_modifier_inr"]
                        v_name = v_match["name"]

                subtotal = u_price * item_sel.quantity
                total_amount += subtotal

                cart_input_items.append({
                    "product_id": item_sel.product_id,
                    "variant_id": item_sel.variant_id,
                    "quantity": item_sel.quantity
                })
                item_details_list.append({
                    "product_id": item_sel.product_id,
                    "product_name": target_p["name"],
                    "variant_id": item_sel.variant_id,
                    "variant_name": v_name,
                    "unit_price_inr": u_price,
                    "quantity": item_sel.quantity,
                    "subtotal_inr": subtotal
                })

            if not cart_input_items or total_amount > self.spending_cap_inr:
                match_p = next((p for p in products if p["id"].lower() in agent_goal.lower() or any(w.lower() in p["name"].lower() for w in agent_goal.split() if len(w) > 3)), None)
                p_name = match_p["name"] if match_p else agent_goal
                p_cost = match_p["price_inr"] if match_p else 0.0

                rej_msg = f"Proposed amount ₹{p_cost:.2f} exceeds single action spending cap of ₹{self.spending_cap_inr:.2f}." if p_cost > 0 else f"Requested items exceed spending cap of ₹{self.spending_cap_inr:.2f}."
                upsell_dict = choice.upsell_proposal.model_dump() if choice.upsell_proposal else None

                logger.log_step(
                    "GUARDRAIL_EVALUATION",
                    agent_goal=agent_goal,
                    proposed_action=f"Requested Product: {p_name}",
                    llm_reasoning=choice.reasoning,
                    reasoning_source=choice.reasoning_source,
                    spending_cap_inr=self.spending_cap_inr,
                    proposed_amount_inr=p_cost,
                    guardrail_passed=False,
                    guardrail_message=rej_msg,
                    outcome_status="BLOCKED_GUARDRAIL",
                    details={"upsell_proposal": upsell_dict}
                )
                console.print(f"[bold red]⛔ GUARDRAIL BLOCKED TRANSACTION:[/bold red] {rej_msg}")
                return {
                    "success": False,
                    "status": "BLOCKED_GUARDRAIL",
                    "reason": rej_msg,
                    "session_id": session_id,
                    "upsell_proposal": upsell_dict
                }

            summary_names = ", ".join([f"{i['quantity']}x {i['product_name']}" for i in item_details_list])

            logger.log_step(
                "LLM_REASONING",
                agent_goal=agent_goal,
                proposed_action=f"Select Bundle: {summary_names}",
                llm_reasoning=choice.reasoning,
                reasoning_source=choice.reasoning_source,
                proposed_amount_inr=total_amount,
                guardrail_passed=True,
                outcome_status="PROPOSED",
                details={"items": cart_input_items, "reasoning_source": choice.reasoning_source}
            )

            eval_res = self.guardrail_engine.evaluate_proposal(
                product_id=item_details_list[0]["product_id"],
                product_name=summary_names,
                total_amount_inr=total_amount,
                quantity=sum([i["quantity"] for i in item_details_list]),
                currency="INR",
                current_session_spent_inr=self.session_spent_inr
            )

            if not eval_res.passed:
                upsell_dict = choice.upsell_proposal.model_dump() if choice.upsell_proposal else None
                logger.log_step(
                    "GUARDRAIL_EVALUATION",
                    agent_goal=agent_goal,
                    proposed_action=f"Purchase Bundle: {summary_names}",
                    llm_reasoning=choice.reasoning,
                    reasoning_source=choice.reasoning_source,
                    spending_cap_inr=self.spending_cap_inr,
                    proposed_amount_inr=total_amount,
                    guardrail_passed=False,
                    guardrail_message=eval_res.rejection_reason,
                    outcome_status="BLOCKED_GUARDRAIL",
                    details={"upsell_proposal": upsell_dict}
                )
                console.print(f"[bold red]⛔ GUARDRAIL BLOCKED TRANSACTION:[/bold red] {eval_res.rejection_reason}")
                return {
                    "success": False,
                    "status": "BLOCKED_GUARDRAIL",
                    "reason": eval_res.rejection_reason,
                    "session_id": session_id,
                    "upsell_proposal": upsell_dict
                }

            logger.log_step(
                "GUARDRAIL_EVALUATION",
                agent_goal=agent_goal,
                proposed_action=f"Purchase Bundle: {summary_names}",
                llm_reasoning=choice.reasoning,
                reasoning_source=choice.reasoning_source,
                spending_cap_inr=self.spending_cap_inr,
                proposed_amount_inr=total_amount,
                guardrail_passed=True,
                guardrail_message="All deterministic spending cap rules passed.",
                outcome_status="PASSED"
            )

            is_approved = self.gating.request_approval(
                product_summary=summary_names,
                total_amount_inr=total_amount,
                llm_reasoning=choice.reasoning,
                spending_cap_inr=self.spending_cap_inr,
                items_detail=item_details_list,
                stock_warnings=choice.stock_warnings
            )

            if not is_approved:
                logger.log_step(
                    "USER_GATING",
                    agent_goal=agent_goal,
                    proposed_action=f"Purchase Bundle: {summary_names}",
                    llm_reasoning=choice.reasoning,
                    reasoning_source=choice.reasoning_source,
                    proposed_amount_inr=total_amount,
                    guardrail_passed=True,
                    gate_status="REJECTED",
                    outcome_status="REJECTED_BY_USER"
                )
                return {
                    "success": False,
                    "status": "REJECTED_BY_USER",
                    "message": "User/Gating checkpoint denied payment clearance.",
                    "session_id": session_id
                }

            return self.execute_preapproved_choice(choice=choice, agent_goal=agent_goal, session_id=session_id)

        return {"success": False, "status": "RETRY_EXHAUSTED", "message": "Could not complete purchase after retries.", "session_id": session_id}
