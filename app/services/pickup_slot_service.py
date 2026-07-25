from datetime import datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.pickup_slot_repository import (get_todays_active_slots , 
                                                     get_pickup_slot_by_date_and_time,
                                                     create_pickup_slot as create_pickup_slot_repo,)
from app.schemas.pickup_slot import (PickupSlotResponse,
                                     PickupSlotCreateRequest,
                                     PickupSlotCreateResponse,
                                     GeneratePickupSlotsRequest)

from app.models.pickup_slot import PickupSlot
from app.models.user import User
from app.enums.user_role import UserRole

CAFETERIA_OPENING_TIME = time(hour=7, minute=0)
CAFETERIA_CLOSING_TIME = time(hour=17, minute=0)
PREPARATION_BUFFER = timedelta(minutes=15)
DEFAULT_SLOT_INTERVAL = 15
DEFAULT_MAX_ORDERS = 30
DEFAULT_WAIT_TIME = 15

def get_available_pickup_slots(db: Session) -> list[PickupSlotResponse]:
    now = datetime.now()
    cutoff_time = now + PREPARATION_BUFFER
    
    current_time = now.time()

    
    if current_time < CAFETERIA_OPENING_TIME or current_time > CAFETERIA_CLOSING_TIME:
        raise HTTPException(
            status_code=403,
            detail="The cafeteria is currently closed."
        )
        
    slots = get_todays_active_slots(db, now.date())
    
    available_slots = []
    
    for slot in slots:
        slot_datetime = datetime.combine(
            slot.slot_date,
            slot.start_time,
        )
        
        if slot_datetime < cutoff_time:
            continue
        
        if slot.current_orders >= slot.max_orders:
            continue

        available = (slot.current_orders < slot.max_orders)
        
        available_slots.append(
            PickupSlotResponse(
                id=slot.id,
                slot_date=slot.slot_date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                estimated_wait_minutes=slot.estimated_wait_minutes,
                available=available,
            )
        )
    
    return available_slots
        

def create_pickup_slot(db: Session, slot_data: PickupSlotCreateRequest,current_user: User,) -> PickupSlotCreateResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only admins can create pickup slots."
        )
        
    if slot_data.start_time >= slot_data.end_time:
        raise HTTPException(
            status_code=400,
            detail="Start time must be before end time."
        )
    
    if (slot_data.start_time < CAFETERIA_OPENING_TIME or slot_data.end_time > CAFETERIA_CLOSING_TIME):
        raise HTTPException(
            status_code= 400,
            detail="Pickup slot must be within cafeteria operating hourse."
        )
    
    if slot_data.max_orders <=0:
        raise HTTPException(
            status_code= 400,
            detail="Maximum orders must be greater than zero."
        )
        
    existing_slot = get_pickup_slot_by_date_and_time(
        db=db,
        slot_date=slot_data.slot_date,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
    ) 
    
    if existing_slot:
        raise HTTPException(
            status_code=409,
            detail= "A pickup slot with the same date and time already exists."
        )
    
    pickup_slot = PickupSlot(
        slot_date=slot_data.slot_date,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        max_orders=slot_data.max_orders,
        estimated_wait_minutes=slot_data.estimated_wait_minutes,
    )
    
    created_slot = create_pickup_slot_repo(
        db=db,
        pickup_slot=pickup_slot
    ) 
    
    return PickupSlotCreateResponse.model_validate(created_slot)


from datetime import datetime, timedelta

def generate_pickup_slots(
    db: Session,
    slot_data: GeneratePickupSlotsRequest,
    current_user: User,
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only admins can generate pickup slots."
        )

    current = datetime.combine(
        slot_data.slot_date,
        CAFETERIA_OPENING_TIME,
    )

    end = datetime.combine(
        slot_data.slot_date,
        CAFETERIA_CLOSING_TIME,
    )

    while current < end:

        next_time = current + timedelta(
            minutes=DEFAULT_SLOT_INTERVAL
        )

        existing = get_pickup_slot_by_date_and_time(
            db=db,
            slot_date=slot_data.slot_date,
            start_time=current.time(),
            end_time=next_time.time(),
        )

        if not existing:

            pickup_slot = PickupSlot(
                slot_date=slot_data.slot_date,
                start_time=current.time(),
                end_time=next_time.time(),
                max_orders=DEFAULT_MAX_ORDERS,
                estimated_wait_minutes=DEFAULT_WAIT_TIME,
            )

            create_pickup_slot_repo(
                db=db,
                pickup_slot=pickup_slot,
            )

        current = next_time

    return {
        "message": "Pickup slots generated successfully."
    }

    
    
        
        