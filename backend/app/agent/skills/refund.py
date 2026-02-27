import json
import os
import random
from datetime import datetime
from langchain_core.tools import tool

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_work_orders() -> list[dict]:
    with open(os.path.join(DATA_DIR, "work_orders.json"), "r") as f:
        return json.load(f)


def _load_policies() -> dict:
    with open(os.path.join(DATA_DIR, "manufacturing_policies.json"), "r") as f:
        return json.load(f)


@tool
def defect_report(work_order_id: str, defect_description: str, severity: str = "major") -> str:
    """Log a quality defect or issue against a specific work order.
    Use this tool when someone reports a defect, quality issue, or
    non-conformance on a manufactured part.
    Provide the work order ID (e.g., 'WO-2001'), a description of the defect,
    and the severity level: 'critical', 'major', or 'minor'.
    """
    work_orders = _load_work_orders()
    policies = _load_policies()
    quality_policy = policies["quality_policy"]

    # Find the work order
    wo = None
    for w in work_orders:
        if w["work_order_id"].upper() == work_order_id.upper():
            wo = w
            break

    if not wo:
        return json.dumps({
            "logged": False,
            "reason": f"Work order {work_order_id} not found. Please verify the ID."
        })

    if wo["status"] == "cancelled":
        return json.dumps({
            "logged": False,
            "reason": f"Work order {work_order_id} has been cancelled. Cannot log defects against cancelled orders."
        })

    ncr_number = f"NCR-{random.randint(10000, 99999)}"
    severity_lower = severity.lower()
    defect_class = quality_policy["defect_classes"].get(severity_lower, quality_policy["defect_classes"]["major"])

    # Determine action based on severity
    actions = {
        "critical": "Part must be SCRAPPED. Production PAUSED for root cause analysis. Engineering review required within 2 hours.",
        "major": "Part QUARANTINED for engineering review. May be reworkable. Corrective action plan due within 24 hours.",
        "minor": "Part flagged for concession review. Production may continue. Document with photos."
    }
    action = actions.get(severity_lower, actions["major"])

    # Check if corrective action threshold is reached
    total_defects = wo["defects_found"] + 1
    threshold_reached = total_defects >= 3

    return json.dumps({
        "logged": True,
        "ncr_number": ncr_number,
        "work_order_id": work_order_id.upper(),
        "product_name": wo["product_name"],
        "machine": wo["machine_assigned"],
        "operator": wo["operator"],
        "severity": severity_lower,
        "classification": defect_class,
        "defect_description": defect_description,
        "action_required": action,
        "total_defects_on_wo": total_defects,
        "corrective_action_triggered": threshold_reached,
        "created_at": datetime.now().isoformat(),
        "summary": (
            f"Defect report {ncr_number} logged against {work_order_id}. "
            f"Severity: {severity_lower.upper()}. {action} "
            + (f"⚠️ Corrective action threshold reached ({total_defects} defects on this WO)." if threshold_reached else "")
        )
    }, indent=2)
