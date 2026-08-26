"""
Autonomous Buyer Agent Core Orchestrator.
Orchestrates: Catalog Fetch -> LLM Reasoning -> Guardrail Evaluation -> Gating Clearance -> Cart & Checkout API execution -> Audit Logging.
Supports multi-product cart selections (e.g. 2x Kahwa + 1x Matcha).
"""

import os
import uuid
import hmac
import hashlib
from typing import Dict, Any, Optional, List
from rich.console import Console
from dotenv import load_dotenv

from buyer_agent.client import MerchantClient
from buyer_agent.llm_reasoner import LLMReasoner
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
        # Cumulative session spend tracking
        self.session_spent_inr = 0.0

    def execute_purchase_goal(
        self,
        agent_goal: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        logger = AuditLogger(session_id=session_id)

        console.print(f"\n[bold green]🤖 Starting Buyer Agent Session:[/bold green] [bold cyan]{session_id}[/bold cyan]")
        console.print(f"[bold yellow]Goal:[/bold yellow] '{agent_goal}'")

        excluded_product_ids: List[str] = []
        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                catalog_data = self.client.get_catalog(in_stock_only=True)
                products = catalog_data.get("products", [])
            except Exception as e:
                err_msg = f"Failed to reach Merchant Catalog API: {str(e)}"
                logger.log_step("CATALOG_SEARCH", agent_goal=agent_goal, outcome_status="FAILED", guardrail_message=err_msg)
                return {"success": False, "status": "API_ERROR", "message": err_msg}

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
                return {"success": False, "status": "REASONING_FAILED", "message": err_msg}

            cart_input_items = []
            item_details_list = []
            total_amount = 0.0

            for item_sel in choice.items:
                target_p = next((p for p in products if p["id"] == item_sel.product_id), None)
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
                err_msg = "No valid products selected from catalog."
                logger.log_step("LLM_REASONING", agent_goal=agent_goal, outcome_status="FAILED", guardrail_message=err_msg)
                return {"success": False, "status": "INVALID_SELECTION", "message": err_msg}

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

            # Pass current_session_spent_inr into Guardrail Engine for cumulative session spend enforcement
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
                console.print(f"[bold red]⛔ GUARDRAIL BLOCKED TRANSACTION:[/bold red] {eval_res.rejection_reason}")
                return {
                    "success": False,
                    "status": "BLOCKED_GUARDRAIL",
                    "reason": eval_res.rejection_reason,
                    "session_id": session_id
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
                err_str = str(e)
                if "STOCKOUT_ERROR" in err_str or "409" in err_str or "Insufficient stock" in err_str:
                    console.print(f"[bold yellow]⚠️ Stockout encountered. Triggering failure recovery...[/bold yellow]")
                    logger.log_step(
                        "FAILURE_HANDLED",
                        agent_goal=agent_goal,
                        proposed_action=f"Attempted purchase of {summary_names}",
                        guardrail_passed=True,
                        outcome_status="STOCKOUT_RECOVERED",
                        details={"error": err_str}
                    )
                    # Exclude all products in the failing cart bundle to avoid infinite retries on multi-item stockouts
                    for item in cart_input_items:
                        if item["product_id"] not in excluded_product_ids:
                            excluded_product_ids.append(item["product_id"])
                    continue
                else:
                    logger.log_step(
                        "PAYMENT_EXECUTION",
                        agent_goal=agent_goal,
                        guardrail_passed=True,
                        outcome_status="FAILED",
                        guardrail_message=err_str
                    )
                    return {"success": False, "status": "CHECKOUT_FAILED", "error": err_str, "session_id": session_id}

            # Generate HMAC SHA256 signature for test simulation
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
                # Accumulate successful session spend
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

                console.print("\n[bold green]🎉 PURCHASE TRANSACTION COMPLETED SUCCESSFULLY![/bold green]")
                console.print(f"[bold cyan]Items Purchased:[/bold cyan]\n  " + "\n  ".join([f"• {i['quantity']}x {i['product_name']} ({i.get('variant_name') or 'Standard'}) — ₹{i['subtotal_inr']:.2f}" for i in item_details_list]))
                console.print(f"[bold cyan]Total Amount Paid:[/bold cyan] [bold green]₹{total_amount:.2f}[/bold green]")
                console.print(f"[bold cyan]Spending Cap Limit:[/bold cyan] ₹{self.spending_cap_inr:.2f}")
                console.print(f"[bold cyan]Cumulative Session Spent:[/bold cyan] ₹{self.session_spent_inr:.2f}")
                console.print(f"[bold cyan]Remaining Cap Balance:[/bold cyan] [bold yellow]₹{remaining_bal:.2f}[/bold yellow]")
                console.print(f"[bold cyan]Reasoning Engine:[/bold cyan] [bold magenta]{choice.reasoning_source}[/bold magenta]")
                console.print(f"[bold cyan]Razorpay Order ID (Real API):[/bold cyan] {rzp_order_id}")
                console.print(f"[bold cyan]Razorpay Payment ID (Test Sim):[/bold cyan] {simulated_payment_id}")

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

        return {"success": False, "status": "RETRY_EXHAUSTED", "message": "Could not complete purchase after retries.", "session_id": session_id}
