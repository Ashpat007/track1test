"""
Gemini LLM Catalog Reasoner (Migrated to modern `google.genai` SDK).
Evaluates natural language goals against raw catalog JSON and outputs structured multi-product cart selections.
CONFINED STRICTLY TO INTENT PARSING & SELECTION — CANNOT EXECUTE PAYMENTS WITHOUT GATING CLEARANCE.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


class AgentItemSelection(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(default=1, gt=0)
    requested_quantity: int = Field(default=1, gt=0)
    stock_warning: Optional[str] = None


class AgentChoice(BaseModel):
    items: List[AgentItemSelection]
    reasoning: str
    reasoning_source: str = "GEMINI_3.6_FLASH"
    stock_warnings: List[str] = Field(default_factory=list)


class LLMReasoner:
    def __init__(self, model_name: str = "gemini-3.6-flash"):
        self.model_name = model_name
        self.client = None
        if GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[LLMReasoner Init Notice] genai.Client init: {e}")

    def select_product_for_goal(
        self,
        agent_goal: str,
        catalog_products: List[Dict[str, Any]],
        spending_cap_inr: float,
        exclude_product_ids: Optional[List[str]] = None
    ) -> AgentChoice:
        """
        Queries Gemini LLM via google.genai SDK to select items matching the buyer's goal.
        Explicitly tracks reasoning_source ("GEMINI_3.6_FLASH" vs "RULE_FALLBACK").
        """
        exclude_ids = exclude_product_ids or []
        available_catalog = [p for p in catalog_products if p["id"] not in exclude_ids and p["stock_qty"] > 0]

        if not available_catalog:
            raise ValueError("No matching in-stock catalog items available for evaluation.")

        if self.client:
            try:
                prompt = f"""
You are an expert autonomous buyer assistant reasoning over a merchant's product catalog.

BUYER GOAL: "{agent_goal}"
SINGLE ACTION SPENDING CAP: ₹{spending_cap_inr:.2f}

CATALOG:
{json.dumps(available_catalog, indent=2)}

INSTRUCTIONS:
1. Select all items matching the buyer's requested products and quantities.
2. If requested quantity > available stock_qty, select remaining stock_qty and set stock_warning.
3. Ensure combined cost <= ₹{spending_cap_inr:.2f}.
4. Provide a rich, natural language explanation for why these items were selected.
5. Output STRICT JSON:
{{
  "items": [
    {{
      "product_id": "string",
      "variant_id": "string or null",
      "quantity": 1,
      "requested_quantity": 1,
      "stock_warning": "string or null"
    }}
  ],
  "reasoning": "string explanation of why this selection fulfills the goal",
  "stock_warnings": ["string"]
}}
"""
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                raw_text = response.text.strip()
                data = json.loads(raw_text)
                
                items = [AgentItemSelection(**i) for i in data.get("items", [])]
                warnings = data.get("stock_warnings", [])
                
                return AgentChoice(
                    items=items,
                    reasoning=data.get("reasoning", "Gemini catalog reasoning completed."),
                    reasoning_source="GEMINI_3.6_FLASH",
                    stock_warnings=warnings
                )
            except Exception as e:
                print(f"[LLMReasoner Notice] Gemini API call exception: {e}. Utilizing Token-Proximity NLP Fallback.")
                return self._token_proximity_nlp_parser(agent_goal, available_catalog, spending_cap_inr)
        else:
            return self._token_proximity_nlp_parser(agent_goal, available_catalog, spending_cap_inr)

    def _token_proximity_nlp_parser(
        self,
        agent_goal: str,
        available_catalog: List[Dict[str, Any]],
        spending_cap_inr: float
    ) -> AgentChoice:
        goal_lower = agent_goal.lower()
        tokens = re.findall(r'\b[\w\-]+\b', goal_lower)

        word_to_num = {
            "one": 1, "a": 1, "an": 1, "single": 1,
            "two": 2, "pair": 2, "couple": 2,
            "three": 3, "trio": 3, "triple": 3,
            "four": 4, "quad": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }

        selected_items: List[AgentItemSelection] = []
        item_descriptions: List[str] = []
        stock_warnings: List[str] = []
        running_total = 0.0

        for p in available_catalog:
            p_id = p["id"].lower()
            name_words = [w for w in p["name"].lower().split() if len(w) > 3]
            cat_words = [p["category"].lower()]
            tags = [t.lower() for t in p.get("tags", [])]

            is_matched = (p_id in goal_lower) or any(kw in goal_lower for kw in name_words + cat_words + tags)
            if not is_matched:
                continue

            target_indices = []
            for idx, token in enumerate(tokens):
                if token == p_id or any(kw in token for kw in name_words):
                    target_indices.append(idx)

            req_qty = 1
            if target_indices:
                t_idx = target_indices[0]
                window = tokens[max(0, t_idx - 4) : min(len(tokens), t_idx + 5)]
                for tok in window:
                    if tok.isdigit():
                        req_qty = int(tok)
                        break
                    elif tok in word_to_num:
                        req_qty = word_to_num[tok]
                        break

            var_id = None
            unit_price = p["price_inr"]
            if p.get("variants"):
                v = p["variants"][0]
                var_id = v["id"]
                unit_price += v["price_modifier_inr"]

            avail_stock = p["stock_qty"]
            actual_qty = req_qty
            warn_msg = None

            if req_qty > avail_stock:
                actual_qty = avail_stock
                warn_msg = f"⚠️ INVENTORY WARNING: You requested {req_qty} units of '{p['name']}', but only {avail_stock} unit(s) remain in stock."
                stock_warnings.append(warn_msg)

            item_cost = unit_price * actual_qty

            if (running_total + item_cost) <= spending_cap_inr and actual_qty >= 1:
                selected_items.append(AgentItemSelection(
                    product_id=p["id"],
                    variant_id=var_id,
                    quantity=actual_qty,
                    requested_quantity=req_qty,
                    stock_warning=warn_msg
                ))
                running_total += item_cost
                item_descriptions.append(f"{actual_qty}x '{p['name']}' (₹{item_cost:.2f})")

        if not selected_items:
            first_p = available_catalog[0]
            unit_p = first_p["price_inr"]
            if unit_p <= spending_cap_inr:
                selected_items.append(AgentItemSelection(product_id=first_p["id"], quantity=1, requested_quantity=1))
                running_total = unit_p
                item_descriptions.append(f"1x '{first_p['name']}' (₹{unit_p:.2f})")

        remaining = spending_cap_inr - running_total
        reasoning_str = f"Rule-based Intent Parser: Selected {', '.join(item_descriptions)}. Combined Total: ₹{running_total:.2f}, Remaining Cap Balance: ₹{remaining:.2f}."
        if stock_warnings:
            reasoning_str += " " + " ".join(stock_warnings)

        return AgentChoice(
            items=selected_items,
            reasoning=reasoning_str,
            reasoning_source="RULE_FALLBACK",
            stock_warnings=stock_warnings
        )
