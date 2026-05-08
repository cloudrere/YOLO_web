from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.assistant import AssistantChatRequest
from app.services.assistant_service import assistant_status, chat_with_assistant
from app.services.log_service import create_log

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/status")
def get_assistant_status(_: User = Depends(require_permission("assistant:use"))):
    return success(assistant_status())


@router.post("/chat")
def chat_api(payload: AssistantChatRequest, db: Session = Depends(get_db), current_user: User = Depends(require_permission("assistant:use"))):
    data = chat_with_assistant(db, current_user, payload.question)
    create_log(db, "assistant", "AI assistant question completed", module="assistant", user_id=current_user.id)
    return success(data)
