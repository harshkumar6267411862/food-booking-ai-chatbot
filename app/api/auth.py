from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    MessageResponse,
    UserRegisterRequest,
)
from app.services.auth_service import register_user

from app.schemas.auth import(
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest
)

from app.services.auth_service import(
    login_user,
    register_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)

def register(user: UserRegisterRequest,db: Session = Depends(get_db),):
    try:
        register_user(
            db,
            user,
        )

        return MessageResponse(
            message="User registered successfully."
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/login",response_model=TokenResponse,status_code=status.HTTP_200_OK)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db),):
    
    user_data = UserLoginRequest(
        registration_number=form_data.username,
        password=form_data.password,
    )
    
    try:
        access_token = login_user(db,user_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=str(e),)
    
    