from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

#CryptContext provides a consistent interface and makes it easier to
#change hashing algorithms or support multiple schemes in the future.

from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings
import secrets

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str,hashed_password: str,) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    to_encode.update(
        {
            "exp" : expire, 
        }
    )
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt

from jose import JWTError

def decode_access_token(token: str) -> dict:
    """
    Decode a JWT access token.

    Raises JWTError if the token is invalid or expired.
    """

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

def generate_otp(length: int = 6) -> str:
    """
    Generate a numeric OTP.
    """

    digits = "0123456789"

    return "".join(
        secrets.choice(digits)
        for _ in range(length)
    )


def hash_otp(otp: str) -> str:
    return pwd_context.hash(otp)


def verify_otp(
    plain_otp: str,
    hashed_otp: str,
) -> bool:
    return pwd_context.verify(
        plain_otp,
        hashed_otp,
    )