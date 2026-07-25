from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.stall import FoodStall
from app.schemas.auth import AdminRegisterResponse
from app.schemas.stall import FoodStallResponse
from app.services.auth_service import get_current_admin, register_stall_admin

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
    current_admin: User = Depends(get_current_admin),
):
    """
    Return stalls that do not yet have an admin assigned.
    Only accessible by existing admins.
    """
    # Find stall_ids already assigned to an admin
    assigned_stall_ids = (
        db.query(User.stall_id)
        .filter(User.stall_id.isnot(None))
        .all()
    )
    assigned_ids = {row[0] for row in assigned_stall_ids}

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
    current_admin: User = Depends(get_current_admin),
):
    """
    Super-admin creates a new stall admin account.
    Returns the auto-generated registration number and login code.
    """
    reg_number, plain_code, stall_name = register_stall_admin(db, stall_id)
    return AdminRegisterResponse(
        registration_number=reg_number,
        login_code=plain_code,
        stall_name=stall_name,
        stall_id=stall_id,
    )
