from datetime import date, time

from sqlalchemy.orm import Session

from app.models.pickup_slot import PickupSlot


def get_todays_active_slots(db: Session, today_date: date) -> list[PickupSlot]:
    return (
        db.query(PickupSlot)
        .filter(
            PickupSlot.slot_date == today_date,
            PickupSlot.is_active.is_(True)
        )
        .order_by(PickupSlot.start_time)
        .all()
    )
    
def get_pickup_slot_by_date_and_time(db:Session,slot_date:date,start_time:time,end_time: time) -> PickupSlot | None:
    return (
        db.query(PickupSlot).filter(
            PickupSlot.slot_date == slot_date,
            PickupSlot.start_time == start_time,
            PickupSlot.end_time == end_time,
        )
        .first()
    )


def create_pickup_slot(db: Session, pickup_slot: PickupSlot) -> PickupSlot:
    db.add(pickup_slot)
    db.commit()
    db.refresh(pickup_slot)
    return pickup_slot

def get_pickup_slot_by_id(
    db: Session,
    pickup_slot_id: int,
) -> PickupSlot | None:
    """
    Retrieve a pickup slot by its ID.
    """

    return (
        db.query(PickupSlot)
        .filter(PickupSlot.id == pickup_slot_id)
        .first()
    )
    
def get_available_pickup_slot_by_id(
    db: Session,
    pickup_slot_id: int,
) -> PickupSlot | None:

    slot = (
        db.query(PickupSlot)
        .filter(
            PickupSlot.id == pickup_slot_id,
            PickupSlot.is_active.is_(True),
        )
        .first()
    )

    if (
        slot
        and slot.current_orders < slot.max_orders
    ):
        return slot

    return None