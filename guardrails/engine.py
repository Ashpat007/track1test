"""
Deterministic Guardrails Engine.
Enforces hard spending caps, quantity limits, and currency validation at the code level.
"""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

DEFAULT_SPENDING_CAP_INR = float(os.getenv("SPENDING_CAP_INR", "500.0"))

class RuleResult(BaseModel):
    rule_name: str
    passed: bool
    details: str

class GuardrailEvaluation(BaseModel):
    passed: bool
    rejection_reason: Optional[str] = None
    proposed_amount_inr: float
    spending_cap_inr: float
    rule_results: List[RuleResult]

class GuardrailEngine:
    def __init__(
        self,
        max_single_action_inr: float = DEFAULT_SPENDING_CAP_INR,
        max_session_spend_inr: float = 1000.0,
        max_quantity_per_item: int = 5,
        allowed_currencies: List[str] = None
    ):
        self.max_single_action_inr = max_single_action_inr
        self.max_session_spend_inr = max_session_spend_inr
        self.max_quantity_per_item = max_quantity_per_item
        self.allowed_currencies = allowed_currencies or ["INR"]

    def evaluate_proposal(
        self,
        product_id: str,
        product_name: str,
        total_amount_inr: float,
        quantity: int,
        current_session_spent_inr: float = 0.0,
        currency: str = "INR"
    ) -> GuardrailEvaluation:
        rules: List[RuleResult] = []
        is_all_passed = True
        rejection_reasons = []

        # Rule 1: Currency Check
        if currency.upper() not in self.allowed_currencies:
            is_all_passed = False
            r_msg = f"Invalid currency '{currency}'. Allowed: {self.allowed_currencies}"
            rejection_reasons.append(r_msg)
            rules.append(RuleResult(rule_name="CURRENCY_CHECK", passed=False, details=r_msg))
        else:
            rules.append(RuleResult(rule_name="CURRENCY_CHECK", passed=True, details="Currency matches INR standard."))

        # Rule 2: Single Action Spending Cap Check
        if total_amount_inr > self.max_single_action_inr:
            is_all_passed = False
            r_msg = f"Proposed amount ₹{total_amount_inr:.2f} exceeds single action spending cap of ₹{self.max_single_action_inr:.2f}."
            rejection_reasons.append(r_msg)
            rules.append(RuleResult(rule_name="SINGLE_ACTION_SPENDING_CAP", passed=False, details=r_msg))
        else:
            rules.append(RuleResult(
                rule_name="SINGLE_ACTION_SPENDING_CAP",
                passed=True,
                details=f"Proposed amount ₹{total_amount_inr:.2f} is within cap of ₹{self.max_single_action_inr:.2f}."
            ))

        # Rule 3: Session Cumulative Spend Check
        projected_total = current_session_spent_inr + total_amount_inr
        if projected_total > self.max_session_spend_inr:
            is_all_passed = False
            r_msg = f"Projected cumulative spend ₹{projected_total:.2f} exceeds session cap of ₹{self.max_session_spend_inr:.2f}."
            rejection_reasons.append(r_msg)
            rules.append(RuleResult(rule_name="SESSION_SPENDING_CAP", passed=False, details=r_msg))
        else:
            rules.append(RuleResult(
                rule_name="SESSION_SPENDING_CAP",
                passed=True,
                details=f"Projected session spend ₹{projected_total:.2f} is within cap ₹{self.max_session_spend_inr:.2f}."
            ))

        # Rule 4: Quantity Cap Check
        if quantity > self.max_quantity_per_item:
            is_all_passed = False
            r_msg = f"Requested quantity {quantity} exceeds maximum unit limit of {self.max_quantity_per_item}."
            rejection_reasons.append(r_msg)
            rules.append(RuleResult(rule_name="QUANTITY_LIMIT", passed=False, details=r_msg))
        else:
            rules.append(RuleResult(
                rule_name="QUANTITY_LIMIT",
                passed=True,
                details=f"Requested quantity {quantity} is within unit limit {self.max_quantity_per_item}."
            ))

        return GuardrailEvaluation(
            passed=is_all_passed,
            rejection_reason="; ".join(rejection_reasons) if rejection_reasons else None,
            proposed_amount_inr=total_amount_inr,
            spending_cap_inr=self.max_single_action_inr,
            rule_results=rules
        )
