import json
import random
from datetime import datetime
from langchain_core.tools import tool


@tool
def escalate_to_engineer(reason: str, priority: str = "medium", department: str = "Manufacturing Engineering") -> str:
    """Escalate an issue to a specialist engineer or supervisor.
    Use this tool when:
    - The issue requires engineering expertise (tooling, process, design)
    - A critical defect or safety concern is identified
    - Machine downtime exceeds normal resolution time
    - The operator or user requests specialized support
    Provide a clear reason, priority level (low/medium/high/critical),
    and target department (Manufacturing Engineering, Quality Engineering, Maintenance, Production Management).
    """
    ticket_number = f"ESC-{random.randint(10000, 99999)}"

    response_times = {
        "low": "2-4 hours",
        "medium": "30-60 minutes",
        "high": "15-30 minutes",
        "critical": "Immediate (5-10 minutes)"
    }

    estimated_response = response_times.get(priority.lower(), "30-60 minutes")

    return json.dumps({
        "escalated": True,
        "ticket_number": ticket_number,
        "department": department,
        "priority": priority,
        "reason": reason,
        "estimated_response_time": estimated_response,
        "created_at": datetime.now().isoformat(),
        "summary": (
            f"Escalation ticket {ticket_number} created. "
            f"Department: {department}. Priority: {priority.upper()}. "
            f"Estimated response: {estimated_response}. "
            f"Reason: {reason}. "
            f"An engineer will be dispatched to assist."
        )
    }, indent=2)
