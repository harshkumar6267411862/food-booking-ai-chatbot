from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column,relationship


from app.database import Base
from app.enums.order_status import OrderStatus
from app.enums.cancelled_by import CancelledBy

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.pickup_slot import PickupSlot
    from app.models.order_item import OrderItem

class Order(Base):
    
    
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    order_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    pickup_slot_id: Mapped[int] = mapped_column(
        ForeignKey("pickup_slots.id"),
        nullable=False
    )

    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False
    )

    special_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
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
    
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    preparing_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    cancel_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    ) 
    
    cancelled_by: Mapped[CancelledBy | None] = mapped_column(
        SQLEnum(CancelledBy),
        nullable=True,
    )
    
    user: Mapped[User] = relationship(
        back_populates="orders"
    )
    
    pickup_slot: Mapped[PickupSlot] = relationship(
        back_populates="orders"
    )
    
    order_items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan"
    )
    
    pickup_otp_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    otp_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    otp_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )