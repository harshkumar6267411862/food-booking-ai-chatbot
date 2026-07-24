from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.pickup_slot import GeneratePickupSlotsRequest
from app.services.auth_service import get_current_admin
from app.services.pickup_slot_service import generate_pickup_slots

router = APIRouter(
    prefix="/admin/pickup-slots",
    tags=["Admin Pickup Slots"],
)

@router.post("/generate")
def generate_slots_endpoint(
    request: GeneratePickupSlotsRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Generate pickup slots for a given date.
    """
    return generate_pickup_slots(
        db=db,
        slot_data=request,
        current_user=current_admin,
    )