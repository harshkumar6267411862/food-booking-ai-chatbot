from datetime import datetime,date, time
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.pickup_slot import PickupSlotResponse
from app.schemas.menu_item import MenuItemSummary
from app.schemas.auth import UserSummary
from app.enums.order_status import OrderStatus

class OrderItemCreate(BaseModel):
    """
    Represents a single menu item in an order.
    """

    menu_item_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    """
    Request body for creating an order.
    """

    pickup_slot_id: int
    items: list[OrderItemCreate]
    
    
# class PickupSlotResponse(BaseModel):
#     slot_date: date
#     start_time: time
#     end_time: time

#     model_config = ConfigDict(from_attributes=True)
    
class OrderItemResponse(BaseModel):
    menu_item: MenuItemSummary
    quantity: int
    price_at_purchase: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """
    Response returned after creating or fetching an order.
    """

    id: int
    order_number: str
    status: OrderStatus
    total_amount: Decimal
    pickup_slot: PickupSlotResponse
    order_items: list[OrderItemResponse]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    

class OrderAdminResponse(BaseModel):
    id: int
    order_number: str
    status: OrderStatus
    total_amount: Decimal

    user: UserSummary

    pickup_slot: PickupSlotResponse
    order_items: list[OrderItemResponse]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
    
class CancelOrderRequest(BaseModel):
    cancel_reason: str = Field(
        min_length=5,
        max_length=255,
    )

class VerifyOTPRequest(BaseModel):
    otp: str = Field(
        min_length=6,
        max_length=6,
    )

class MarkReadyResponse(BaseModel):
    order: OrderAdminResponse
    otp: str