"""
Interactive CLI Demo Runner for Razorpay Buildathon Track 01 Submission.
Displays Merchant Catalog Details, Agent Spec Discovery, Gemini LLM Reasoning,
Deterministic Guardrail Checks, Human Gating Panel, Autonomous Upsell Recommendations,
Multi-Merchant Federated Cross-Store Stockout Recovery (Store A ➔ Store B), Razorpay Test Order Creation, and Audit Trail.
"""

import sys
import os
import re
import time
import threading
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

# Set stdout encoding for Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from merchant_api.app import app as merchant_app, CATALOG_DB, STORE_B_CATALOG_DB
from buyer_agent.agent import BuyerAgent
from buyer_agent.client import MerchantClient
from buyer_agent.llm_reasoner import AgentChoice, AgentItemSelection
from guardrails.audit import AuditLogger

console = Console(force_terminal=True)
SERVER_PORT = 8000
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"


def start_merchant_server():
    """Starts FastAPI merchant server in a background thread."""
    config = uvicorn.Config(merchant_app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5)
    return server


def display_merchant_banner_and_catalog():
    """Displays rich table of merchant products so the user/judge sees the product details."""
    console.clear()
    console.print(Panel.fit(
        "[bold green]AURA ARTISAN TEAS & BOTANICALS[/bold green]\n"
        "[italic cyan]Agent-Readable Commerce API & Autonomous Machine-to-Machine Payments[/italic cyan]\n"
        "[yellow]Razorpay AI Buildathon — Track 01: AI Growth & Agentic Commerce[/yellow]",
        border_style="green"
    ))

    table = Table(title="Merchant Catalog A: Aura Artisan Teas (Primary)", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Product Name", style="bold white", width=32)
    table.add_column("Category", style="cyan", width=16)
    table.add_column("Price (INR)", style="bold green", justify="right", width=12)
    table.add_column("Stock", justify="center", width=8)
    table.add_column("Variants / Attributes", style="yellow")

    for p in CATALOG_DB.values():
        var_str = ", ".join([v["name"] for v in p.get("variants", [])]) or "Standard Pack"
        flavor_str = ", ".join(p["attributes"].get("flavor_notes", []))
        caffeine = p["attributes"].get("caffeine_level", "N/A")
        stock_display = f"[bold green]{p['stock_qty']}[/bold green]" if p['stock_qty'] > 0 else "[bold red]0 (OUT)[/bold red]"
        
        table.add_row(
            p["id"],
            p["name"],
            p["category"],
            f"₹{p['price_inr']:.2f}",
            stock_display,
            f"[bold]{var_str}[/bold]\n[dim]Flavors: {flavor_str} | Caffeine: {caffeine}[/dim]"
        )

    console.print(table)
    console.print()

    # Display Federated Merchant B Catalog
    table_b = Table(title="Merchant Catalog B: Botanical Leaf Co. (Federated Partner Merchant)", show_header=True, header_style="bold cyan")
    table_b.add_column("ID", style="dim", width=14)
    table_b.add_column("Product Name", style="bold white", width=38)
    table_b.add_column("Category", style="cyan", width=16)
    table_b.add_column("Price (INR)", style="bold green", justify="right", width=12)
    table_b.add_column("Stock", justify="center", width=8)

    for p in STORE_B_CATALOG_DB.values():
        table_b.add_row(
            p["id"],
            p["name"],
            p["category"],
            f"₹{p['price_inr']:.2f}",
            f"[bold green]{p['stock_qty']}[/bold green]"
        )

    console.print(table_b)
    console.print()


def display_agent_discovered_spec():
    """Shows what the agent discovers when calling GET /agent-spec."""
    client = MerchantClient(base_url=SERVER_URL)
    try:
        spec = client.get_agent_spec()
        spec_panel = (
            f"[bold cyan]API Version:[/bold cyan] {spec['api_version']}\n"
            f"[bold cyan]Currency Standard:[/bold cyan] {spec['currency']} ({spec['price_unit']})\n"
            f"[bold cyan]Supported Actions:[/bold cyan] {', '.join(spec['supported_actions'])}\n"
            f"[bold cyan]Stock Reservation Policy:[/bold cyan] {spec['stock_reservation_minutes']} mins\n"
            f"[bold cyan]Deterministic Guardrails & Gating Required:[/bold cyan] [bold green]{spec['gating_required']}[/bold green]\n"
            f"[bold cyan]Federated Merchants:[/bold cyan] Store A (Aura Artisan Teas) & Store B (Botanical Leaf Co.)"
        )
        console.print(Panel(spec_panel, title="[bold blue]Agent API Specification Discovery (GET /agent-spec)[/bold blue]", border_style="blue"))
    except Exception as e:
        console.print(f"[bold red]Failed to reach agent spec: {e}[/bold red]")


def display_audit_logs_summary(session_id: str):
    """Displays a clean, de-duplicated step-by-step timeline of SQL Audit logs where each step card shows strictly relevant details."""
    if not session_id:
        return
    logger = AuditLogger(session_id=session_id)
    history = logger.get_session_history()

    console.print()
    console.print(Panel(f"[bold gold1]📋 DURABLE SQL AUDIT TRAIL TIMELINE — Session ID: {session_id}[/bold gold1]", border_style="gold1"))

    step_icons = {
        "CATALOG_SEARCH": "🔍",
        "LLM_REASONING": "🧠",
        "GUARDRAIL_EVALUATION": "🛡️",
        "USER_GATING": "🛑",
        "PAYMENT_EXECUTION": "💳",
        "FEDERATED_PAYMENT_EXECUTION": "🌐",
        "FAILURE_HANDLED": "⚠️"
    }

    for idx, r in enumerate(history, 1):
        stype = r["step_type"]
        icon = step_icons.get(stype, "📌")
        outcome = r["outcome_status"]
        lines = [f"[bold cyan]Step {idx}: {icon} {stype}[/bold cyan]"]

        if stype == "CATALOG_SEARCH":
            lines.append(f"  [bold white]Action:[/bold white] Queried Agent-Readable Product Catalog (`GET /catalog`)")
            lines.append(f"  [bold green]Outcome:[/bold green] Catalog API Online & Unreserved Stock Filtered")

        elif stype == "LLM_REASONING":
            lines.append(f"  [bold white]Proposed Action:[/bold white] {r['proposed_action']}")
            if r["llm_reasoning"]:
                lines.append(f"  [bold yellow]LLM Reasoning:[/bold yellow] [italic]{r['llm_reasoning']}[/italic]")
            if r["proposed_amount_inr"]:
                lines.append(f"  [bold green]Proposed Amount:[/bold green] ₹{r['proposed_amount_inr']:.2f}")

        elif stype == "GUARDRAIL_EVALUATION":
            g_pass = "[bold green]PASS[/bold green]" if r["guardrail_passed"] else "[bold red]BLOCKED[/bold red]"
            lines.append(f"  [bold magenta]Guardrail Status:[/bold magenta] {g_pass}")
            lines.append(f"  [bold white]Rule Check:[/bold white] {r['guardrail_message'] or 'Rules satisfied'}")
            if r["proposed_amount_inr"]:
                lines.append(f"  [bold green]Proposed Amount:[/bold green] ₹{r['proposed_amount_inr']:.2f}")

        elif stype == "USER_GATING":
            gate_status = r["gate_status"]
            g_color = "green" if gate_status == "APPROVED" else "red"
            lines.append(f"  [bold {g_color}]Human Review Checkpoint:[/bold {g_color}] Gating Clearance {gate_status}")

        elif stype in ["PAYMENT_EXECUTION", "FEDERATED_PAYMENT_EXECUTION"]:
            lines.append(f"  [bold white]Action:[/bold white] Executed Checkout & Razorpay Test Payment Verification")
            if r["proposed_action"]:
                lines.append(f"  [bold white]Items:[/bold white] {r['proposed_action']}")
            if r["razorpay_order_id"]:
                lines.append(f"  [bold cyan]Razorpay Order ID:[/bold cyan] {r['razorpay_order_id']}")
            lines.append(f"  [bold green]Payment Verification Mode:[/bold green] SIMULATED_TEST_SIGNATURE (HMAC SHA256)")
            lines.append(f"  [bold green]Outcome:[/bold green] [bold white]{outcome}[/bold white]")

        else:
            lines.append(f"  [bold white]Action:[/bold white] {r['proposed_action']}")
            lines.append(f"  [bold white]Outcome:[/bold white] {outcome}")

        panel_color = "green" if outcome in ["SUCCESS", "PASSED", "APPROVED", "FEDERATED_TEST_SUCCESS", "SIMULATED_TEST_SUCCESS"] else ("yellow" if "PROPOSED" in outcome else "red")
        console.print(Panel("\n".join(lines), border_style=panel_color, expand=False))
        console.print()


def run_interactive_demo():
    console.print("[dim]Starting local FastAPI Merchant Server...[/dim]")
    start_merchant_server()

    while True:
        display_merchant_banner_and_catalog()
        display_agent_discovered_spec()

        console.print("[bold yellow]Select a Demo Scenario:[/bold yellow]")
        console.print("1. [bold green]Successful Purchase Flow[/bold green] (Pre-set Goal: \"Get a caffeine-free herbal tea for sleep under ₹500\")")
        console.print("2. [bold magenta]Guardrail Spending Cap Block & Autonomous Upsell Recovery[/bold magenta] (Matcha ₹950 vs ₹500 cap)")
        console.print("3. [bold orange1]Multi-Merchant Cross-Store Stockout Recovery[/bold orange1] (Store A Stockout ➔ Auto Failover to Store B)")
        console.print("4. [bold cyan]Custom Goal & Multi-Store Search[/bold cyan] (Type your prompt & spending limit)")
        console.print("5. [bold red]Exit Demo[/bold red]")

        choice = Prompt.ask("\nEnter choice [1/2/3/4/5]", choices=["1", "2", "3", "4", "5"], default="1")

        if choice == "5":
            console.print("\n[bold green]👋 Thank you for testing Aura Artisan Teas & Botanicals Agentic Commerce System! Goodbye![/bold green]")
            sys.exit(0)

        if choice == "1":
            spending_cap = 500.0
            goal = "Get a caffeine-free herbal tea for sleep under ₹500"
            agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=spending_cap, gating_mode="CLI")
            console.print(f"\n[bold green]Running Scenario 1:[/bold green] Goal = '{goal}' | Spending Cap = ₹{spending_cap:.2f}")
            res = agent.execute_purchase_goal(goal)
            display_audit_logs_summary(res.get("session_id", res.get("audit_session_id")))

        elif choice == "2":
            spending_cap = 500.0
            goal = "Buy Japanese Ceremonial Matcha Grade-A"
            agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=spending_cap, gating_mode="CLI")
            console.print(f"\n[bold magenta]Running Scenario 2 (Guardrail Block & Autonomous Upsell Recovery):[/bold magenta]")
            console.print(f"Goal = '{goal}' | Initial Spending Cap = ₹{spending_cap:.2f} (Matcha is ₹950.00)")
            
            res = agent.execute_purchase_goal(goal)
            up = res.get("upsell_proposal")

            if up:
                console.print(Panel.fit(
                    f"[bold yellow]🛍️ AUTONOMOUS REVENUE GROWTH & UPSELL PROPOSAL[/bold yellow]\n\n"
                    f"[white]{up['recommendation_reasoning']}[/white]\n\n"
                    f"[bold green]Option 1 (Cross-Sell / Downsell):[/bold green] Accept In-Budget Alternative '[bold cyan]{up['alternative_product_name']}[/bold cyan]' (₹{up['alternative_product_price_inr']:.2f})\n"
                    f"[bold magenta]Option 2 (Revenue Upsell):[/bold magenta] Upgrade Spending Cap to [bold yellow]₹{up['suggested_cap_increase_inr']:.2f}[/bold yellow] & Purchase '[bold cyan]{up['breached_product_name']}[/bold cyan]'\n"
                    f"[bold red]Option 3:[/bold red] Decline Recommendation",
                    title="Revenue Growth & Upsell Opportunities",
                    border_style="magenta"
                ))

                opt = Prompt.ask("\nSelect Recommendation Option [1/2/3]", choices=["1", "2", "3"], default="1")
                
                if opt == "1":
                    alt_choice = AgentChoice(
                        items=[AgentItemSelection(**i) for i in up["alternative_items"]],
                        reasoning=f"User accepted in-budget alternative '{up['alternative_product_name']}'",
                        reasoning_source="GEMINI_3.6_FLASH"
                    )
                    res_alt = agent.execute_preapproved_choice(choice=alt_choice, agent_goal=goal)
                    console.print(f"\n[bold green]✓ Purchase Completed:[/bold green] Purchased {res_alt.get('summary_names')} for ₹{res_alt.get('amount_inr'):.2f}")
                    display_audit_logs_summary(res_alt.get("session_id"))
                elif opt == "2":
                    upgraded_agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=up["suggested_cap_increase_inr"], gating_mode="CLI")
                    up_choice = AgentChoice(
                        items=[AgentItemSelection(product_id=up["breached_product_id"], quantity=1)],
                        reasoning=f"User upgraded spending cap to ₹{up['suggested_cap_increase_inr']:.2f} to unlock '{up['breached_product_name']}'",
                        reasoning_source="GEMINI_3.6_FLASH"
                    )
                    res_up = upgraded_agent.execute_preapproved_choice(choice=up_choice, agent_goal=goal)
                    console.print(f"\n[bold magenta]🚀 Revenue Upsell Successful:[/bold magenta] Upgraded cap to ₹{up['suggested_cap_increase_inr']:.2f} and purchased {res_up.get('summary_names')} for ₹{res_up.get('amount_inr'):.2f}")
                    display_audit_logs_summary(res_up.get("session_id"))
                else:
                    console.print("[bold red]Decline registered.[/bold red] Transaction aborted.")
            else:
                display_audit_logs_summary(res.get("session_id"))

        elif choice == "3":
            spending_cap = 500.0
            goal = "Buy Kashmiri Kahwa Saffron Blend"
            agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=spending_cap, gating_mode="CLI")
            console.print(f"\n[bold orange1]Running Scenario 3 (Multi-Merchant Cross-Store Stockout Recovery):[/bold orange1]")
            
            client = MerchantClient(base_url=SERVER_URL)
            client.simulate_stockout("tea-001")
            console.print("[bold yellow]SIMULATION INJECTED: Depleted stock of Kashmiri Kahwa (tea-001) in Store A (Aura Artisan Teas) to 0![/bold yellow]")

            res = agent.execute_purchase_goal(goal)
            if res.get("federated_failover"):
                console.print(f"\n[bold green]🌐 FEDERATED CROSS-MERCHANT PURCHASE COMPLETED:[/bold green] Purchased [bold white]{res.get('summary_names')}[/bold white] for [bold green]₹{res.get('amount_inr'):.2f}[/bold green] via [bold cyan]{res.get('store_name')}[/bold cyan]!")
                console.print(f"[bold cyan]Razorpay Order ID:[/bold cyan] {res.get('razorpay_order_id')}")
                console.print(f"[bold cyan]Payment ID:[/bold cyan] {res.get('razorpay_payment_id')}")
            display_audit_logs_summary(res.get("session_id", res.get("audit_session_id")))

        elif choice == "4":
            console.print("\n[bold cyan]--- CUSTOM SHOPPING GOAL (MULTI-STORE DISCOVERY) ---[/bold cyan]")
            goal = Prompt.ask("Step 1/2: Enter your Shopping Goal")
            
            cap_str = Prompt.ask("Step 2/2: Enter your Max Spending Limit in ₹ INR")
            try:
                spending_cap = float(cap_str.replace("₹", "").replace("Rs", "").strip())
            except ValueError:
                spending_cap = 1500.0

            agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=spending_cap, gating_mode="CLI")
            console.print(f"\n[bold cyan]Executing Custom Scenario:[/bold cyan] Goal = '{goal}' | Max Spending Limit = ₹{spending_cap:.2f}")
            res = agent.execute_purchase_goal(goal)
            display_audit_logs_summary(res.get("session_id", res.get("audit_session_id")))

        console.print("\n[bold dim]------------------------------------------------------------[/bold dim]")
        Prompt.ask("[bold yellow]Press Enter to return to the Main Menu...[/bold yellow]", default="")


if __name__ == "__main__":
    run_interactive_demo()
