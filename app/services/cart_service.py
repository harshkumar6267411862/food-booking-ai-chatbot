from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.models.menu_item import MenuItem

from app.repositories.cart_repository import get_or_create_cart
from app.repositories.cart_item_repository import (
    create_cart_item,
    get_cart_item,
    update_cart_item,
)
from app.repositories.cart_item_repository import get_cart_items


def add_item_to_cart(
    db: Session,
    user_id: int,
    menu_item: MenuItem,
) -> CartItem:

    cart = get_or_create_cart(
        db,
        user_id,
    )

    cart_item = get_cart_item(
        db,
        cart.id,
        menu_item.id,
    )

    if cart_item:

        cart_item.quantity += 1

        return update_cart_item(
            db,
            cart_item,
        )

    cart_item = CartItem(
        cart_id=cart.id,
        menu_item_id=menu_item.id,
        quantity=1,
        price_at_purchase=menu_item.current_price,
    )

    return create_cart_item(
        db,
        cart_item,
    )
    
def calculate_cart_total(
    db: Session,
    user_id: int,
) -> Decimal:

    cart = get_or_create_cart(
        db,
        user_id,
    )

    total = Decimal("0.00")

    for item in get_cart_items(
        db,
        cart.id,
    ):
        total += (
            item.price_at_purchase * item.quantity
        )

    return total

def get_cart_summary(
    db: Session,
    user_id: int,
) -> str:

    cart = get_or_create_cart(
        db,
        user_id,
    )

    cart_items = get_cart_items(
        db,
        cart.id,
    )

    if not cart_items:
        return "🛒 Your cart is empty."

    response = "🛒 *Your Cart*\n\n"

    for item in cart_items:

        subtotal = (
            item.quantity *
            item.price_at_purchase
        )

        response += (
            f"{item.quantity} × "
            f"{item.menu_item.name} "
            f"₹{subtotal}\n"
        )

    total = calculate_cart_total(
        db,
        user_id,
    )

    response += (
        f"\n💰 *Total:* ₹{total}"
    )

    return response
    
