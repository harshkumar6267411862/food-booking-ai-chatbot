from datetime import time
from app.database import SessionLocal
from app.models.stall import FoodStall
from app.repositories.stall_repository import (
    get_food_stall_by_name,
)


STALLS = [
    {
        "name": "Vishal Dhaba",
        "description": "Vishal Dhaba",
        "location": "BLOCK-27",
        "opening_time": time(8, 0),
        "closing_time": time(22, 0),
    },
    {
        "name": "Gupta Canteen",
        "description": "Gupta Canteen",
        "location": "BLOCK-28",
        "opening_time": time(8, 0),
        "closing_time": time(22, 0),
    },
    {
        "name": "Kitchen Ette",
        "description": "Kitchen Ette",
        "location": "CC",
        "opening_time": time(8, 0),
        "closing_time": time(22, 0),
    },
    {
        "name": "Ahuja",
        "description": "Ahuja Canteen",
        "location": "UNIMALL",
        "opening_time": time(8, 0),
        "closing_time": time(22, 0),
    },
    {
        "name": "Chai Vyanjan",
        "description": "Chai Vyanjan",
        "location": "UNIMALL",
        "opening_time": time(8, 0),
        "closing_time": time(22, 0),
    },
]


def seed_stalls():
    db = SessionLocal()

    try:
        for stall_data in STALLS:

            existing = get_food_stall_by_name(
                db=db,
                name=stall_data["name"],
            )

            if existing:
                print(f"✔ {stall_data['name']} already exists.")
                continue

            stall = FoodStall(**stall_data)

            db.add(stall)
            db.commit()

            print(f"✅ Added {stall.name}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_stalls()