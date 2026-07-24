from jose import JWTError, jwt

from fastapi import(
    Depends,
    HTTPException,
    status,   
)

from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import(
    get_user_by_registration_number,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",    
)

def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db),) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate":"Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        registration_number = payload.get("sub")
        
        if registration_number is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_registration_number(db, registration_number,)
    
    if user is None:
        raise credentials_exception
    
    return user