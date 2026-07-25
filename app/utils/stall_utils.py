from datetime import datetime
from app.models.stall import FoodStall


def is_stall_open(stall: FoodStall) -> bool:
    current_time = datetime.now().time()

    return (
        stall.opening_time
        <= current_time
        <= stall.closing_time
    )