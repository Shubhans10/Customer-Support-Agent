import json
import os
from langchain_core.tools import tool

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_orders() -> list[dict]:
    with open(os.path.join(DATA_DIR, "orders.json"), "r") as f:
        return json.load(f)


@tool
def order_lookup(query: str) -> str:
    """Look up order information by order ID or customer name.
    Use this tool when the customer asks about their order status,
    tracking information, delivery date, or order details.
    The query can be an order ID (e.g., 'ORD-1001') or a customer name (e.g., 'Alice Johnson').
    """
    orders = _load_orders()
    query_lower = query.lower().strip()

    # Search by order ID
    for order in orders:
        if order["order_id"].lower() == query_lower:
            return json.dumps({
                "found": True,
                "order": order,
                "summary": (
                    f"Order {order['order_id']} for {order['customer_name']}: "
                    f"Status is '{order['status']}'. "
                    f"Items: {', '.join(i['name'] for i in order['items'])}. "
                    f"Total: ${order['total']:.2f}. "
                    f"Ordered on {order['order_date']}."
                    + (f" Delivered on {order['delivery_date']}." if order['delivery_date'] else "")
                    + (f" Tracking: {order['tracking_number']}." if order['tracking_number'] else "")
                )
            }, indent=2)

    # Search by customer name
    matches = [o for o in orders if query_lower in o["customer_name"].lower()]
    if matches:
        results = []
        for order in matches:
            results.append({
                "order_id": order["order_id"],
                "status": order["status"],
                "total": order["total"],
                "order_date": order["order_date"],
                "items": [i["name"] for i in order["items"]]
            })
        return json.dumps({
            "found": True,
            "count": len(results),
            "orders": results,
            "summary": f"Found {len(results)} order(s) for '{query}'."
        }, indent=2)

    return json.dumps({
        "found": False,
        "summary": f"No orders found matching '{query}'. Please verify the order ID (format: ORD-XXXX) or customer name."
    })
