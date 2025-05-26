from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException

from api.v1.auth import get_current_session
from core.langgraph.graph import LangGraphAgent
from core.logging import logger
from models.session import Session
from schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
agent = LangGraphAgent()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    session: Session = Depends(get_current_session),
):
    try:
        logger.info(
            "chat_request_received",
            session_id=session.id,
            message_count=len(chat_request.messages),
        )

        result = await agent.get_response(
            chat_request.messages, session.id, user_id=session.user_id
        )

        logger.info("chat_request_processed", session_id=session.id)

        return ChatResponse(messages=result)
    except Exception as e:
        logger.error(
            "chat_request_failed", session_id=session.id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
