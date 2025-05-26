from typing import (
    TYPE_CHECKING,
    List,
)

from sqlmodel import (
    Field,
    Relationship,
)
from base import BaseModel

if TYPE_CHECKING:
    from user import User


class Session(BaseModel):
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    name: str = Field(default="")
    user: "User" = Relationship(back_populates="sessions")
