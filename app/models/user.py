from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum , String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.database import Base
from app.enums.user_role import UserRole

if TYPE_CHECKING:
    from app.models.order import Order

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    registration_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
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
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
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