from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
import json

from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT, PLANNER_PROMPT
from app.agent.skills.order_lookup import work_order_lookup
from app.agent.skills.refund import defect_report
from app.agent.skills.faq_search import knowledge_base_search
from app.agent.skills.escalation import escalate_to_engineer
from app.agent.skills.sentiment import equipment_status
from app.agent.skills.chart_generator import generate_chart
from app.config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE

# All agent skills (tools)
tools = [work_order_lookup, equipment_status, defect_report, knowledge_base_search, escalate_to_engineer, generate_chart]

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
    },
    "generate_chart": {
        "name": "Chart Generation",
        "description": "Generate performance charts and data visualizations",
        "icon": "📊"
    }
}


def _create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=TEMPERATURE,
        api_key=OPENAI_API_KEY,
        streaming=True,
    )


def _planner_node(state: AgentState) -> dict:
    """Plan which skills to use and in what order."""
    llm = _create_llm()
    messages = state["messages"]
    
    # Get the latest user message
    user_msg = ""
    for msg in reversed(messages):
        if hasattr(msg, 'content') and not isinstance(msg, AIMessage):
            user_msg = msg.content
            break
    
    planner_messages = [
        SystemMessage(content=PLANNER_PROMPT),
        SystemMessage(content=f"User query: {user_msg}")
    ]
    
    response = llm.invoke(planner_messages)
    plan_text = response.content.strip()
    
    # Try to parse the plan
    try:
        # Handle markdown code blocks
        if "```" in plan_text:
            plan_text = plan_text.split("```")[1]
            if plan_text.startswith("json"):
                plan_text = plan_text[4:]
        plan = json.loads(plan_text)
    except (json.JSONDecodeError, IndexError):
        plan = []
    
    # Store plan in a system message so the stream handler can pick it up
    plan_msg = SystemMessage(content=f"__PLAN__:{json.dumps(plan)}")
    return {"messages": [plan_msg]}


def _agent_node(state: AgentState) -> dict:
    """Run the LLM agent with tools bound."""
    llm = _create_llm()
    llm_with_tools = llm.bind_tools(tools)

    messages = state["messages"]
    # Prepend system prompt if not already there
    if not messages or not isinstance(messages[0], SystemMessage) or "__PLAN__" in messages[0].content:
        # Filter out plan messages and prepend system prompt
        filtered = [m for m in messages if not (isinstance(m, SystemMessage) and "__PLAN__" in m.content)]
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + filtered

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

    # Add nodes — sequential: planner → agent → tools → agent loop
    graph.add_node("planner", _planner_node)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", ToolNode(tools))

    # Set entry point to planner
    graph.set_entry_point("planner")

    # Planner always goes to agent
    graph.add_edge("planner", "agent")

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
