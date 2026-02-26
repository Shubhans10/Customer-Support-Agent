from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.skills.order_lookup import order_lookup
from app.agent.skills.refund import process_refund
from app.agent.skills.faq_search import faq_search
from app.agent.skills.escalation import escalate_to_human
from app.agent.skills.sentiment import analyze_sentiment
from app.config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE

# All agent skills (tools)
tools = [order_lookup, process_refund, faq_search, escalate_to_human, analyze_sentiment]

SKILL_DESCRIPTIONS = {
    "order_lookup": {
        "name": "Order Lookup",
        "description": "Search for order details by order ID or customer name",
        "icon": "📦"
    },
    "process_refund": {
        "name": "Refund Processing",
        "description": "Process refund requests based on store policies",
        "icon": "💳"
    },
    "faq_search": {
        "name": "FAQ Search",
        "description": "Search the knowledge base for answers to common questions",
        "icon": "📖"
    },
    "escalate_to_human": {
        "name": "Escalation",
        "description": "Escalate complex issues to a human support agent",
        "icon": "🙋"
    },
    "analyze_sentiment": {
        "name": "Sentiment Analysis",
        "description": "Analyze customer emotional tone to adjust response",
        "icon": "🎭"
    }
}


def _create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=TEMPERATURE,
        api_key=OPENAI_API_KEY,
        streaming=True,
    )


def _agent_node(state: AgentState) -> dict:
    """Run the LLM agent with tools bound."""
    llm = _create_llm()
    llm_with_tools = llm.bind_tools(tools)

    messages = state["messages"]
    # Prepend system prompt if not already there
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def _should_continue(state: AgentState) -> str:
    """Determine whether to route to tools or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def build_graph() -> StateGraph:
    """Build and compile the LangGraph agent graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", ToolNode(tools))

    # Set entry point
    graph.set_entry_point("agent")

    # Add conditional edge from agent
    graph.add_conditional_edges(
        "agent",
        _should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )

    # After tools, loop back to agent
    graph.add_edge("tools", "agent")

    return graph.compile()


# Pre-compiled graph instance
agent_graph = build_graph()
