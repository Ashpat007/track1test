"""
Human/Code Gating Checkpoint.
Serves as the explicit decision gate (Human-in-the-loop or Code Gating) before payment clearance is granted to the Merchant API.
Renders itemized pricing breakdown, spending cap limits, remaining balance, and inventory warnings.
"""

import sys
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


class GatingCheckpoint:
    def __init__(self, mode: str = "CLI"):
        """
        mode: 'CLI' (interactive prompt) or 'AUTO_APPROVE' (for automated testing suites).
        """
        self.mode = mode

    def request_approval(
        self,
        product_summary: str,
        total_amount_inr: float,
        llm_reasoning: str,
        spending_cap_inr: float,
        items_detail: List[Dict[str, Any]],
        stock_warnings: Optional[List[str]] = None
    ) -> bool:
        """
        Presents the Gating Clearance Panel to the human reviewer / system checkpoint.
        """
        remaining_balance = spending_cap_inr - total_amount_inr

        panel_lines = [
            f"[bold cyan]Selected Items Bundle:[/bold cyan]"
        ]

        for item in items_detail:
            v_str = f" ({item['variant_name']})" if item.get("variant_name") else ""
            panel_lines.append(f"  • {item['quantity']}x {item['product_name']}{v_str} — [bold green]₹{item['subtotal_inr']:.2f}[/bold green]")

        panel_lines.extend([
            "",
            f"[bold white]Total Order Cost:[/bold white] [bold green]₹{total_amount_inr:.2f}[/bold green]",
            f"[bold white]Spending Cap Limit:[/bold white] ₹{spending_cap_inr:.2f}",
            f"[bold white]Remaining Cap Balance:[/bold white] [bold yellow]₹{remaining_balance:.2f}[/bold yellow]",
            f"[bold white]LLM Reasoning:[/bold white] [italic]{llm_reasoning}[/italic]"
        ])

        if stock_warnings:
            panel_lines.append("")
            for warn in stock_warnings:
                panel_lines.append(f"[bold yellow]⚠️ INVENTORY NOTICE:[/bold yellow] [bold orange1]{warn}[/bold orange1]")

        panel_content = "\n".join(panel_lines)

        try:
            console.print()
            console.print(Panel(
                panel_content,
                title="[bold red]GUARDRAIL CHECKPOINT — HUMAN / CODE GATING GATE[/bold red]",
                border_style="red"
            ))
        except Exception:
            pass

        if self.mode == "AUTO_APPROVE":
            try:
                console.print("[dim][GATING GATE] Mode is AUTO_APPROVE. Automatically granting clearance for execution.[/dim]")
            except Exception:
                pass
            return True

        # Interactive CLI Human Gate Prompt
        try:
            approved = Confirm.ask("\n[bold yellow]Execute payment transaction with Razorpay Test API?[/bold yellow]", default=True)
            if approved:
                return True
            else:
                return False
        except Exception:
            return True
