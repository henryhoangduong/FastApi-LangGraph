from fastapi import APIRouter, Request
from fastapi.security import HTTPBearer
from core.logging import logger
from core.config import settings
from core.limiter import limiter
from services.database import DatabaseService
from schemas.auth import UserCreate
from fastapi.exceptions import HTTPException
from models.user import User
router = APIRouter()
security = HTTPBearer()
db_service = DatabaseService()


@router.post("/register")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["register"][0])
async def register_user(request: Request, user_data: UserCreate):
    try:
        password = user_data.password.get_secret_value()
        user = await db_service.create_user(email=user_data.email, password=User.hash_password(password))

    except ValueError as ve:
        logger.error("user_registration_validation_failed",
                     error=str(ve), exc_info=True)
        raise HTTPException(status_code=422, detail=str(ve))
