from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import AdminProfileSetupRequest, UserResponse
from app.schemas.stall import FoodStallResponse
from app.services.auth_service import get_current_admin, complete_admin_profile

router = APIRouter(
    prefix="/admin/profile",
    tags=["Admin Profile"],
)


@router.post(
    "/setup",
    response_model=UserResponse,
)
def setup_profile(
    request: AdminProfileSetupRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Complete an admin's profile after first login.
    Sets name, phone_number, and marks profile_complete=True.
    """
    updated = complete_admin_profile(
        db=db,
        user=current_admin,
        name=request.name,
        phone_number=request.phone_number,
    )
    return updated


@router.get(
    "/stall",
    response_model=FoodStallResponse,
)
def get_my_stall(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Return the stall assigned to the currently logged-in admin.
    """
    from fastapi import HTTPException, status
    if not current_admin.stall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stall assigned to this admin.",
        )
    return current_admin.stall
