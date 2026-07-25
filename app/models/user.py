from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.database import Base
from app.enums.user_role import UserRole



if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user_session import UserSession
    from app.models.cart import Cart
    from app.models.stall import FoodStall

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    registration_number: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )
    
    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=True
    )
    
    phone_number: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False    
    )
    
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.STUDENT,
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    stall_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("food_stalls.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    profile_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    cart: Mapped["Cart | None"] = relationship(
        back_populates="user",
    )
    session: Mapped["UserSession"] = relationship(
        back_populates="user",
        uselist=False,
    )

    stall: Mapped["FoodStall | None"] = relationship(
        back_populates="admin",
        foreign_keys="[User.stall_id]",
    )