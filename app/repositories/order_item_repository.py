from sqlalchemy.orm import Session

from app.models.order_item import OrderItem
from app.models.order import Order


def create_order_item(db: Session, order_item: OrderItem) -> OrderItem:
    """
    Save a single order item.
    """

    db.add(order_item)

    return order_item


def create_order_items(
    db: Session,
    order_items: list[OrderItem],
) -> list[OrderItem]:
    """
    Save multiple order items.
    """

    db.add_all(order_items)

    return order_items


def get_order_items_by_order(
    db: Session,
    order_id: int,
) -> list[OrderItem]:
    """
    Retrieve all items belonging to an order.
    """

    return (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id)
        .all()
    )
    
def get_order_by_id(
    db: Session,
    order_id: int,
) -> Order | None:
    return (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )


def get_all_orders(
    db: Session,
) -> list[Order]:
    return (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .all()
    )