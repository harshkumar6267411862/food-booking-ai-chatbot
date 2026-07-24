from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import Numeric
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.menu_item import MenuItem


class CartItem(Base):

    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id"),
        nullable=False,
    )

    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    
    price_at_purchase: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    cart: Mapped["Cart"] = relationship(
        back_populates="cart_items",
    )

    menu_item: Mapped["MenuItem"] = relationship(
        back_populates="cart_items",
    )