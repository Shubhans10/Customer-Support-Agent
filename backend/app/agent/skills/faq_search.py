import json
import os
from langchain_core.tools import tool

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_faqs() -> list[dict]:
    with open(os.path.join(DATA_DIR, "faqs.json"), "r") as f:
        return json.load(f)


@tool
def faq_search(query: str) -> str:
    """Search the FAQ knowledge base for answers to common customer questions.
    Use this tool when the customer asks general questions about policies,
    shipping, payments, account management, or product information.
    Provide a natural language query describing what the customer wants to know.
    """
    faqs = _load_faqs()
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # Score each FAQ by keyword overlap
    scored = []
    for faq in faqs:
        faq_text = (faq["question"] + " " + faq["answer"] + " " + faq["category"]).lower()
        faq_words = set(faq_text.split())
        overlap = len(query_words & faq_words)
        if overlap > 0:
            scored.append((overlap, faq))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:3]

    if not top_results:
        return json.dumps({
            "found": False,
            "summary": "No matching FAQ entries found for your question. Let me try to help you directly or escalate to a specialist."
        })

    results = []
    for _, faq in top_results:
        results.append({
            "question": faq["question"],
            "answer": faq["answer"],
            "category": faq["category"]
        })

    return json.dumps({
        "found": True,
        "count": len(results),
        "results": results,
        "summary": f"Found {len(results)} relevant FAQ entries."
    }, indent=2)
