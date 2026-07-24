from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, CancelOrderRequest
from app.enums.cancelled_by import CancelledBy
from app.services.auth_service import get_current_user
from app.services.order_service import create_order

from app.services.order_service import (
    create_order,
    get_my_orders,
    cancel_order,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_order(
        db=db,
        user_id=current_user.id,
        order_data=order_data,
    )
    
@router.get(
    "/me",
    response_model=list[OrderResponse],
)
def get_my_orders_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_orders(
        db=db,
        user_id=current_user.id,
    )

@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_order_endpoint(
    order_id: int,
    request: CancelOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel an order by student.
    """
    return cancel_order(
        db=db,
        order_id=order_id,
        cancel_reason=request.cancel_reason,
        cancelled_by=CancelledBy.USER,
        user_id=current_user.id,
    )