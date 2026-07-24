from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.enums.user_role import UserRole
from app.models.menu_item import MenuItem
from app.models.user import User

from app.repositories.menu_item_repository import (
    get_food_stall_by_id,
    get_menu_item_by_name_and_stall,
    create_menu_item as create_menu_item_repo,
    get_all_menu_items,
    get_menu_item_by_id,
)

from app.schemas.menu_item import (
    MenuItemCreateRequest,
    MenuItemCreateResponse,
)


def create_menu_item(
    db: Session,
    menu_data: MenuItemCreateRequest,
    current_user: User,
) -> MenuItemCreateResponse:

    # Admin Authorization
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only admins can create menu items."
        )

    # Stall Validation
    food_stall = get_food_stall_by_id(
        db=db,
        stall_id=menu_data.stall_id,
    )

    if not food_stall:
        raise HTTPException(
            status_code=404,
            detail="Food stall not found."
        )

    # Price Validation
    if menu_data.current_price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Current price must be greater than zero."
        )

    # Preparation Time Validation
    if menu_data.preparation_time <= 0:
        raise HTTPException(
            status_code=400,
            detail="Preparation time must be greater than zero."
        )

    # Duplicate Check
    existing_menu_item = get_menu_item_by_name_and_stall(
        db=db,
        stall_id=menu_data.stall_id,
        name=menu_data.name,
    )

    if existing_menu_item:
        raise HTTPException(
            status_code=409,
            detail="Menu item already exists for this food stall."
        )

    # SQLAlchemy Object
    menu_item = MenuItem(
        stall_id=menu_data.stall_id,
        name=menu_data.name,
        description=menu_data.description,
        category=menu_data.category,
        current_price=menu_data.current_price,
        preparation_time=menu_data.preparation_time,
        image_url=menu_data.image_url,
    )

    # Repository Call
    created_menu_item = create_menu_item_repo(
        db=db,
        menu_item=menu_item,
    )

    # Response
    return MenuItemCreateResponse.model_validate(created_menu_item)


def get_menu_items(
    db: Session,
    stall_id: int | None = None,
    category: str | None = None,
    is_available: bool | None = None,
) -> list[MenuItem]:
    return get_all_menu_items(
        db=db,
        stall_id=stall_id,
        category=category,
        is_available=is_available,
    )


def get_menu_item_by_id_service(
    db: Session,
    menu_item_id: int,
) -> MenuItem:
    item = get_menu_item_by_id(db=db, menu_item_id=menu_item_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Menu item {menu_item_id} not found."
        )
    return item