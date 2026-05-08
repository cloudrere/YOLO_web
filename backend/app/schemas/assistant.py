from pydantic import BaseModel


class AssistantChatRequest(BaseModel):
    question: str


class AssistantChatResponse(BaseModel):
    answer: str
    model: str
    configured: bool = True
