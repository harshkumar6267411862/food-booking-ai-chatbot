from enum import Enum


class NotificationType(str, Enum):
    ORDER_CONFIRMED = "Order Confirmed"
    ORDER_READY = "Order Ready"
    ORDER_CANCELLED = "Order Cancelled"
    REMINDER = "Reminder"