from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.stall import FoodStall
from app.schemas.auth import AdminRegisterResponse, StallAdminDetailResponse, ResetLoginCodeResponse
from app.schemas.stall import FoodStallResponse
from app.services.auth_service import get_current_admin, register_stall_admin, get_all_stall_admins, reset_admin_login_code


router = APIRouter(
    prefix="/admin",
    tags=["Admin Registration"],
)


@router.get(
    "/stalls/unassigned",
    response_model=list[FoodStallResponse],
)
def get_unassigned_stalls(
    db: Session = Depends(get_db),
):
    """
    Return stalls that do not yet have an admin assigned.
    Publicly accessible so new admins can select a stall to register.
    """
    # Find stall_ids already assigned to an admin
    assigned_stall_ids = (
        db.query(User.stall_id)
        .filter(User.stall_id.isnot(None))
        .all()
    )
    assigned_ids = {row[0] for row in assigned_stall_ids}

    # SQLAlchemy's notin_() generates broken SQL when given an empty set.
    # When no stalls are assigned yet, return all stalls directly.
    if not assigned_ids:
        unassigned = (
            db.query(FoodStall)
            .order_by(FoodStall.name)
            .all()
        )
    else:
        unassigned = (
            db.query(FoodStall)
            .filter(FoodStall.id.notin_(assigned_ids))
            .order_by(FoodStall.name)
            .all()
        )
    return unassigned


@router.post(
    "/register",
    response_model=AdminRegisterResponse,
    status_code=201,
)
def register_admin(
    stall_id: int,
    db: Session = Depends(get_db),
):
    """
    Register a new admin account for an unassigned stall.
    Returns the auto-generated registration number and login code.
    """
    reg_number, plain_code, stall_name = register_stall_admin(db, stall_id)
    return AdminRegisterResponse(
        registration_number=reg_number,
        login_code=plain_code,
        stall_name=stall_name,
        stall_id=stall_id,
    )


@router.get(
    "/list",
    response_model=list[StallAdminDetailResponse],
)
def list_stall_admins(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Super Admin endpoint to list all stall admins and their stall details.
    """
    if current_admin.stall_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can access the admin list.",
        )
    return get_all_stall_admins(db)


@router.post(
    "/reset-login-code/{user_id}",
    response_model=ResetLoginCodeResponse,
)
def reset_login_code(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Super Admin endpoint to reset a stall admin's login code.
    Returns the new login code for that admin.
    """
    if current_admin.stall_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can reset login codes.",
        )
    reg_number, new_code, stall_name = reset_admin_login_code(db, user_id)
    return ResetLoginCodeResponse(
        registration_number=reg_number,
        new_login_code=new_code,
        stall_name=stall_name,
    )

