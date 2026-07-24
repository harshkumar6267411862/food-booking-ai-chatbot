from sqlalchemy.orm import Session

from app.models.cart import Cart


def get_cart_by_user_id(
    db: Session,
    user_id: int,
) -> Cart | None:

    return (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .first()
    )


def create_cart(
    db: Session,
    cart: Cart,
) -> Cart:

    db.add(cart)
    db.commit()
    db.refresh(cart)

    return cart


def get_or_create_cart(
    db: Session,
    user_id: int,
) -> Cart:

    cart = get_cart_by_user_id(
        db,
        user_id,
    )

    if cart:
        return cart

    cart = Cart(
        user_id=user_id,
    )

    return create_cart(
        db,
        cart,
    )


def delete_cart(
    db: Session,
    cart: Cart,
) -> None:

    db.delete(cart)
    db.commit()