from sqlalchemy.orm import Session

from app.models.stall import FoodStall


def get_food_stall_by_id(
    db: Session,
    stall_id: int,
) -> FoodStall | None:
    return (
        db.query(FoodStall)
        .filter(FoodStall.id == stall_id)
        .first()
    )


def get_food_stall_by_name(
    db: Session,
    name: str,
) -> FoodStall | None:
    return (
        db.query(FoodStall)
        .filter(FoodStall.name == name)
        .first()
    )


def get_all_food_stalls(
    db: Session,
) -> list[FoodStall]:
    return (
        db.query(FoodStall)
        .order_by(FoodStall.name)
        .all()
    )
    
