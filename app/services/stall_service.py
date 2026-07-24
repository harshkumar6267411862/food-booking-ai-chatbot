from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.stall import FoodStall
from app.repositories.stall_repository import (
    get_all_food_stalls,
    get_food_stall_by_id,
)

def get_stalls(db: Session, only_open: bool = False) -> list[FoodStall]:
    stalls = get_all_food_stalls(db)
    if only_open:
        stalls = [s for s in stalls if s.is_open]
    return stalls

def get_stall_by_id(db: Session, stall_id: int) -> FoodStall:
    stall = get_food_stall_by_id(db, stall_id)
    if not stall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food stall with ID {stall_id} not found."
        )
    return stall
