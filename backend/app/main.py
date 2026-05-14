import json
import uuid
import asyncio
import time
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.models import ChatRequest, CompareRequest, SkillInfo
from app.agent.graph import agent_graph, agent_only_graph, SKILL_DESCRIPTIONS
from app.agent.skills.chart_generator import chart_store
from app.config import OPENAI_MODEL

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

# Token pricing per 1M tokens (GPT-4.1-mini defaults)
TOKEN_PRICING = {
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def _get_pricing():
    """Get token pricing for the configured model."""
    return TOKEN_PRICING.get(OPENAI_MODEL, TOKEN_PRICING["gpt-4.1-mini"])


def _estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost in dollars based on token counts."""
    pricing = _get_pricing()
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


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
        final_assistant_content = ""

        async for event in agent_graph.astream_events(inputs, version="v2"):
            kind = event["event"]
            metadata = event.get("metadata", {})
            langgraph_node = metadata.get("langgraph_node", "")

            # --- PLAN: detect plan output from planner node ---
            if kind == "on_chat_model_end" and langgraph_node == "planner":
                output = event.get("data", {}).get("output")
                if output and hasattr(output, "content"):
                    plan_text = str(output.content).strip()
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

            # --- Capture final assistant response from agent node ---
            if kind == "on_chat_model_end" and langgraph_node == "agent":
                output = event.get("data", {}).get("output")
                if output and hasattr(output, "content") and output.content:
                    if not (hasattr(output, "tool_calls") and output.tool_calls):
                        final_assistant_content = output.content

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
                if langgraph_node == "planner":
                    continue

                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    if "__PLAN__" in chunk.content:
                        continue
                    if not (hasattr(chunk, "tool_calls") and chunk.tool_calls) and \
                       not (hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks):
                        yield _format_sse("message", {
                            "content": chunk.content,
                            "timestamp": datetime.now().isoformat(),
                        })

        # Save conversation history without re-running the graph
        if final_assistant_content:
            history.append(AIMessage(content=final_assistant_content))
        conversations[conversation_id] = list(history)

    except Exception as e:
        yield _format_sse("error", {
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    yield _format_sse("done", {
        "timestamp": datetime.now().isoformat(),
    })


# ═══════════════════════════════════════════════════════
# COMPARE MODE: Skills vs Agent side-by-side
# ═══════════════════════════════════════════════════════

async def _run_skills_pipeline(message: str) -> dict:
    """Run the skills pipeline and collect results + token usage."""
    start_time = time.time()
    inputs = {"messages": [HumanMessage(content=message)]}

    events_collected = []
    final_content = ""
    plan_steps = []
    skill_events = []
    token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "nodes": []}

    async for event in agent_graph.astream_events(inputs, version="v2"):
        kind = event["event"]
        metadata = event.get("metadata", {})
        langgraph_node = metadata.get("langgraph_node", "")

        # Capture plan
        if kind == "on_chat_model_end" and langgraph_node == "planner":
            output = event.get("data", {}).get("output")
            if output and hasattr(output, "content"):
                plan_text = str(output.content).strip()
                try:
                    if "```" in plan_text:
                        plan_text = plan_text.split("```")[1]
                        if plan_text.startswith("json"):
                            plan_text = plan_text[4:]
                    parsed = json.loads(plan_text.strip())
                    if isinstance(parsed, list):
                        plan_steps = parsed
                except (json.JSONDecodeError, IndexError):
                    pass

                # Token usage from planner
                if hasattr(output, "usage_metadata") and output.usage_metadata:
                    meta = output.usage_metadata
                    p = meta.get("input_tokens", 0)
                    c = meta.get("output_tokens", 0)
                    token_usage["prompt_tokens"] += p
                    token_usage["completion_tokens"] += c
                    token_usage["total_tokens"] += (p + c)
                    token_usage["nodes"].append({
                        "node": "planner",
                        "prompt_tokens": p,
                        "completion_tokens": c,
                        "total_tokens": p + c,
                    })

        # Capture agent response + tokens
        if kind == "on_chat_model_end" and langgraph_node == "agent":
            output = event.get("data", {}).get("output")
            if output and hasattr(output, "content") and output.content:
                if not (hasattr(output, "tool_calls") and output.tool_calls):
                    final_content = output.content

                # Token usage from agent
                if hasattr(output, "usage_metadata") and output.usage_metadata:
                    meta = output.usage_metadata
                    p = meta.get("input_tokens", 0)
                    c = meta.get("output_tokens", 0)
                    call_num = sum(1 for n in token_usage["nodes"] if n["node"].startswith("agent")) + 1
                    token_usage["prompt_tokens"] += p
                    token_usage["completion_tokens"] += c
                    token_usage["total_tokens"] += (p + c)
                    token_usage["nodes"].append({
                        "node": f"agent_call_{call_num}",
                        "prompt_tokens": p,
                        "completion_tokens": c,
                        "total_tokens": p + c,
                    })

        # Capture tool events
        if kind == "on_tool_start":
            tool_name = event.get("name", "unknown")
            skill_info = SKILL_DESCRIPTIONS.get(tool_name, {})
            skill_events.append({
                "type": "start",
                "skill_name": tool_name,
                "display_name": skill_info.get("name", tool_name),
                "icon": skill_info.get("icon", "🔧"),
            })
        elif kind == "on_tool_end":
            tool_name = event.get("name", "unknown")
            skill_info = SKILL_DESCRIPTIONS.get(tool_name, {})
            skill_events.append({
                "type": "result",
                "skill_name": tool_name,
                "display_name": skill_info.get("name", tool_name),
                "icon": skill_info.get("icon", "🔧"),
            })

    elapsed = (time.time() - start_time) * 1000  # ms
    cost = _estimate_cost(token_usage["prompt_tokens"], token_usage["completion_tokens"])

    return {
        "method": "skills",
        "content": final_content,
        "plan_steps": plan_steps,
        "skill_events": skill_events,
        "token_usage": token_usage,
        "time_ms": round(elapsed, 1),
        "estimated_cost": cost,
    }


async def _run_agent_pipeline(message: str) -> dict:
    """Run the pure agent (no tools) pipeline and collect results + token usage."""
    start_time = time.time()
    inputs = {"messages": [HumanMessage(content=message)]}

    final_content = ""
    token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "nodes": []}

    async for event in agent_only_graph.astream_events(inputs, version="v2"):
        kind = event["event"]
        metadata = event.get("metadata", {})
        langgraph_node = metadata.get("langgraph_node", "")

        if kind == "on_chat_model_end" and langgraph_node == "agent":
            output = event.get("data", {}).get("output")
            if output and hasattr(output, "content") and output.content:
                final_content = output.content

                if hasattr(output, "usage_metadata") and output.usage_metadata:
                    meta = output.usage_metadata
                    p = meta.get("input_tokens", 0)
                    c = meta.get("output_tokens", 0)
                    token_usage["prompt_tokens"] += p
                    token_usage["completion_tokens"] += c
                    token_usage["total_tokens"] += (p + c)
                    token_usage["nodes"].append({
                        "node": "agent_direct",
                        "prompt_tokens": p,
                        "completion_tokens": c,
                        "total_tokens": p + c,
                    })

    elapsed = (time.time() - start_time) * 1000
    cost = _estimate_cost(token_usage["prompt_tokens"], token_usage["completion_tokens"])

    return {
        "method": "agent",
        "content": final_content,
        "plan_steps": [],
        "skill_events": [],
        "token_usage": token_usage,
        "time_ms": round(elapsed, 1),
        "estimated_cost": cost,
    }


async def _stream_compare_response(message: str):
    """Run both Skills and Agent pipelines concurrently and stream results via SSE."""
    yield _format_sse("compare_start", {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    })

    try:
        # Run both pipelines concurrently
        skills_result, agent_result = await asyncio.gather(
            _run_skills_pipeline(message),
            _run_agent_pipeline(message),
        )

        # Emit skills result
        yield _format_sse("skills_result", {
            "content": skills_result["content"],
            "plan_steps": skills_result["plan_steps"],
            "skill_events": skills_result["skill_events"],
            "token_usage": skills_result["token_usage"],
            "time_ms": skills_result["time_ms"],
            "estimated_cost": skills_result["estimated_cost"],
            "timestamp": datetime.now().isoformat(),
        })

        # Emit agent result
        yield _format_sse("agent_result", {
            "content": agent_result["content"],
            "token_usage": agent_result["token_usage"],
            "time_ms": agent_result["time_ms"],
            "estimated_cost": agent_result["estimated_cost"],
            "timestamp": datetime.now().isoformat(),
        })

        # Emit comparison summary
        skills_total = skills_result["token_usage"]["total_tokens"]
        agent_total = agent_result["token_usage"]["total_tokens"]
        token_diff_pct = round(((skills_total - agent_total) / max(skills_total, 1)) * 100, 1) if skills_total > 0 else 0
        time_diff_pct = round(((skills_result["time_ms"] - agent_result["time_ms"]) / max(skills_result["time_ms"], 1)) * 100, 1)

        yield _format_sse("comparison_summary", {
            "skills": {
                "total_tokens": skills_total,
                "prompt_tokens": skills_result["token_usage"]["prompt_tokens"],
                "completion_tokens": skills_result["token_usage"]["completion_tokens"],
                "time_ms": skills_result["time_ms"],
                "estimated_cost": skills_result["estimated_cost"],
                "skills_used": len([e for e in skills_result["skill_events"] if e["type"] == "result"]),
                "nodes": skills_result["token_usage"]["nodes"],
            },
            "agent": {
                "total_tokens": agent_total,
                "prompt_tokens": agent_result["token_usage"]["prompt_tokens"],
                "completion_tokens": agent_result["token_usage"]["completion_tokens"],
                "time_ms": agent_result["time_ms"],
                "estimated_cost": agent_result["estimated_cost"],
                "nodes": agent_result["token_usage"]["nodes"],
            },
            "token_diff_pct": token_diff_pct,
            "time_diff_pct": time_diff_pct,
            "model": OPENAI_MODEL,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        yield _format_sse("error", {
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    yield _format_sse("compare_done", {
        "timestamp": datetime.now().isoformat(),
    })


# ═══════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════

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


@app.post("/api/chat/compare")
async def compare(request: CompareRequest):
    """Compare Skills vs Agent execution side-by-side with token tracking."""
    return StreamingResponse(
        _stream_compare_response(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
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
            details=info.get("details"),
            examples=info.get("examples"),
            data_source=info.get("data_source"),
        ))
    return {"skills": skills}


@app.get("/api/token-pricing")
async def token_pricing():
    """Get token pricing info for the configured model."""
    pricing = _get_pricing()
    return {
        "model": OPENAI_MODEL,
        "pricing_per_1m_tokens": pricing,
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    from app.config import LLM_PROVIDER
    return {
        "status": "ok",
        "llm_provider": LLM_PROVIDER,
        "model": OPENAI_MODEL,
        "timestamp": datetime.now().isoformat(),
    }
