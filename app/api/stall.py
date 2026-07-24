from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.stall import FoodStallResponse
from app.services.stall_service import get_stalls, get_stall_by_id

router = APIRouter(
    prefix="/stalls",
    tags=["Food Stalls"],
)


@router.get("/", response_model=list[FoodStallResponse])
def list_stalls(
    only_open: bool = False,
    db: Session = Depends(get_db),
):
    """
    Retrieve all food stalls.
    """
    return get_stalls(db=db, only_open=only_open)


@router.get("/{stall_id}", response_model=FoodStallResponse)
def get_stall(
    stall_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve details for a specific stall.
    """
    return get_stall_by_id(db=db, stall_id=stall_id)
