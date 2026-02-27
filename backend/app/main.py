import json
import uuid
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.models import ChatRequest, SkillInfo
from app.agent.graph import agent_graph, SKILL_DESCRIPTIONS
from app.agent.skills.chart_generator import chart_store

app = FastAPI(
    title="AMM Assist API",
    description="AI-powered Advanced Manufacturing operations assistant with observable skill execution",
    version="2.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Conversation-Id"],
)

# In-memory conversation store (POC only)
conversations: dict[str, list] = {}


def _format_sse(event_type: str, data: dict) -> str:
    """Format a server-sent event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _stream_agent_response(message: str, conversation_id: str):
    """Stream agent execution with skill trace events via SSE."""
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    history = conversations[conversation_id]
    history.append(HumanMessage(content=message))

    yield _format_sse("agent_thinking", {
        "status": "analyzing",
        "timestamp": datetime.now().isoformat(),
    })

    try:
        inputs = {"messages": list(history)}

        async for event in agent_graph.astream_events(inputs, version="v2"):
            kind = event["event"]
            metadata = event.get("metadata", {})
            langgraph_node = metadata.get("langgraph_node", "")

            # --- PLAN: detect plan output from planner node ---
            if kind == "on_chat_model_end" and langgraph_node == "planner":
                output = event.get("data", {}).get("output")
                if output and hasattr(output, "content"):
                    plan_text = str(output.content).strip()
                    # Strip __PLAN__: prefix if present
                    if "__PLAN__:" in plan_text:
                        plan_text = plan_text.split("__PLAN__:")[1]
                    try:
                        if "```" in plan_text:
                            plan_text = plan_text.split("```")[1]
                            if plan_text.startswith("json"):
                                plan_text = plan_text[4:]
                        plan = json.loads(plan_text.strip())
                        if isinstance(plan, list):
                            yield _format_sse("plan", {
                                "steps": plan,
                                "timestamp": datetime.now().isoformat(),
                            })
                    except (json.JSONDecodeError, IndexError):
                        pass
                continue

            # --- TOOL START ---
            if kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                skill_info = SKILL_DESCRIPTIONS.get(tool_name, {})
                yield _format_sse("skill_start", {
                    "skill_name": tool_name,
                    "display_name": skill_info.get("name", tool_name),
                    "icon": skill_info.get("icon", "🔧"),
                    "input": str(event.get("data", {}).get("input", "")),
                    "timestamp": datetime.now().isoformat(),
                })

            # --- TOOL END ---
            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                skill_info = SKILL_DESCRIPTIONS.get(tool_name, {})
                output = event.get("data", {}).get("output", "")

                try:
                    if hasattr(output, "content"):
                        output_data = json.loads(output.content)
                    else:
                        output_data = json.loads(str(output))
                except (json.JSONDecodeError, TypeError):
                    output_data = {"result": str(output)}

                # Check if this is a chart result (has chart_id from chart_store)
                if isinstance(output_data, dict) and "chart_id" in output_data:
                    chart_id = output_data["chart_id"]
                    chart_b64 = chart_store.pop(chart_id, None)
                    if chart_b64:
                        yield _format_sse("chart", {
                            "skill_name": tool_name,
                            "image_base64": chart_b64,
                            "chart_type": output_data.get("chart_type", "unknown"),
                            "summary": output_data.get("summary", ""),
                            "timestamp": datetime.now().isoformat(),
                        })
                    # Send clean skill_result (no base64)
                    yield _format_sse("skill_result", {
                        "skill_name": tool_name,
                        "display_name": skill_info.get("name", tool_name),
                        "icon": skill_info.get("icon", "📊"),
                        "output": output_data,
                        "timestamp": datetime.now().isoformat(),
                    })
                else:
                    yield _format_sse("skill_result", {
                        "skill_name": tool_name,
                        "display_name": skill_info.get("name", tool_name),
                        "icon": skill_info.get("icon", "🔧"),
                        "output": output_data,
                        "timestamp": datetime.now().isoformat(),
                    })

            # --- LLM STREAMING (only from agent node, NOT planner) ---
            elif kind == "on_chat_model_stream":
                # Skip tokens from planner node
                if langgraph_node == "planner":
                    continue

                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    # Skip plan-related content
                    if "__PLAN__" in chunk.content:
                        continue
                    # Only yield when no tool calls
                    if not (hasattr(chunk, "tool_calls") and chunk.tool_calls) and \
                       not (hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks):
                        yield _format_sse("message", {
                            "content": chunk.content,
                            "timestamp": datetime.now().isoformat(),
                        })

        # Get final state to update conversation history
        final_state = await agent_graph.ainvoke({"messages": list(history)})
        clean_messages = [m for m in final_state["messages"]
                          if not (hasattr(m, 'content') and "__PLAN__" in str(m.content))]
        conversations[conversation_id] = clean_messages

    except Exception as e:
        yield _format_sse("error", {
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    yield _format_sse("done", {
        "timestamp": datetime.now().isoformat(),
    })


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint that streams agent execution via SSE."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    return StreamingResponse(
        _stream_agent_response(request.message, conversation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Conversation-Id": conversation_id,
        }
    )


@app.get("/api/skills")
async def list_skills():
    """List all available agent skills."""
    skills = []
    for key, info in SKILL_DESCRIPTIONS.items():
        skills.append(SkillInfo(
            name=info["name"],
            description=info["description"],
            icon=info["icon"],
        ))
    return {"skills": skills}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
