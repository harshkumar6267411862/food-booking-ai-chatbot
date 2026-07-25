from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.order import OrderResponse, OrderAdminResponse, MarkReadyResponse, VerifyOTPRequest, CancelOrderRequest
from app.services.order_service import (
    confirm_order, 
    get_pending_orders_for_admin,
    start_preparing_order,
    mark_order_ready,
    verify_otp_and_complete_order,
    cancel_order,
    auto_cancel_pending_orders,
)
from app.repositories.order_repository import get_order_by_id

from app.enums.cancelled_by import CancelledBy
from app.services.auth_service import get_current_admin

router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin Orders"],
)

def verify_admin_stall_ownership(current_admin: User, order_stall_id: int):
    if current_admin.stall_id is None or current_admin.stall_id != order_stall_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to manage orders for this stall.",
        )


@router.patch(
    "/{order_id}/confirm",
    response_model=OrderResponse,
)
def confirm_order_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Confirm a pending order.
    """
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    verify_admin_stall_ownership(current_admin, order.stall_id)

    return confirm_order(
        db=db,
        order_id=order_id,
    )
    
@router.get(
    "/pending",
    response_model=list[OrderAdminResponse],
)
def get_pending_orders(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Retrieve all pending orders for the logged-in admin's stall.
    """
    if current_admin.stall_id is None:
        return []
    return get_pending_orders_for_admin(db, stall_id=current_admin.stall_id)

@router.patch(
    "/{order_id}/prepare",
    response_model=OrderResponse,
)
def prepare_order_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Start preparing a confirmed order.
    """
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    verify_admin_stall_ownership(current_admin, order.stall_id)

    return start_preparing_order(db=db, order_id=order_id)


@router.patch(
    "/{order_id}/ready",
    response_model=MarkReadyResponse,
)
def mark_order_ready_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Mark an order as ready for pickup.
    Returns the order details and the plain-text OTP for the user.
    """
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    verify_admin_stall_ownership(current_admin, order.stall_id)

    ready_order_obj, otp = mark_order_ready(db=db, order_id=order_id)
    return MarkReadyResponse(order=OrderAdminResponse.model_validate(ready_order_obj), otp=otp)


@router.post(
    "/{order_id}/verify-otp",
    response_model=OrderResponse,
)
def verify_otp_endpoint(
    order_id: int,
    request: VerifyOTPRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Verify the OTP and complete the order.
    """
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    verify_admin_stall_ownership(current_admin, order.stall_id)

    return verify_otp_and_complete_order(
        db=db, 
        order_id=order_id, 
        otp=request.otp
    )


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_order_admin_endpoint(
    order_id: int,
    request: CancelOrderRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Cancel an order by admin (with reason).
    """
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    verify_admin_stall_ownership(current_admin, order.stall_id)

    return cancel_order(
        db=db,
        order_id=order_id,
        cancel_reason=request.cancel_reason,
        cancelled_by=CancelledBy.ADMIN,
    )



@router.post(
    "/cron/auto-cancel",
    response_model=dict,
)
def auto_cancel_endpoint(
    db: Session = Depends(get_db),
    # Optional: secure this endpoint if it's hit by an external cron
    # current_admin: User = Depends(get_current_admin), 
):
    """
    Automatically cancel pending orders that are older than 5 minutes.
    Can be called by a cron job or background task.
    """
    cancelled_count = auto_cancel_pending_orders(db)
    return {"message": f"Successfully auto-cancelled {cancelled_count} orders."}