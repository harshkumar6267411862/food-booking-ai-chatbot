from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.enums.user_role import UserRole
from app.models.user import User
from app.models.stall import FoodStall
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_registration_number,
    get_user_by_phone,
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
import secrets
import string

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


def _generate_unique_reg_number(db: Session) -> str:
    """Generate a unique admin registration number like AD483921."""
    for _ in range(20):
        digits = "".join(secrets.choice(string.digits) for _ in range(6))
        reg_num = f"AD{digits}"
        if not get_user_by_registration_number(db, reg_num):
            return reg_num
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate a unique registration number.",
    )


def _generate_login_code(length: int = 10) -> str:
    """Generate a random alphanumeric login code."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def register_stall_admin(db: Session, stall_id: int) -> tuple[str, str, str]:
    """
    Create a new admin user assigned to the given stall.
    Returns (registration_number, plain_login_code, stall_name).
    """
    stall = db.query(FoodStall).filter(FoodStall.id == stall_id).first()
    if not stall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stall with ID {stall_id} not found.",
        )

    # Ensure stall doesn't already have an admin
    existing_admin = db.query(User).filter(User.stall_id == stall_id).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stall '{stall.name}' already has an admin assigned.",
        )

    reg_number = _generate_unique_reg_number(db)
    plain_code = _generate_login_code()

    new_admin = User(
        registration_number=reg_number,
        name=None,
        email=None,
        phone_number=reg_number,  # placeholder until profile setup
        password_hash=hash_password(plain_code),
        role=UserRole.ADMIN,
        stall_id=stall_id,
        profile_complete=False,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return reg_number, plain_code, stall.name


def complete_admin_profile(
    db: Session,
    user: User,
    name: str,
    phone_number: str,
) -> User:
    """
    Complete an admin's profile after first login.
    """
    # Normalise phone
    clean_phone = phone_number.lstrip("+").lstrip("91")
    if len(clean_phone) == 10:
        pass  # already normalised
    # Check uniqueness
    existing = get_user_by_phone(db, phone_number)
    if existing and existing.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered.",
        )
    user.name = name
    user.phone_number = phone_number
    user.profile_complete = True
    db.commit()
    db.refresh(user)
    return user