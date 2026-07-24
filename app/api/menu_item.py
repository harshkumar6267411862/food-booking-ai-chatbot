from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.menu_item import (
    MenuItemCreateRequest,
    MenuItemCreateResponse,
    MenuItemResponse,
)
from app.services.menu_item_service import (
    create_menu_item as create_menu_item_service,
    get_menu_items,
    get_menu_item_by_id_service,
)
from app.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/menu-items",
    tags=["Menu Items"],
)


@router.post(
    "/",
    response_model=MenuItemCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_item_endpoint(
    menu_data: MenuItemCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_menu_item_service(
        db=db,
        menu_data=menu_data,
        current_user=current_user,
    )


@router.get(
    "/",
    response_model=list[MenuItemResponse],
)
def list_menu_items(
    stall_id: int | None = None,
    category: str | None = None,
    is_available: bool | None = True,
    db: Session = Depends(get_db),
):
    """
    Retrieve available menu items (public for students & chatbot).
    """
    return get_menu_items(
        db=db,
        stall_id=stall_id,
        category=category,
        is_available=is_available,
    )


@router.get(
    "/{item_id}",
    response_model=MenuItemResponse,
)
def get_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve single menu item by ID.
    """
    return get_menu_item_by_id_service(db=db, menu_item_id=item_id)