import pytest
from datetime import date, time
from decimal import Decimal

from app.models.stall import FoodStall
from app.models.menu_item import MenuItem
from app.enums.menu_category import MenuCategory

def test_get_stalls_and_menu_items(client, db):
    # Setup stall & menu item
    stall = FoodStall(name="Canteen Stall 1", description="Main Canteen", location="Block A", is_open=True)
    db.add(stall)
    db.commit()
    db.refresh(stall)

    item1 = MenuItem(
        stall_id=stall.id,
        name="Veg Sandwich",
        category=MenuCategory.SNACK,
        current_price=Decimal("40.00"),
        preparation_time=5,
        is_available=True
    )
    item2 = MenuItem(
        stall_id=stall.id,
        name="Chicken Burger",
        category=MenuCategory.MAIN_COURSE,
        current_price=Decimal("90.00"),
        preparation_time=12,
        is_available=True
    )
    db.add_all([item1, item2])
    db.commit()

    # 1. Test GET /stalls/
    res = client.get("/stalls/")
    assert res.status_code == 200
    stalls_data = res.json()
    assert len(stalls_data) >= 1
    assert any(s["name"] == "Canteen Stall 1" for s in stalls_data)

    # 2. Test GET /stalls/{id}
    res = client.get(f"/stalls/{stall.id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Canteen Stall 1"

    # 3. Test GET /menu-items/
    res = client.get("/menu-items/")
    assert res.status_code == 200
    items_data = res.json()
    assert len(items_data) >= 2
    names = [i["name"] for i in items_data]
    assert "Veg Sandwich" in names
    assert "Chicken Burger" in names

    # 4. Test GET /menu-items/{item_id}
    res = client.get(f"/menu-items/{item1.id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Veg Sandwich"
    assert Decimal(str(res.json()["current_price"])) == Decimal("40.00")
