"""
Gemini LLM Catalog Reasoner (Migrated to modern `google.genai` SDK with Multi-Model Quota Fallback & Autonomous Revenue Upsell Engine).
Evaluates natural language goals against raw catalog JSON and outputs structured multi-product cart selections or upside recommendation proposals.
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


class AgentRecommendationProposal(BaseModel):
    budget_breached: bool = False
    breached_product_id: Optional[str] = None
    breached_product_name: Optional[str] = None
    breached_product_price_inr: Optional[float] = None
    alternative_items: List[AgentItemSelection] = Field(default_factory=list)
    alternative_product_name: Optional[str] = None
    alternative_product_price_inr: Optional[float] = None
    suggested_cap_increase_inr: Optional[float] = None
    recommendation_reasoning: Optional[str] = None


class AgentChoice(BaseModel):
    items: List[AgentItemSelection]
    reasoning: str
    reasoning_source: str = "GEMINI_3.6_FLASH"
    stock_warnings: List[str] = Field(default_factory=list)
    upsell_proposal: Optional[AgentRecommendationProposal] = None


class LLMReasoner:
    def __init__(self, model_name: str = "gemini-3.6-flash"):
        self.model_name = model_name
        self.fallback_models = ["gemini-3.5-flash", "gemini-flash-latest"]
        self.client = None
        if GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[LLMReasoner Init Notice] genai.Client init: {e}")

    def generate_upsell_recommendation(
        self,
        agent_goal: str,
        catalog_products: List[Dict[str, Any]],
        spending_cap_inr: float,
        breached_p: Dict[str, Any],
        requested_qty: int = 1
    ) -> AgentRecommendationProposal:
        """
        Generates an autonomous Revenue Growth & Upsell Recommendation Proposal when requested product or quantity exceeds spending cap.
        Provides both an in-budget alternative/quantity (cross-sell) and a spending cap upgrade suggestion (upsell).
        """
        total_breached_price = breached_p["price_inr"] * requested_qty

        if requested_qty > 1 and breached_p["price_inr"] <= spending_cap_inr:
            var_id = breached_p["variants"][0]["id"] if breached_p.get("variants") else None
            alt_name = f"1x {breached_p['name']}"
            alt_price = breached_p["price_inr"]
            alt_items = [AgentItemSelection(product_id=breached_p["id"], variant_id=var_id, quantity=1, requested_quantity=1)]
        else:
            in_budget_products = [p for p in catalog_products if p["price_inr"] <= spending_cap_inr and p["stock_qty"] > 0]
            alt_product = in_budget_products[0] if in_budget_products else None
            alt_items = []
            alt_name = None
            alt_price = 0.0

            if alt_product:
                var_id = alt_product["variants"][0]["id"] if alt_product.get("variants") else None
                alt_price = alt_product["price_inr"] + (alt_product["variants"][0]["price_modifier_inr"] if var_id else 0.0)
                alt_name = alt_product["name"]
                alt_items.append(AgentItemSelection(product_id=alt_product["id"], variant_id=var_id, quantity=1, requested_quantity=1))

        # Suggested spending cap increase to unlock full requested amount
        suggested_cap = float(int(total_breached_price / 100.0) + 1) * 100.0
        display_breached_name = f"{requested_qty}x {breached_p['name']}" if requested_qty > 1 else breached_p["name"]

        rec_reasoning = (
            f"Requested '{display_breached_name}' (₹{total_breached_price:.2f}) exceeds your single action spending cap of ₹{spending_cap_inr:.2f}. "
            f"Recommendation Option A: Purchase in-budget option '{alt_name}' (₹{alt_price:.2f}). "
            f"Recommendation Option B: Upgrade your spending cap to ₹{suggested_cap:.2f} to unlock '{display_breached_name}'."
        )

        return AgentRecommendationProposal(
            budget_breached=True,
            breached_product_id=breached_p["id"],
            breached_product_name=display_breached_name,
            breached_product_price_inr=total_breached_price,
            alternative_items=alt_items,
            alternative_product_name=alt_name,
            alternative_product_price_inr=alt_price,
            suggested_cap_increase_inr=suggested_cap,
            recommendation_reasoning=rec_reasoning
        )

    def select_product_for_goal(
        self,
        agent_goal: str,
        catalog_products: List[Dict[str, Any]],
        spending_cap_inr: float,
        exclude_product_ids: Optional[List[str]] = None
    ) -> AgentChoice:
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

                    engine_tag = "GEMINI_3.6_FLASH"
                    
                    # Check if requested product or total requested quantity exceeds spending cap
                    matched_p = next((p for p in available_catalog if p["id"].lower() in agent_goal.lower() or any(w.lower() in p["name"].lower() for w in agent_goal.split() if len(w) > 3)), None)
                    upsell_prop = None
                    if matched_p:
                        req_q = 1
                        q_m = re.search(r'\b(\d+)\b', agent_goal)
                        if q_m:
                            req_q = int(q_m.group(1))
                        total_req_cost = matched_p["price_inr"] * req_q

                        if total_req_cost > spending_cap_inr:
                            upsell_prop = self.generate_upsell_recommendation(
                                agent_goal, catalog_products, spending_cap_inr, matched_p, requested_qty=req_q
                            )

                    return AgentChoice(
                        items=items,
                        reasoning=reasoning_text,
                        reasoning_source=engine_tag,
                        stock_warnings=warnings,
                        upsell_proposal=upsell_prop
                    )
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        print(f"[LLMReasoner Notice] {target_model} rate limited (429). Instantly switching model...")
                        continue
                    else:
                        print(f"[LLMReasoner Notice] {target_model} exception: {e}.")
                        break

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
                window = tokens[max(0, t_idx - 3) : min(len(tokens), t_idx + 3)]
                for tok in window:
                    if tok.isdigit():
                        val = int(tok)
                        if val < 50:  # Ignore large numbers (like budget caps 700, 1500)
                            req_qty = val
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
            req_q = 1
            q_m = re.search(r'\b(\d+)\b', agent_goal)
            if q_m:
                req_q = int(q_m.group(1))
            upsell_prop = self.generate_upsell_recommendation(agent_goal, all_catalog, spending_cap_inr, m_p, requested_qty=req_q)
            reasoning_str = f"Rule-based Intent Parser: Requested item '{req_q}x {m_p['name']}' (₹{m_p['price_inr'] * req_q:.2f}) exceeds spending cap of ₹{spending_cap_inr:.2f}."
            return AgentChoice(
                items=[],
                reasoning=reasoning_str,
                reasoning_source="RULE_FALLBACK",
                stock_warnings=stock_warnings,
                upsell_proposal=upsell_prop
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

    def explain_agent_decision(self, user_query: str, catalog: List[Dict[str, Any]], recent_history: List[Dict[str, Any]] = None) -> str:
        """
        Answers user conversational queries questioning the agent's reasoning, product attributes, or choices.
        Supports fuzzy product matching for typos (e.g. 'darjeling', 'proce') and precise price & attribute answers.
        """
        q_lower = user_query.lower()

        # Step 1: Check for exact or fuzzy catalog product match
        matched_product = None
        for p in catalog:
            p_name = p["name"].lower()
            p_words = p_name.replace("-", " ").replace("(", "").replace(")", "").split()
            q_words = q_lower.split()

            # Check if any word in query matches product name words
            for qw in q_words:
                if len(qw) > 3:
                    for pw in p_words:
                        if len(pw) > 3 and (qw in pw or pw in qw or (set(qw) & set(pw) == set(pw))):
                            matched_product = p
                            break
                if matched_product:
                    break
            if matched_product:
                break

        # If query asks specifically about price / cost for a matched product
        if matched_product and any(k in q_lower for k in ["price", "proce", "cost", "how much", "rate"]):
            attrs = matched_product.get("attributes", {})
            flavors = ", ".join(attrs.get("flavor_notes", [])) or "Artisanal blend"
            return f"**{matched_product['name']}** is priced at **₹{matched_product['price_inr']:.2f}** ({matched_product['stock_qty']} units in stock). Flavor notes: {flavors}."

        # Step 2: Try Gemini LLM reasoning
        if self.client:
            cat_summary = json.dumps([{
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "price_inr": p["price_inr"],
                "stock_qty": p["stock_qty"],
                "attributes": p.get("attributes", {})
            } for p in catalog], indent=2)

            prompt = (
                "You are Boundly's Autonomous AI Buyer Agent. The user is asking a conversational question about product details, "
                f"flavor profiles, caffeine levels, or pricing.\n\nUser Question: {user_query}\n\nAvailable Merchant Catalog JSON:\n{cat_summary}\n\n"
                "Respond in a helpful, concise, professional 2-3 sentence explanation detailing the exact product flavor notes, caffeine level, pricing, or spending cap compliance."
            )
            for m in [self.model_name] + self.fallback_models:
                try:
                    response = self.client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    pass

        # Step 3: Deterministic Fallback if LLM rate limited
        if matched_product:
            attrs = matched_product.get("attributes", {})
            flavors = ", ".join(attrs.get("flavor_notes", [])) or "Artisanal blend"
            caffeine = attrs.get("caffeine_level", "Standard")
            origin = attrs.get("origin", "Artisan Estate")
            return f"**{matched_product['name']}** (`{matched_product['id']}`) is priced at **₹{matched_product['price_inr']:.2f}** ({matched_product['stock_qty']} in stock). Flavor profile: **{flavors}**, caffeine level: **{caffeine}**, origin: **{origin}**."

        if "why" in q_lower or "reason" in q_lower or "pick" in q_lower or "recommend" in q_lower:
            return "I select products by balancing your goal constraints (such as caffeine level, flavor profile, or stock availability) against your spending cap limit, ensuring maximum cap compliance and zero overdraft risk."
        
        return "We offer artisanal teas including Kashmir Kahwa (saffron, cardamom, cinnamon, almond), Himalayan Chamomile, Imperial Darjeeling, Masala Chai, Ceremonial Matcha, Tulsi Ginger, and Pure Saffron Strands. Ask me about any specific tea or instruct me to make a purchase!"


