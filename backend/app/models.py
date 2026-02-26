from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum


class ChatRequest(BaseModel):
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
