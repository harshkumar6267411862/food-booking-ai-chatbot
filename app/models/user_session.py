from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey,Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums.chat_state import ChatState


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.stall import FoodStall


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    state: Mapped[ChatState] = mapped_column(
        default=ChatState.WAITING_FOR_NAME,
        nullable=False,
    )

    selected_stall_id: Mapped[int | None] = mapped_column(
        ForeignKey("food_stalls.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user: Mapped["User"] = relationship(back_populates="session",)

    selected_stall: Mapped["FoodStall"] = relationship()
    
    current_menu_page = mapped_column(
        Integer,
        default=1,
            nullable=False,
)