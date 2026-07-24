from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Time
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.order import Order

class PickupSlot(Base):
    __tablename__ = "pickup_slots"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    slot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    max_orders: Mapped[int] = mapped_column(
        nullable=False
    )

    current_orders: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    @property
    def available(self) -> bool:
        return self.is_active and self.current_orders < self.max_orders

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    estimated_wait_minutes: Mapped[int] = mapped_column(
    default=0,
    nullable=False
    )
    
    orders: Mapped[list[Order]] = relationship(
        back_populates="pickup_slot"
    )