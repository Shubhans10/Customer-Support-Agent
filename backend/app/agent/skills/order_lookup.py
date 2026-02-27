import json
import os
from langchain_core.tools import tool

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_work_orders() -> list[dict]:
    with open(os.path.join(DATA_DIR, "work_orders.json"), "r") as f:
        return json.load(f)


@tool
def work_order_lookup(query: str) -> str:
    """Look up work order information by work order ID, product name, customer, or status.
    Use this tool when someone asks about production status, work order details,
    due dates, or progress on manufacturing jobs.
    The query can be a work order ID (e.g., 'WO-2001'), product name, customer name,
    or a status filter (e.g., 'in_progress', 'on_hold', 'completed').
    """
    work_orders = _load_work_orders()
    query_lower = query.lower().strip()

    # Search by work order ID
    for wo in work_orders:
        if wo["work_order_id"].lower() == query_lower:
            progress = (wo["completed_quantity"] / wo["quantity"] * 100) if wo["quantity"] > 0 else 0
            return json.dumps({
                "found": True,
                "work_order": wo,
                "progress_pct": round(progress, 1),
                "summary": (
                    f"Work Order {wo['work_order_id']}: {wo['product_name']} for {wo['customer']}. "
                    f"Status: {wo['status'].upper()}. Priority: {wo['priority']}. "
                    f"Progress: {wo['completed_quantity']}/{wo['quantity']} ({progress:.0f}%). "
                    f"Machine: {wo['machine_assigned']}. Operator: {wo['operator']}. "
                    f"Material: {wo['material']}. "
                    + (f"Due: {wo['due_date']}. " if wo['due_date'] else "")
                    + (f"Defects: {wo['defects_found']}. " if wo['defects_found'] > 0 else "No defects. ")
                    + (f"Notes: {wo['notes']}" if wo['notes'] else "")
                )
            }, indent=2)

    # Search by status
    status_matches = [wo for wo in work_orders if query_lower == wo["status"].lower()]
    if status_matches:
        results = []
        for wo in status_matches:
            progress = (wo["completed_quantity"] / wo["quantity"] * 100) if wo["quantity"] > 0 else 0
            results.append({
                "work_order_id": wo["work_order_id"],
                "product_name": wo["product_name"],
                "customer": wo["customer"],
                "priority": wo["priority"],
                "progress_pct": round(progress, 1),
                "due_date": wo["due_date"]
            })
        return json.dumps({
            "found": True,
            "count": len(results),
            "work_orders": results,
            "summary": f"Found {len(results)} work order(s) with status '{query}'."
        }, indent=2)

    # Search by customer or product name
    text_matches = [
        wo for wo in work_orders
        if query_lower in wo["customer"].lower()
        or query_lower in wo["product_name"].lower()
    ]
    if text_matches:
        results = []
        for wo in text_matches:
            progress = (wo["completed_quantity"] / wo["quantity"] * 100) if wo["quantity"] > 0 else 0
            results.append({
                "work_order_id": wo["work_order_id"],
                "product_name": wo["product_name"],
                "customer": wo["customer"],
                "status": wo["status"],
                "priority": wo["priority"],
                "progress_pct": round(progress, 1)
            })
        return json.dumps({
            "found": True,
            "count": len(results),
            "work_orders": results,
            "summary": f"Found {len(results)} work order(s) matching '{query}'."
        }, indent=2)

    return json.dumps({
        "found": False,
        "summary": f"No work orders found matching '{query}'. Try a work order ID (WO-XXXX), status, customer, or product name."
    })
