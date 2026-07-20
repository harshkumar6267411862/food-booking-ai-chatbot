from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    PREPARING = "Preparing"
    READY = "Ready"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"