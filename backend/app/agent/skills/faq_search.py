import json
import os
from langchain_core.tools import tool

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_knowledge_base() -> list[dict]:
    with open(os.path.join(DATA_DIR, "knowledge_base.json"), "r") as f:
        return json.load(f)


@tool
def knowledge_base_search(query: str) -> str:
    """Search the manufacturing knowledge base for SOPs, safety protocols,
    quality procedures, maintenance guides, and material specifications.
    Use this tool when someone asks about procedures, safety requirements,
    how to operate equipment, or any manufacturing-related question.
    Provide a natural language query describing what information is needed.
    """
    entries = _load_knowledge_base()
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # Score each entry by keyword overlap
    scored = []
    for entry in entries:
        entry_text = (entry["question"] + " " + entry["answer"] + " " + entry["category"]).lower()
        entry_words = set(entry_text.split())
        overlap = len(query_words & entry_words)
        if overlap > 0:
            scored.append((overlap, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:3]

    if not top_results:
        return json.dumps({
            "found": False,
            "summary": "No matching knowledge base entries found. Consider escalating to engineering for specialized guidance."
        })

    results = []
    for _, entry in top_results:
        results.append({
            "id": entry["id"],
            "question": entry["question"],
            "answer": entry["answer"],
            "category": entry["category"]
        })

    return json.dumps({
        "found": True,
        "count": len(results),
        "results": results,
        "summary": f"Found {len(results)} relevant knowledge base entries."
    }, indent=2)
