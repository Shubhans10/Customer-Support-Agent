from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.skills.order_lookup import work_order_lookup
from app.agent.skills.refund import defect_report
from app.agent.skills.faq_search import knowledge_base_search
from app.agent.skills.escalation import escalate_to_engineer
from app.agent.skills.sentiment import equipment_status
from app.config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE

# All agent skills (tools)
tools = [work_order_lookup, equipment_status, defect_report, knowledge_base_search, escalate_to_engineer]

SKILL_DESCRIPTIONS = {
    "work_order_lookup": {
        "name": "Work Order Lookup",
        "description": "Search work orders by ID, product, customer, or status",
        "icon": "📋"
    },
    "equipment_status": {
        "name": "Equipment Status",
        "description": "Check machine health, sensors, and maintenance schedules",
        "icon": "🔧"
    },
    "defect_report": {
        "name": "Defect Report",
        "description": "Log quality defects and non-conformance reports",
        "icon": "🔍"
    },
    "knowledge_base_search": {
        "name": "Knowledge Base",
        "description": "Search SOPs, safety protocols, and procedures",
        "icon": "📖"
    },
    "escalate_to_engineer": {
        "name": "Engineer Escalation",
        "description": "Escalate issues to engineering or management",
        "icon": "🙋"
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
