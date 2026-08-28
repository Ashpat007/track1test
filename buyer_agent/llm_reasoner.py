"""
Gemini LLM Catalog Reasoner (Migrated to modern `google.genai` SDK with Multi-Model Quota Fallback).
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
        self.fallback_models = ["gemini-2.5-flash", "gemini-1.5-flash"]
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
        Queries Gemini LLM via google.genai SDK with instant multi-model fallback.
        Explicitly tracks reasoning_source ("GEMINI_3.6_FLASH", "GEMINI_2.5_FLASH", or "RULE_FALLBACK").
        """
        exclude_ids = exclude_product_ids or []
        available_catalog = [p for p in catalog_products if p["id"] not in exclude_ids and p["stock_qty"] > 0]

        if not available_catalog:
            raise ValueError("No matching in-stock catalog items available for evaluation.")

        stockout_context = ""
        if exclude_ids:
            excluded_names = [next((p["name"] for p in catalog_products if p["id"] == eid), eid) for eid in exclude_ids]
            stockout_context = f"\nIMPORTANT STOCKOUT NOTICE: The following item(s) are OUT OF STOCK and excluded from catalog: {', '.join(excluded_names)}. You MUST explicitly state in your reasoning that the primary item was out of stock and explain why this alternative item was chosen to fulfill the goal.\n"

        if self.client:
            models_to_try = [self.model_name] + [m for m in self.fallback_models if m != self.model_name]
            prompt = f"""
You are an expert autonomous buyer assistant reasoning over a merchant's product catalog.

BUYER GOAL: "{agent_goal}"
SINGLE ACTION SPENDING CAP: ₹{spending_cap_inr:.2f}
{stockout_context}
CATALOG:
{json.dumps(available_catalog, indent=2)}

INSTRUCTIONS:
1. Select all items matching the buyer's requested products and quantities.
2. If requested quantity > available stock_qty, select remaining stock_qty and set stock_warning.
3. Ensure combined cost <= ₹{spending_cap_inr:.2f}.
4. Provide a rich, natural language explanation for why these items were selected. If requested items exceed spending cap or primary items were out of stock, state that clearly in reasoning.
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
            for target_model in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=target_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    raw_text = response.text.strip()
                    data = json.loads(raw_text)
                    
                    items = [AgentItemSelection(**i) for i in data.get("items", [])]
                    warnings = data.get("stock_warnings", [])
                    reasoning_text = data.get("reasoning", "Gemini catalog reasoning completed.")

                    if exclude_ids and "stock" not in reasoning_text.lower() and "out of" not in reasoning_text.lower():
                        excluded_names_str = ", ".join([next((p["name"] for p in catalog_products if p["id"] == eid), eid) for eid in exclude_ids])
                        reasoning_text = f"⚠️ [STOCKOUT RECOVERED]: Primary item '{excluded_names_str}' hit 0 stock. Recovered by selecting in-stock alternative: {reasoning_text}"

                    engine_tag = "GEMINI_3.6_FLASH" if "3.6" in target_model else ("GEMINI_2.5_FLASH" if "2.5" in target_model else "GEMINI_1.5_FLASH")
                    
                    return AgentChoice(
                        items=items,
                        reasoning=reasoning_text,
                        reasoning_source=engine_tag,
                        stock_warnings=warnings
                    )
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        print(f"[LLMReasoner Notice] {target_model} rate limited (429). Instantly switching model...")
                        continue
                    else:
                        print(f"[LLMReasoner Notice] {target_model} exception: {e}.")
                        break

            # Fallback parser if API rate limits persist
            print("[LLMReasoner Notice] Utilizing Token-Proximity NLP Fallback.")
            return self._token_proximity_nlp_parser(agent_goal, available_catalog, spending_cap_inr, exclude_ids, catalog_products)
        else:
            return self._token_proximity_nlp_parser(agent_goal, available_catalog, spending_cap_inr, exclude_ids, catalog_products)

    def _token_proximity_nlp_parser(
        self,
        agent_goal: str,
        available_catalog: List[Dict[str, Any]],
        spending_cap_inr: float,
        exclude_product_ids: Optional[List[str]] = None,
        full_catalog: Optional[List[Dict[str, Any]]] = None
    ) -> AgentChoice:
        goal_lower = agent_goal.lower()
        tokens = re.findall(r'\b[\w\-]+\b', goal_lower)
        exclude_ids = exclude_product_ids or []
        all_catalog = full_catalog or available_catalog

        word_to_num = {
            "one": 1, "a": 1, "an": 1, "single": 1,
            "two": 2, "pair": 2, "couple": 2,
            "three": 3, "trio": 3, "triple": 3,
            "four": 4, "quad": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }

        matched_products: List[Dict[str, Any]] = []
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

            matched_products.append(p)

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

        if not selected_items and matched_products:
            m_p = matched_products[0]
            reasoning_str = f"Rule-based Intent Parser: Requested item '{m_p['name']}' (₹{m_p['price_inr']:.2f}) exceeds spending cap of ₹{spending_cap_inr:.2f}."
            return AgentChoice(
                items=[],
                reasoning=reasoning_str,
                reasoning_source="RULE_FALLBACK",
                stock_warnings=stock_warnings
            )

        if not selected_items and not matched_products:
            first_in_budget = next((p for p in available_catalog if p["price_inr"] <= spending_cap_inr), None)
            if first_in_budget:
                selected_items.append(AgentItemSelection(product_id=first_in_budget["id"], quantity=1, requested_quantity=1))
                running_total = first_in_budget["price_inr"]
                item_descriptions.append(f"1x '{first_in_budget['name']}' (₹{running_total:.2f})")

        remaining = spending_cap_inr - running_total
        reasoning_prefix = ""
        if exclude_ids:
            ex_names = ", ".join([next((p["name"] for p in all_catalog if p["id"] == eid), eid) for eid in exclude_ids])
            reasoning_prefix = f"⚠️ [STOCKOUT RECOVERED]: Primary item '{ex_names}' hit 0 stock. Automatically recovered by selecting in-stock alternative: "

        reasoning_str = f"{reasoning_prefix}Selected {', '.join(item_descriptions)}. Combined Total: ₹{running_total:.2f}, Remaining Cap Balance: ₹{remaining:.2f}."
        if stock_warnings:
            reasoning_str += " " + " ".join(stock_warnings)

        return AgentChoice(
            items=selected_items,
            reasoning=reasoning_str,
            reasoning_source="RULE_FALLBACK",
            stock_warnings=stock_warnings
        )
