import pytest
from datetime import date, time
from decimal import Decimal

from app.models.stall import FoodStall
from app.models.menu_item import MenuItem
from app.models.pickup_slot import PickupSlot
from app.models.user import User
from app.enums.menu_category import MenuCategory
from app.enums.user_role import UserRole
from app.utils.security import hash_password

@pytest.fixture
def setup_data(db, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "WHATSAPP_PROVIDER", "mock")
    stall = FoodStall(name="Test Stall", description="Test", location="A1", opening_time=time(0, 0), closing_time=time(23, 59))
    db.add(stall)
    db.commit()
    db.refresh(stall)

    menu_item = MenuItem(stall_id=stall.id, name="Test Burger", category=MenuCategory.MAIN_COURSE, current_price=Decimal("50.00"), preparation_time=10)
    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)

    slot = PickupSlot(slot_date=date.today(), start_time=time(12, 0), end_time=time(13, 0), max_orders=10, current_orders=0, estimated_wait_minutes=5)
    db.add(slot)
    db.commit()
    db.refresh(slot)
    
    admin = User(
        registration_number="ADMIN001",
        name="Admin",
        email="admin@test.com",
        phone_number="9876543211",
        password_hash=hash_password("Password1!"),
        role=UserRole.ADMIN,
        stall_id=stall.id,
    )
    db.add(admin)
    db.commit()

    return {"stall": stall, "menu_item": menu_item, "slot": slot, "admin": admin}

def test_full_order_lifecycle(client, setup_data):
    # 1. Register User
    res = client.post("/auth/register", json={
        "registration_number": "12345678",
        "name": "Test User",
        "email": "test@test.com",
        "phone_number": "9876543210",
        "password": "Password1!"
    })
    assert res.status_code == 201

    # 2. Login User
    res = client.post("/auth/login", data={"username": "12345678", "password": "Password1!"})
    assert res.status_code == 200
    user_token = res.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. Login Admin
    res = client.post("/auth/login", data={"username": "ADMIN001", "password": "Password1!"})
    assert res.status_code == 200
    admin_token = res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 4. Create Order
    menu_item_id = setup_data["menu_item"].id
    slot_id = setup_data["slot"].id
    res = client.post("/orders/", headers=user_headers, json={
        "pickup_slot_id": slot_id,
        "items": [{"menu_item_id": menu_item_id, "quantity": 2}]
    })
    assert res.status_code == 201
    order_id = res.json()["id"]

    # 5. Admin confirms order
    res = client.patch(f"/admin/orders/{order_id}/confirm", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "CONFIRMED"

    # 6. Admin starts preparing
    res = client.patch(f"/admin/orders/{order_id}/prepare", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "PREPARING"

    # 7. Admin marks ready
    res = client.patch(f"/admin/orders/{order_id}/ready", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["order"]["status"] == "READY"
    otp = res.json()["otp"]
    assert len(otp) == 6

    # 8. Admin verifies OTP and completes
    res = client.post(f"/admin/orders/{order_id}/verify-otp", headers=admin_headers, json={"otp": otp})
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"
