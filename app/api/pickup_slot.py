from fastapi import APIRouter, Depends,status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.pickup_slot import PickupSlotResponse,PickupSlotCreateResponse,PickupSlotCreateRequest,GeneratePickupSlotsRequest
from app.services.pickup_slot_service import get_available_pickup_slots,create_pickup_slot as create_pickup_slot_service,generate_pickup_slots
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/pickup-slots",
    tags=["Pickup Slots"]
)
@router.get("/",response_model=list[PickupSlotResponse])

def get_pickup_slots(db:Session = Depends(get_db)):
    return get_available_pickup_slots(db)

@router.post("/",response_model=PickupSlotCreateResponse,status_code=status.HTTP_201_CREATED,)

def create_pickup_slot_endpoint(slot_data: PickupSlotCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_pickup_slot_service(
        db = db,
        slot_data = slot_data,
        current_user=current_user,
    )
    
@router.post("/generate")
def generate_slots(
    slot_data: GeneratePickupSlotsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return generate_pickup_slots(
        db=db,
        slot_data=slot_data,
        current_user=current_user,
    )

    