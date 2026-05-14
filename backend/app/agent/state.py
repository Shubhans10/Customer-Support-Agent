from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


def _merge_token_usage(existing: dict, new: dict) -> dict:
    """Merge token usage dicts, summing values for matching keys and appending node breakdowns."""
    merged = dict(existing) if existing else {}
    if not new:
        return merged

    # Sum top-level counters
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        merged[key] = merged.get(key, 0) + new.get(key, 0)

    # Append per-node breakdown entries
    if "nodes" not in merged:
        merged["nodes"] = []
    if "nodes" in new:
        merged["nodes"].extend(new["nodes"])

    return merged


class AgentState(TypedDict):
    """State schema for the customer support agent graph."""
    messages: Annotated[list[BaseMessage], add_messages]
    token_usage: Annotated[dict, _merge_token_usage]
