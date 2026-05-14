from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class CompareRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class SkillEventType(str, Enum):
    SKILL_START = "skill_start"
    SKILL_RESULT = "skill_result"
    AGENT_THINKING = "agent_thinking"
    MESSAGE = "message"
    DONE = "done"
    ERROR = "error"


class SkillEvent(BaseModel):
    type: SkillEventType
    skill_name: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Any] = None
    timestamp: Optional[str] = None


class SkillInfo(BaseModel):
    name: str
    description: str
    icon: str
    details: Optional[str] = None
    examples: Optional[list[str]] = None
    data_source: Optional[str] = None


class TokenUsageNode(BaseModel):
    node: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class TokenUsageSummary(BaseModel):
    method: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    nodes: list[TokenUsageNode] = []
    time_ms: float = 0
    estimated_cost: float = 0
