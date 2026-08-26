"""
Headless Demo Runner for Agentic Commerce.
Runs Scenario 1 (Happy Path), Scenario 2 (Guardrail Block), and Scenario 3 (Stockout Recovery) automatically.
Prints rich output and SQL Audit logs to terminal.
"""

import sys
import os
import time
import threading
import uvicorn
from rich.console import Console
from rich.panel import Panel

# Set stdout encoding for Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from merchant_api.app import app as merchant_app
from buyer_agent.agent import BuyerAgent
from buyer_agent.client import MerchantClient
from guardrails.audit import AuditLogger

console = Console(force_terminal=True)
SERVER_PORT = 8000
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"


def start_merchant_server():
    config = uvicorn.Config(merchant_app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5)
    return server


def print_audit_trail(session_id: str):
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


def main():
    console.print("[dim]Starting local FastAPI Merchant Server...[/dim]")
    start_merchant_server()

    console.print(Panel.fit(
        "[bold green]AURA ARTISAN TEAS & BOTANICALS — DEMO SUITE[/bold green]\n"
        "[italic cyan]Agent-Readable Commerce API & Autonomous Machine-to-Machine Payments[/italic cyan]\n"
        "[yellow]Razorpay AI Buildathon — Track 01[/yellow]",
        border_style="green"
    ))

    # Scenario 1: Happy Path
    console.print("\n=======================================================")
    console.print("[bold green]SCENARIO 1: Successful Purchase Flow[/bold green]")
    console.print("[yellow]Goal:[/yellow] 'Get a caffeine-free tea under ₹500'")
    console.print("=======================================================")
    
    agent1 = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=500.0, gating_mode="AUTO_APPROVE")
    res1 = agent1.execute_purchase_goal("Get a caffeine-free tea under ₹500")
    print_audit_trail(res1.get("session_id", res1.get("audit_session_id")))

    # Scenario 2: Guardrail Block
    console.print("\n=======================================================")
    console.print("[bold red]SCENARIO 2: Guardrail Spending Cap Breach Block[/bold red]")
    console.print("[yellow]Goal:[/yellow] 'Buy Japanese Ceremonial Matcha Grade-A' (Cap: ₹100)")
    console.print("=======================================================")
    
    agent2 = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=100.0, gating_mode="AUTO_APPROVE")
    res2 = agent2.execute_purchase_goal("Buy Japanese Ceremonial Matcha Grade-A")
    print_audit_trail(res2.get("session_id"))

    # Scenario 3: Stockout Recovery
    console.print("\n=======================================================")
    console.print("[bold orange1]SCENARIO 3: Mid-Purchase Stockout Recovery[/bold orange1]")
    console.print("[yellow]Goal:[/yellow] 'Get a caffeine-free tea under ₹500'")
    console.print("=======================================================")
    
    client = MerchantClient(base_url=SERVER_URL)
    client.simulate_stockout("tea-002")
    console.print("[bold yellow]INJECTED FAILURE: Depleted stock of 'Himalayan Chamomile' (tea-002) to 0![/bold yellow]")

    agent3 = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=500.0, gating_mode="AUTO_APPROVE")
    res3 = agent3.execute_purchase_goal("Get a caffeine-free tea under ₹500")
    print_audit_trail(res3.get("session_id", res3.get("audit_session_id")))

    console.print("\n[bold green]ALL DEMO SCENARIOS EXECUTED SUCCESSFULLY![/bold green]")


if __name__ == "__main__":
    main()
