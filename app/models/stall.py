from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem
    from app.models.user import User


class FoodStall(Base):
    __tablename__ = "food_stalls"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    menu_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )
    
    opening_time: Mapped[time] = mapped_column(
    Time,
    nullable=False
)

    closing_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    menu_items: Mapped[list["MenuItem"]] = relationship(
        back_populates="food_stall",
        cascade="all, delete-orphan"
    )

    admin: Mapped["User | None"] = relationship(
        back_populates="stall",
        foreign_keys="[User.stall_id]",
        uselist=False,
    )