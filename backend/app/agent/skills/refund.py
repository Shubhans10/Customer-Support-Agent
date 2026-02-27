import json
import os
from datetime import datetime, timedelta
from langchain_core.tools import tool

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_orders() -> list[dict]:
    with open(os.path.join(DATA_DIR, "orders.json"), "r") as f:
        return json.load(f)


def _load_policies() -> dict:
    with open(os.path.join(DATA_DIR, "policies.json"), "r") as f:
        return json.load(f)


@tool
def process_refund(order_id: str, reason: str) -> str:
    """Process a refund request for a given order.
    Use this tool when a customer wants to return an item or get a refund.
    Checks refund eligibility based on store policies and order status.
    Provide the order ID (e.g., 'ORD-1001') and the reason for the refund.
    """
    orders = _load_orders()
    policies = _load_policies()
    refund_policy = policies["refund_policy"]

    # Find the order
    order = None
    for o in orders:
        if o["order_id"].upper() == order_id.upper():
            order = o
            break

    if not order:
        return json.dumps({
            "eligible": False,
            "reason": f"Order {order_id} not found. Please verify the order ID."
        })

    # Check order status
    if order["status"] == "cancelled":
        return json.dumps({
            "eligible": False,
            "order_id": order_id,
            "reason": "This order has already been cancelled. No refund is needed."
        })

    if order["status"] == "returned":
        return json.dumps({
            "eligible": False,
            "order_id": order_id,
            "reason": "This order has already been returned and refunded."
        })

    if order["status"] == "processing":
        return json.dumps({
            "eligible": True,
            "order_id": order_id,
            "action": "cancel_order",
            "summary": (
                f"Order {order_id} is still being processed. "
                f"We can cancel it for a full refund of ${order['total']:.2f}. "
                f"Refund will be processed within 5-7 business days."
            ),
            "refund_amount": order["total"]
        })

    # Check return window for delivered orders
    if order["status"] == "delivered" and order["delivery_date"]:
        delivery_date = datetime.strptime(order["delivery_date"], "%Y-%m-%d")
        days_since = (datetime.now() - delivery_date).days
        window = refund_policy["standard_return_window_days"]

        if days_since > window:
            return json.dumps({
                "eligible": False,
                "order_id": order_id,
                "reason": (
                    f"The {window}-day return window has expired. "
                    f"Item was delivered {days_since} days ago on {order['delivery_date']}."
                )
            })

        return json.dumps({
            "eligible": True,
            "order_id": order_id,
            "action": "initiate_return",
            "summary": (
                f"Order {order_id} is eligible for a refund. "
                f"Delivered {days_since} days ago (within the {window}-day window). "
                f"Refund amount: ${order['total']:.2f}. "
                f"Reason: {reason}. "
                f"A return shipping label will be emailed to {order['customer_email']}."
            ),
            "refund_amount": order["total"],
            "return_label_sent_to": order["customer_email"]
        })

    # Shipped but not delivered
    if order["status"] == "shipped":
        return json.dumps({
            "eligible": True,
            "order_id": order_id,
            "action": "intercept_and_refund",
            "summary": (
                f"Order {order_id} is currently in transit. "
                f"We can attempt to intercept the shipment for a full refund of ${order['total']:.2f}. "
                f"If interception fails, you can return it once delivered."
            ),
            "refund_amount": order["total"]
        })

    return json.dumps({
        "eligible": False,
        "order_id": order_id,
        "reason": f"Unable to process refund for order status: {order['status']}."
    })
