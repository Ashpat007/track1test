"""
Interactive CLI Demo Runner for Razorpay Buildathon Track 01 Submission.
Displays Merchant Catalog Details, Agent Spec Discovery, Gemini LLM Reasoning,
Deterministic Guardrail Checks, Human Gating Panel, Autonomous Upsell Recommendations, Razorpay Test Order Creation, and Audit Trail.
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

from merchant_api.app import app as merchant_app, CATALOG_DB
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

    table = Table(title="Merchant Product Catalog (Agent-Readable Data)", show_header=True, header_style="bold magenta")
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
            f"[bold cyan]Deterministic Guardrails & Gating Required:[/bold cyan] [bold green]{spec['gating_required']}[/bold green]"
        )
        console.print(Panel(spec_panel, title="[bold blue]Agent API Specification Discovery (GET /agent-spec)[/bold blue]", border_style="blue"))
    except Exception as e:
        console.print(f"[bold red]Failed to fetch agent spec: {e}[/bold red]")


def display_audit_logs_summary(session_id: str):
    """Displays a clean, ultra-readable step-by-step timeline of SQL Audit logs."""
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
        "FAILURE_HANDLED": "⚠️"
    }

    for idx, r in enumerate(history, 1):
        icon = step_icons.get(r["step_type"], "📌")
        stype = r["step_type"]
        g_pass = "[bold green]PASS[/bold green]" if r["guardrail_passed"] else "[bold red]BLOCKED[/bold red]"
        gate_status = r["gate_status"]
        outcome = r["outcome_status"]

        lines = [
            f"[bold cyan]Step {idx}: {icon} {stype}[/bold cyan]",
            f"  [bold white]Action:[/bold white] {r['proposed_action'] or 'Executed endpoint call'}"
        ]

        if r["llm_reasoning"]:
            lines.append(f"  [bold yellow]LLM Reasoning:[/bold yellow] [italic]{r['llm_reasoning']}[/italic]")
        
        if r["proposed_amount_inr"]:
            lines.append(f"  [bold green]Proposed Amount:[/bold green] ₹{r['proposed_amount_inr']:.2f}")

        lines.append(f"  [bold magenta]Guardrail Evaluation:[/bold magenta] {g_pass} ({r['guardrail_message'] or 'Rules satisfied'})")

        if gate_status != "N/A":
            lines.append(f"  [bold red]Gating Checkpoint:[/bold red] {gate_status}")

        if r["razorpay_order_id"]:
            lines.append(f"  [bold cyan]Razorpay Order ID:[/bold cyan] {r['razorpay_order_id']}")

        lines.append(f"  [bold green]Step Outcome:[/bold green] [bold white]{outcome}[/bold white]")

        panel_color = "green" if outcome in ["SUCCESS", "PASSED", "APPROVED"] else ("yellow" if "PROPOSED" in outcome else "red")
        console.print(Panel("\n".join(lines), border_style=panel_color, expand=False))
        console.print()


def run_interactive_demo():
    console.print("[dim]Starting local FastAPI Merchant Server...[/dim]")
    start_merchant_server()

    display_merchant_banner_and_catalog()
    display_agent_discovered_spec()

    console.print("[bold yellow]Select a Demo Scenario:[/bold yellow]")
    console.print("1. [bold green]Successful Purchase Flow[/bold green] (Pre-set Goal: Herbal tea under ₹500)")
    console.print("2. [bold red]Guardrail Block Test[/bold red] (Pre-set Goal: Matcha ₹950 exceeding ₹500 cap)")
    console.print("3. [bold orange1]Mid-Purchase Stockout Recovery[/bold orange1] (Simulates sudden stock depletion)")
    console.print("4. [bold magenta]Autonomous Revenue Growth & Upsell Demo[/bold magenta] (In-budget recommendation & cap upgrade)")
    console.print("5. [bold cyan]Custom Shopping Goal & Spending Cap[/bold cyan] (Type your prompt & spending limit)")

    choice = Prompt.ask("\nEnter choice [1/2/3/4/5]", choices=["1", "2", "3", "4", "5"], default="1")

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
        console.print(f"\n[bold red]Running Scenario 2 (Guardrail Block):[/bold red] Goal = '{goal}' | Spending Cap = ₹{spending_cap:.2f}")
        res = agent.execute_purchase_goal(goal)
        display_audit_logs_summary(res.get("session_id"))

    elif choice == "3":
        spending_cap = 500.0
        goal = "Get a caffeine-free herbal tea for sleep under ₹500"
        agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=spending_cap, gating_mode="CLI")
        console.print(f"\n[bold orange1]Running Scenario 3 (Stockout Recovery):[/bold orange1]")
        
        client = MerchantClient(base_url=SERVER_URL)
        client.simulate_stockout("tea-002")
        console.print("[bold yellow]SIMULATION INJECTED: Depleted stock of 'Himalayan Chamomile' (tea-002) to 0![/bold yellow]")

        res = agent.execute_purchase_goal(goal)
        display_audit_logs_summary(res.get("session_id", res.get("audit_session_id")))

    elif choice == "4":
        spending_cap = 500.0
        goal = "Buy Ceremonial Matcha Grade-A"
        agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=spending_cap, gating_mode="CLI")
        console.print(f"\n[bold magenta]Running Scenario 4 (Revenue Upsell & Cross-Sell Engine):[/bold magenta]")
        console.print(f"Goal = '{goal}' | Initial Cap = ₹{spending_cap:.2f} (Matcha is ₹950.00)")
        
        res = agent.execute_purchase_goal(goal)
        up = res.get("upsell_proposal")

        if up:
            console.print(Panel.fit(
                f"[bold yellow]🛍️ AUTONOMOUS REVENUE GROWTH & UPSELL PROPOSAL[/bold yellow]\n\n"
                f"[white]{up['recommendation_reasoning']}[/white]\n\n"
                f"[bold green]Option 1:[/bold green] Accept In-Budget Alternative '[bold cyan]{up['alternative_product_name']}[/bold cyan]' (₹{up['alternative_product_price_inr']:.2f})\n"
                f"[bold magenta]Option 2:[/bold magenta] Upgrade Spending Cap to [bold yellow]₹{up['suggested_cap_increase_inr']:.2f}[/bold yellow] & Purchase '[bold cyan]{up['breached_product_name']}[/bold cyan]'\n"
                f"[bold red]Option 3:[/bold red] Decline Recommendation",
                title="Revenue Growth Opportunities",
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

    elif choice == "5":
        console.print("\n[bold cyan]--- CUSTOM SHOPPING GOAL ---[/bold cyan]")
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

    console.print("\n[bold green]Demo Run Completed![/bold green] You can re-run `python run_demo.py` at any time.")


if __name__ == "__main__":
    run_interactive_demo()
