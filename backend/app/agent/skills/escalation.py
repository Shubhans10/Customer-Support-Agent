import json
import random
from datetime import datetime
from langchain_core.tools import tool


@tool
def escalate_to_human(reason: str, priority: str = "medium", department: str = "General Support") -> str:
    """Escalate the conversation to a human support agent.
    Use this tool when:
    - The customer explicitly asks to speak with a human/manager
    - The issue is too complex to resolve automatically
    - The customer is very frustrated or angry
    - The issue involves a policy exception
    Provide a clear reason for escalation, priority level (low/medium/high/urgent),
    and the target department (Billing, Technical Support, Shipping, Management).
    """
    ticket_number = f"ESC-{random.randint(10000, 99999)}"

    wait_times = {
        "low": "30-45 minutes",
        "medium": "15-20 minutes",
        "high": "5-10 minutes",
        "urgent": "1-3 minutes"
    }

    estimated_wait = wait_times.get(priority.lower(), "15-20 minutes")

    return json.dumps({
        "escalated": True,
        "ticket_number": ticket_number,
        "department": department,
        "priority": priority,
        "reason": reason,
        "estimated_wait_time": estimated_wait,
        "created_at": datetime.now().isoformat(),
        "summary": (
            f"Escalation ticket {ticket_number} has been created. "
            f"Department: {department}. Priority: {priority}. "
            f"Estimated wait time: {estimated_wait}. "
            f"A human agent will review your case shortly."
        )
    }, indent=2)
