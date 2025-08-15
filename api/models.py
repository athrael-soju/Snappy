from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from config import DEFAULT_TOP_K, OPENAI_MODEL, OPENAI_TEMPERATURE


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []
    k: Optional[int] = DEFAULT_TOP_K
    ai_enabled: Optional[bool] = True
    temperature: Optional[float] = OPENAI_TEMPERATURE
    system_prompt: Optional[str] = None


class RetrievedPage(BaseModel):
    image_url: Optional[str]
    label: Optional[str]
    payload: Dict[str, Any]
    score: Optional[float] = None


class ChatResponse(BaseModel):
    text: str
    images: List[RetrievedPage]


class SearchItem(BaseModel):
    image_url: Optional[str]
    label: Optional[str]
    payload: Dict[str, Any]
    score: Optional[float] = None
