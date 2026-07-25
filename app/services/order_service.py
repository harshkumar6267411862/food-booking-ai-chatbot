from decimal import Decimal
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.repositories.menu_item_repository import get_menu_item_by_id
from app.repositories.order_item_repository import create_order_items
from app.repositories.order_repository import create_order as repo_create_order
from app.repositories.pickup_slot_repository import get_pickup_slot_by_id
from app.schemas.order import OrderCreate,OrderItemCreate
from app.services.whatsapp_service import send_whatsapp_message
from app.enums.order_status import OrderStatus
from app.repositories.order_repository import get_order_by_id
from app.repositories.order_repository import (
    get_orders_by_user,
)

from app.repositories.cart_repository import (
    get_cart_by_user_id,
    delete_cart,
)

from app.repositories.cart_item_repository import (
    get_cart_items,
)
from app.utils.security import generate_otp, hash_otp, verify_otp
from app.enums.cancelled_by import CancelledBy
from app.repositories.order_repository import get_pending_orders, get_pending_orders_by_stall
from app.services.whatsapp_service import send_whatsapp_message

def generate_order_number(order_id: int) -> str:
    """
    Generate a readable order number.
    """

    return f"ORD{order_id:06d}"

def create_order(
    db: Session,
    user_id: int,
    order_data: OrderCreate,
) -> Order:
    pickup_slot = get_pickup_slot_by_id(
        db,
        order_data.pickup_slot_id,
    )

    if pickup_slot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pickup slot not found.",
        )

    if pickup_slot.current_orders >= pickup_slot.max_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pickup slot is full.",
        )

    total_amount = Decimal("0.00")
    validated_items: list[tuple] = []

    for item in order_data.items:
        menu_item = get_menu_item_by_id(
            db,
            item.menu_item_id,
        )

        if menu_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item {item.menu_item_id} not found.",
            )

        if not menu_item.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{menu_item.name} is unavailable.",
            )

        total_amount += menu_item.current_price * item.quantity
        validated_items.append((item, menu_item))

    stall_id = validated_items[0][1].stall_id if validated_items else None

    order = Order(
        order_number="TEMP",
        user_id=user_id,
        stall_id=stall_id,
        pickup_slot_id=pickup_slot.id,
        total_amount=total_amount,
    )

    try:
        repo_create_order(db, order)

        order.order_number = generate_order_number(order.id)

        order_items = []

        for request_item, menu_item in validated_items:
            order_items.append(
                OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=request_item.quantity,
                    price_at_purchase=menu_item.current_price,
                )
            )

        create_order_items(db, order_items)

        pickup_slot.current_orders += 1

        db.commit()
        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise
    
    
def create_order_from_cart(
    db: Session,
    user_id: int,
    pickup_slot_id: int,
) -> Order:

    cart = get_cart_by_user_id(
        db=db,
        user_id=user_id,
    )

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty.",
        )

    cart_items = get_cart_items(
        db=db,
        cart_id=cart.id,
    )

    if len(cart_items) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty.",
        )

    order_items = [
        OrderItemCreate(
            menu_item_id=item.menu_item_id,
            quantity=item.quantity,
        )
        for item in cart_items
    ]

    order_data = OrderCreate(
        pickup_slot_id=pickup_slot_id,
        items=order_items,
    )

    order = create_order(
        db=db,
        user_id=user_id,
        order_data=order_data,
    )

    delete_cart(
        db=db,
        cart=cart,
    )

    return order
    
def get_my_orders(
    db: Session,
    user_id: int,
) -> list[Order]:
    """
    Retrieve all orders belonging to the authenticated user.
    """

    return get_orders_by_user(
        db=db,
        user_id=user_id,
    )
    
def confirm_order(
    db: Session,
    order_id: int,
) -> Order:
    """
    Confirm a pending order.
    """

    order = get_order_by_id(
        db=db,
        order_id=order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    update_order_status(
        order=order,
        new_status=OrderStatus.CONFIRMED,
    )

    db.commit()
    db.refresh(order)

    return order
    
    
ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING: {
        OrderStatus.CONFIRMED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.CONFIRMED: {
        OrderStatus.PREPARING,
    },
    OrderStatus.PREPARING: {
        OrderStatus.READY,
    },
    OrderStatus.READY: {
        OrderStatus.COMPLETED,
    },
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}

def set_status_timestamp(
    order: Order,
    new_status: OrderStatus,
    now: datetime,
) -> None:

    now = datetime.now(timezone.utc)

    if new_status == OrderStatus.CONFIRMED:
        order.accepted_at = now

    elif new_status == OrderStatus.PREPARING:
        order.preparing_at = now

    elif new_status == OrderStatus.READY:
        order.ready_at = now

    elif new_status == OrderStatus.COMPLETED:
        order.completed_at = now

    elif new_status == OrderStatus.CANCELLED:
        order.cancelled_at = now
        
def update_order_status(
    order: Order,
    new_status: OrderStatus,
) -> tuple[Order, str | None]:

    allowed = ALLOWED_TRANSITIONS.get(
        order.status,
        set(),
    )

    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot change order from "
                f"{order.status.value} "
                f"to {new_status.value}."
            ),
        )

    now = datetime.now(timezone.utc)

    set_status_timestamp(
        order,
        new_status,
        now,
    )

    otp_value = None

    match new_status:

        case OrderStatus.READY:

            otp_value = generate_otp()

            order.pickup_otp_hash = hash_otp(otp_value)

            order.otp_generated_at = now

            if order.user and order.user.phone_number:
                
                msg = f"🎉 Order {order.order_number} is READY for pickup!\n\nYour Pickup OTP is: *{otp_value}*\n\nPlease present this OTP at the counter."
                send_whatsapp_message(order.user.phone_number, msg)

        case OrderStatus.CONFIRMED:
            if order.user and order.user.phone_number:
                
                msg = f"✅ Your order {order.order_number} has been CONFIRMED by the canteen! We will start preparing it soon."
                send_whatsapp_message(order.user.phone_number, msg)
        
        case OrderStatus.COMPLETED:

            if order.user and order.user.phone_number:
            
                msg = (
                    f"✅ *Order Collected*\n\n"
                    f"Your order *{order.order_number}* has been successfully collected.\n\n"
                    f"Thank you for using MunchBot! 🍽️\n\n"
                    f"Reply *HI* anytime to place another order."
                )

                send_whatsapp_message(
                    order.user.phone_number,
                    msg,
                )
                
        case OrderStatus.CANCELLED:

            if order.user and order.user.phone_number:
            
                reason = order.cancel_reason or "No reason provided."

                msg = (
                    f"❌ *Order Cancelled*\n\n"
                    f"Your order *{order.order_number}* has been cancelled.\n\n"
                    f"*Reason:*\n"
                    f"{reason}\n\n"
                    f"We apologize for the inconvenience.\n\n"
                    f"Reply *HI* to place a new order."
                )

                send_whatsapp_message(
                    order.user.phone_number,
                    msg,
                )

        case _:
            pass

    order.status = new_status

    return order, otp_value


def get_pending_orders_for_admin(
    db: Session,
    stall_id: int | None = None,
) -> list[Order]:
    """
    Retrieve all pending orders for the admin dashboard.
    If stall_id is provided, filter to that stall only.
    If stall_id is None (Super Admin), return an empty list.
    """
    if stall_id is not None:
        return get_pending_orders_by_stall(db, stall_id)
    return []


def start_preparing_order(db: Session, order_id: int) -> Order:
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    
    update_order_status(order, OrderStatus.PREPARING)
    db.commit()
    db.refresh(order)
    return order


def mark_order_ready(db: Session, order_id: int) -> tuple[Order, str]:
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    
    _, otp = update_order_status(order, OrderStatus.READY)
    assert otp is not None
    db.commit()
    db.refresh(order)
    return order,otp


def verify_otp_and_complete_order(db: Session, order_id: int, otp: str) -> Order:
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    
    if order.status != OrderStatus.READY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not ready for pickup.")
        
    if not order.pickup_otp_hash or not verify_otp(otp, order.pickup_otp_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP.")
        
    update_order_status(order, OrderStatus.COMPLETED)
    if order.pickup_slot.current_orders > 0:
        order.pickup_slot.current_orders -= 1
    order.otp_verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


def cancel_order(
    db: Session, 
    order_id: int, 
    cancel_reason: str, 
    cancelled_by: CancelledBy,
    user_id: int | None = None
) -> Order:
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        
    if cancelled_by == CancelledBy.USER:
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Users can only cancel pending orders.")
        if user_id is not None and order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this order.")
        
    if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already completed or cancelled.")
    
    order.cancel_reason = cancel_reason
    order.cancelled_by = cancelled_by
    update_order_status(order, OrderStatus.CANCELLED)
    
    if order.pickup_slot.current_orders > 0:
        order.pickup_slot.current_orders -= 1
    
    db.commit()
    db.refresh(order)
    return order

from datetime import timedelta

def auto_cancel_pending_orders(db: Session) -> int:
    """Cancels pending orders older than 5 minutes."""
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    
    pending_orders = get_pending_orders(db)
    cancelled_count = 0
    
    for order in pending_orders:
        order_time = order.created_at
        if order_time.tzinfo is None:
            order_time = order_time.replace(tzinfo=timezone.utc)
            
        if order_time < cutoff_time:
            order.cancel_reason = "Admin didn't accept the order within 5 mins"
            order.cancelled_by = CancelledBy.SYSTEM
            update_order_status(order, OrderStatus.CANCELLED)
            order.cancel_reason = "Admin didn't accept the order within 5 mins"
            order.cancelled_by = CancelledBy.SYSTEM
            if order.pickup_slot.current_orders > 0:
                order.pickup_slot.current_orders -= 1
            if order.user and order.user.phone_number:
                from app.services.whatsapp_service import send_whatsapp_message
                msg = f"⚠️ Order {order.order_number} was auto-cancelled because it was not accepted within 5 minutes."
                send_whatsapp_message(order.user.phone_number, msg)
            cancelled_count += 1
            
    if cancelled_count > 0:
        db.commit()
        
    return cancelled_count
