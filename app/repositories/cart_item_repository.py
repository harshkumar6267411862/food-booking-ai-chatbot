from sqlalchemy.orm import Session

from app.models.cart_item import CartItem


def get_cart_item(
    db: Session,
    cart_id: int,
    menu_item_id: int,
) -> CartItem | None:

    return (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart_id,
            CartItem.menu_item_id == menu_item_id,
        )
        .first()
    )


def get_cart_items(
    db: Session,
    cart_id: int,
) -> list[CartItem]:

    return (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart_id)
        .all()
    )


def create_cart_item(
    db: Session,
    cart_item: CartItem,
) -> CartItem:

    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return cart_item


def update_cart_item(
    db: Session,
    cart_item: CartItem,
) -> CartItem:

    db.commit()
    db.refresh(cart_item)

    return cart_item


def delete_cart_item(
    db: Session,
    cart_item: CartItem,
) -> None:

    db.delete(cart_item)
    db.commit()