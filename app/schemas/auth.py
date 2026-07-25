import re
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.enums.user_role import UserRole


class UserRegisterRequest(BaseModel):
    registration_number: str = Field(
        min_length=8,
        max_length=8,
        pattern=r"^[A-Za-z0-9]+$",
    )
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone_number: str = Field(
        pattern=r"^(?:\+91|91)?[6-9]\d{9}$",
        description="Indian phone number (e.g. 9876543210 or +919876543210)",
    )
    password: str = Field(
        min_length=8,
        max_length=24,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"[0-9]", value):
            raise ValueError(
                "Password must contain at least one digit."
            )

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError(
                "Password must contain at least one special character."
            )

        return value


class MessageResponse(BaseModel):
    message: str


class UserLoginRequest(BaseModel):
    registration_number: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    registration_number: str
    name: str | None = None
    email: str | None = None
    role: UserRole
    stall_id: int | None = None
    profile_complete: bool = False
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
    
class UserSummary(BaseModel):
    """
    Minimal user information for nested responses.
    """

    registration_number: str | None = None
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminRegisterResponse(BaseModel):
    """
    Returned after a super-admin creates a new stall admin account.
    """
    registration_number: str
    login_code: str
    stall_name: str
    stall_id: int


class AdminProfileSetupRequest(BaseModel):
    """
    Submitted by a new admin on first login to complete their profile.
    """
    name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(
        pattern=r"^(?:\+91|91)?[6-9]\d{9}$",
        description="Indian mobile number (e.g. 9876543210)",
    )