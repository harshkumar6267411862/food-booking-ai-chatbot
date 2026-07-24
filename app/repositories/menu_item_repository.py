from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.models.stall import FoodStall


def get_food_stall_by_id(
    db: Session,
    stall_id: int,
):
    return (
        db.query(FoodStall)
        .filter(FoodStall.id == stall_id)
        .first()
    )


def get_menu_item_by_name_and_stall(
    db: Session,
    stall_id: int,
    name: str,
):
    return (
        db.query(MenuItem)
        .filter(
            MenuItem.stall_id == stall_id,
            MenuItem.name == name,
        )
        .first()
    )


def create_menu_item(
    db: Session,
    menu_item: MenuItem,
):
    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)

    return menu_item

def update_menu_item(
    db: Session,
    menu_item: MenuItem,
) -> MenuItem:

    db.commit()
    db.refresh(menu_item)

    return menu_item

def get_menu_item_by_id(
    db: Session,
    menu_item_id: int,
) -> MenuItem | None:
    """
    Retrieve a menu item by its ID.
    """

    return (
        db.query(MenuItem)
        .filter(MenuItem.id == menu_item_id)
        .first()
    )


def get_all_menu_items(
    db: Session,
    stall_id: int | None = None,
    category: str | None = None,
    is_available: bool | None = None,
) -> list[MenuItem]:
    """
    Retrieve menu items with optional filtering.
    """
    query = db.query(MenuItem)
    if stall_id is not None:
        query = query.filter(MenuItem.stall_id == stall_id)
    if category is not None:
        query = query.filter(MenuItem.category == category)
    if is_available is not None:
        query = query.filter(MenuItem.is_available == is_available)
    return query.all()


def get_menu_items_by_stall_id(
    db: Session,
    stall_id: int,
) -> list[MenuItem]:

    return (
        db.query(MenuItem)
        .filter(
            MenuItem.stall_id == stall_id,
            MenuItem.is_available == True,
        )
        .order_by(MenuItem.id)
        .all()
    )