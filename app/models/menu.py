from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums.menu_category import MenuCategory

if TYPE_CHECKING:
    from app.models.stall import FoodStall
    from app.models.order_item import OrderItem
    
    
class MenuItem(Base):
    
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    stall_id: Mapped[int] = mapped_column(
        ForeignKey("food_stalls.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    category: Mapped[MenuCategory] = mapped_column(
        SQLEnum(MenuCategory),
        nullable=False
    )

    current_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    preparation_time: Mapped[int] = mapped_column(
        nullable=False
    )

    is_available: Mapped[bool] = mapped_column(
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

    food_stall: Mapped[FoodStall] = relationship(
        back_populates="menu_items"
    )
    
    image_url: Mapped[str | None] = mapped_column(
    String(500),
    nullable=True
    )
    
    order_items: Mapped[list[OrderItem]] = relationship(
    back_populates="menu_item"
    )