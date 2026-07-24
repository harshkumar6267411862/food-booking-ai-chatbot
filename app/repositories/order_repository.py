from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order
from app.enums.order_status import OrderStatus


def create_order(db: Session, order: Order) -> Order:
    """
    Save a new order to the database.
    """

    db.add(order)
    db.flush()

    return order


def get_order_by_id(db: Session, order_id: int) -> Order | None:
    """
    Retrieve an order by its ID.
    """

    return (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )


def get_orders_by_user(db: Session, user_id: int) -> list[Order]:
    """
    Retrieve all orders placed by a user.
    """

    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    
def get_pending_orders(db: Session) -> list[Order]:
    """
    Fetch all pending orders with related data.
    """

    return (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.pickup_slot),
            joinedload(Order.order_items).joinedload(OrderItem.menu_item),
        )
        .filter(Order.status == OrderStatus.PENDING)
        .order_by(Order.created_at.asc())
        .all()
    )
    
def get_latest_active_order_by_user(
    db: Session,
    user_id: int,
) -> Order | None:
    """
    Retrieve the user's most recent active order.
    Active means the order is not completed or cancelled.
    """

    return (
        db.query(Order)
        .filter(
            Order.user_id == user_id,
            Order.status.in_(
                [
                    OrderStatus.PENDING,
                    OrderStatus.CONFIRMED,
                    OrderStatus.PREPARING,
                    OrderStatus.READY,
                ]
            ),
        )
        .order_by(Order.created_at.desc())
        .first()
    )