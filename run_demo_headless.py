"""
Headless Batch Multi-Persona Agent Benchmark Runner.
Executes synthetic buyer personas autonomously through the Merchant API, Guardrails Engine, and Audit Logger at scale.
"""

import sys
import os
import time
import threading
import uvicorn
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from merchant_api.app import app as merchant_app
from buyer_agent.agent import BuyerAgent

SERVER_PORT = 8003
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"
console = Console()


def start_server():
    config = uvicorn.Config(merchant_app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5)


def run_headless_benchmark():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]⚡ HEADLESS MULTI-PERSONA BUYER AGENT BENCHMARK[/bold cyan]\n"
        "[dim]Simulating 6 Synthetic Buyer Personas at Scale via REST API[/dim]",
        border_style="cyan"
    ))

    start_server()

    personas = [
        {
            "name": "Relaxation Seeker",
            "goal": "caffeine-free chamomile lavender sleep tea",
            "cap": 400.0,
            "mode": "AUTO_APPROVE"
        },
        {
            "name": "Spiced Tea Lover",
            "goal": "Kashmiri Kahwa and Masala Chai",
            "cap": 800.0,
            "mode": "AUTO_APPROVE"
        },
        {
            "name": "Luxury Spice Buyer",
            "goal": "1g Kashmiri Pure Saffron Strands",
            "cap": 1000.0,
            "mode": "AUTO_APPROVE"
        },
        {
            "name": "Strict Budget Shopper",
            "goal": "Ceremonial Grade Matcha",
            "cap": 300.0,
            "mode": "AUTO_APPROVE"
        },
        {
            "name": "Multi-Unit Host",
            "goal": "3 units of tea-001",
            "cap": 2000.0,
            "mode": "AUTO_APPROVE"
        },
        {
            "name": "Classic Connoisseur",
            "goal": "Darjeeling First Flush and Earl Grey",
            "cap": 1200.0,
            "mode": "AUTO_APPROVE"
        }
    ]

    results: List[Dict[str, Any]] = []

    for idx, p in enumerate(personas, 1):
        console.print(f"\n[bold yellow][{idx}/{len(personas)}] Running Persona:[/bold yellow] [bold white]{p['name']}[/bold white] (Cap: ₹{p['cap']:.2f})")
        agent = BuyerAgent(merchant_base_url=SERVER_URL, spending_cap_inr=p['cap'], gating_mode=p['mode'])
        
        res = agent.execute_purchase_goal(p['goal'])
        results.append({
            "name": p["name"],
            "goal": p["goal"],
            "cap": p["cap"],
            "success": res.get("success", False),
            "status": res.get("status", "FAILED"),
            "amount": res.get("amount_inr", 0.0),
            "reasoning_source": res.get("reasoning_source", "N/A"),
            "reason": res.get("reason") or res.get("message") or "Success"
        })

    # Summary Benchmark Report Card Table
    table = Table(title="📊 Autonomous Multi-Persona Agent Benchmark Summary", border_style="green", header_style="bold magenta")
    table.add_column("Persona", style="cyan", no_wrap=True)
    table.add_column("Goal", style="white")
    table.add_column("Cap (₹)", justify="right", style="yellow")
    table.add_column("Amount (₹)", justify="right", style="green")
    table.add_column("Engine", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Outcome Details", style="dim")

    total_transacted = 0.0
    total_successful = 0
    total_blocked = 0

    for r in results:
        if r["success"]:
            total_successful += 1
            total_transacted += r["amount"]
            status_str = "[green]SUCCESS ✓[/green]"
        else:
            total_blocked += 1
            status_str = f"[red]{r['status']}[/red]"

        table.add_row(
            r["name"],
            r["goal"],
            f"₹{r['cap']:.2f}",
            f"₹{r['amount']:.2f}" if r["amount"] > 0 else "-",
            r["reasoning_source"],
            status_str,
            str(r["reason"])[:45]
        )

    console.print("\n")
    console.print(table)

    summary_panel = Panel.fit(
        f"[bold green]Total Personas Processed:[/bold green] {len(personas)}\n"
        f"[bold cyan]Successful Transactions:[/bold cyan] {total_successful}\n"
        f"[bold red]Blocked by Guardrails:[/bold red] {total_blocked}\n"
        f"[bold yellow]Total Volume Transacted:[/bold yellow] [bold green]₹{total_transacted:.2f}[/bold green]",
        title="✨ Benchmark Performance Metrics",
        border_style="gold1"
    )
    console.print(summary_panel)


if __name__ == "__main__":
    run_headless_benchmark()
