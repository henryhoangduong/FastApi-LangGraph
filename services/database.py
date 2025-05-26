from sqlalchemy import QueuePool, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel

from core.config import Environment, settings
from core.logging import logger
from models.user import User
from models.session import Session as ChatSession


class DatabaseService:

    def __init__(self):
        """Initialize database service with connection pool."""
        try:
            # Configure environment-specific database connection pool settings
            pool_size = settings.POSTGRES_POOL_SIZE
            max_overflow = settings.POSTGRES_MAX_OVERFLOW

            # Create engine with appropriate pool configuration
            self.engine = create_engine(
                settings.POSTGRES_URL,
                pool_pre_ping=True,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=30,  # Connection timeout (seconds)
                pool_recycle=1800,  # Recycle connections after 30 minutes
            )

            # Create tables (only if they don't exist)
            SQLModel.metadata.create_all(self.engine)

            logger.info(
                "database_initialized",
                environment=settings.ENVIRONMENT.value,
                pool_size=pool_size,
                max_overflow=max_overflow,
            )
        except SQLAlchemyError as e:
            logger.error(
                "database_initialization_error",
                error=str(e),
                environment=settings.ENVIRONMENT.value,
            )
            # In production, don't raise - allow app to start even with DB issues
            if settings.ENVIRONMENT != Environment.PRODUCTION:
                raise

    async def create_user(self, email: str, password: str) -> User:
        with Session(self.engine) as session:
            user = User(email=email, hashed_password=password)
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info("user_created", email=email)
            return user

    async def get_user(self, user_id: str):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            return user


    async def create_session(self, session_id: str, user_id: int, name: str = ""):
        with Session(self.engine) as session:
            chat_session = ChatSession(
                id=session_id, user_id=user_id, name=name)
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            logger.info("session_created", session_id=session_id,
                        user_id=user_id, name=name)
            return chat_session
