import json
import uuid
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.models import ChatRequest, SkillInfo
from app.agent.graph import agent_graph, SKILL_DESCRIPTIONS

app = FastAPI(
    title="Customer Support Agent API",
    description="AI-powered customer support agent with observable skill execution",
    version="1.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation store (POC only)
conversations: dict[str, list] = {}


def _format_sse(event_type: str, data: dict) -> str:
    """Format a server-sent event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _stream_agent_response(message: str, conversation_id: str):
    """Stream agent execution with skill trace events via SSE."""
    # Get or create conversation
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    history = conversations[conversation_id]
    history.append(HumanMessage(content=message))

    # Send thinking event
    yield _format_sse("agent_thinking", {
        "status": "analyzing",
        "timestamp": datetime.now().isoformat(),
    })

    try:
        # Stream through the graph
        inputs = {"messages": list(history)}

        async for event in agent_graph.astream_events(inputs, version="v2"):
            kind = event["event"]

            # Tool call initiated (skill start)
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

            # Tool call completed (skill result)
            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                skill_info = SKILL_DESCRIPTIONS.get(tool_name, {})
                output = event.get("data", {}).get("output", "")
                # Try to parse as JSON for structured display
                try:
                    if hasattr(output, "content"):
                        output_data = json.loads(output.content)
                    else:
                        output_data = json.loads(str(output))
                except (json.JSONDecodeError, TypeError):
                    output_data = {"result": str(output)}

                yield _format_sse("skill_result", {
                    "skill_name": tool_name,
                    "display_name": skill_info.get("name", tool_name),
                    "icon": skill_info.get("icon", "🔧"),
                    "output": output_data,
                    "timestamp": datetime.now().isoformat(),
                })

            # LLM streaming tokens for final response
            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    # Only yield message tokens when there are no tool calls
                    if not (hasattr(chunk, "tool_calls") and chunk.tool_calls) and \
                       not (hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks):
                        yield _format_sse("message", {
                            "content": chunk.content,
                            "timestamp": datetime.now().isoformat(),
                        })

        # Get final state to update conversation history
        final_state = await agent_graph.ainvoke({"messages": list(history)})
        # Update conversation with all new messages
        conversations[conversation_id] = final_state["messages"]

    except Exception as e:
        yield _format_sse("error", {
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    # Signal stream end
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
