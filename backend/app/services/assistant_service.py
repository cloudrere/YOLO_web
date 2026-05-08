import time

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import AppException
from app.models.ai_chat_log import AIChatLog
from app.models.user import User


def chat_with_assistant(db: Session, user: User, question: str) -> dict:
    if not settings.ai_assistant_base_url or not settings.ai_assistant_api_key:
        raise AppException(40060, "AI assistant is not configured")
    start = time.perf_counter()
    answer = ""
    status = "success"
    error_message = ""
    try:
        answer = request_chat_completion(question)
        return {"answer": answer, "model": settings.ai_assistant_model, "configured": True}
    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        db.add(
            AIChatLog(
                user_id=user.id,
                model=settings.ai_assistant_model,
                question=question,
                answer=answer,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
            )
        )
        db.commit()


def request_chat_completion(question: str) -> str:
    url = settings.ai_assistant_base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = f"{url}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.ai_assistant_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.ai_assistant_model,
        "messages": [
            {"role": "system", "content": "你是 YOLO 视觉检测平台的中文 AI 助手，回答要简洁、准确。"},
            {"role": "user", "content": question},
        ],
        "temperature": 0.3,
    }
    with httpx.Client(timeout=settings.ai_assistant_timeout_seconds) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise AppException(50260, "AI assistant returned no answer", 502)
    message = choices[0].get("message") or {}
    return str(message.get("content") or "")


def assistant_status() -> dict:
    return {"configured": bool(settings.ai_assistant_base_url and settings.ai_assistant_api_key), "model": settings.ai_assistant_model}
