from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.enums.user_role import UserRole
from app.models.user import User
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_registration_number,
)
from app.schemas.auth import UserRegisterRequest
from app.utils.security import hash_password

from app.schemas.auth import UserLoginRequest
from app.utils.security import (
    create_access_token,
    verify_password,
    decode_access_token,
    oauth2_scheme
)

from jose import JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from app.database import get_db

def register_user(db: Session, user_data: UserRegisterRequest,):
    existing_user = get_user_by_registration_number(
        db,
        user_data.registration_number,
    )
    
    if existing_user:
        raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Registration number already exists."
        )
    
    existing_email = get_user_by_email(
        db,
        user_data.email,
    )
    
    if existing_email:
        raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Email already exists."
        )
    
    new_user = User(
        registration_number = user_data.registration_number,
        name = user_data.name,
        email = user_data.email,
        phone_number = user_data.phone_number,
        role = UserRole.STUDENT,
        password_hash = hash_password(user_data.password),
    )
    
    created_user = create_user(db, new_user,)
    
    return created_user

def login_user(db: Session, user_data: UserLoginRequest) -> str:
    user = get_user_by_registration_number(db, user_data.registration_number)
    
    if not user:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid registration number or password."
        )
    
    if not verify_password(user_data.password,user.password_hash):
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid registration number or password."
        )
    
    access_token = create_access_token(
        {
            "sub": user.registration_number,
            "role": user.role.value,
        }
    )
    
    return access_token


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Retrieve the currently authenticated user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = decode_access_token(token)

        registration_number = payload.get("sub")

        if registration_number is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = get_user_by_registration_number(
        db,
        registration_number,
    )

    if user is None:
        raise credentials_exception

    return user

def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the authenticated user is an admin.
    """

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return current_user