from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from core.config import settings
from core.limiter import limiter
from core.logging import logger
from models.user import User
from schemas.auth import UserCreate, UserResponse, SessionResponse
from services.database import DatabaseService
from utils.auth import create_access_token, verify_token
from fastapi import Depends
from utils.sanitization import sanitize_string
import uuid

router = APIRouter()
security = HTTPBearer()
db_service = DatabaseService()


@router.post("/register", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["register"][0])
async def register_user(request: Request, user_data: UserCreate):
    try:
        password = user_data.password.get_secret_value()
        user = await db_service.create_user(
            email=user_data.email, password=User.hash_password(password)
        )
        token = create_access_token(str(user.id))
        return UserResponse(id=user.id, email=user.email, token=token)

    except ValueError as ve:
        logger.error(
            "user_registration_validation_failed", error=str(ve), exc_info=True
        )
        raise HTTPException(status_code=422, detail=str(ve))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        token = sanitize_string(credentials.credentials)
        user_id = verify_token(token)
        if user_id is None:
            logger.error("invalid_token", token_part=token[:10] + "...")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify user exists in database
        user_id_int = int(user_id)
        user = await db_service.get_user(user_id_int)
        if user is None:
            logger.error("user_not_found", user_id=user_id_int)
            raise HTTPException(
                status_code=404,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
    except ValueError as ve:
        logger.error("token_validation_failed", error=str(ve), exc_info=True)
        raise HTTPException(
            status_code=422,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/session", response_model=SessionResponse)
async def create_session(user: User = Depends(get_current_user)):
    try:
        session_id = str(uuid.uuid4())
        session = await db_service.create_session(session_id, user.id)
        token = create_access_token(session_id)

        logger.info(
            "session_created",
            session_id=session_id,
            user_id=user.id,
            name=session.name,
            expires_at=token.expires_at.isoformat(),
        )
        return SessionResponse(session_id=session_id, name=session.name, token=token)

    except ValueError as ve:
        logger.error(
            "session_creation_validation_failed",
            error=str(ve),
            user_id=user.id,
            exc_info=True,
        )
