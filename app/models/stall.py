from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.menu import MenuItem


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

    is_open: Mapped[bool] = mapped_column(
        Boolean,
        default=True
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