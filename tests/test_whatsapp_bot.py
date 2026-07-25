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
from app.services.whatsapp_service import SENT_MESSAGES, clear_sent_messages

@pytest.fixture
def setup_bot_data(db, monkeypatch):
    clear_sent_messages()
    from app.config import settings
    monkeypatch.setattr(settings, "WHATSAPP_PROVIDER", "mock")
    import app.services.pickup_slot_service as pss
    monkeypatch.setattr(pss, "CAFETERIA_OPENING_TIME", time(0, 0))
    monkeypatch.setattr(pss, "CAFETERIA_CLOSING_TIME", time(23, 59))

    stall = FoodStall(name="Bot Stall", description="Bot Canteen", location="Block B", opening_time=time(0, 0), closing_time=time(23, 59))
    db.add(stall)
    db.commit()
    db.refresh(stall)

    item1 = MenuItem(
        stall_id=stall.id,
        name="Samosa",
        category=MenuCategory.SNACK,
        current_price=Decimal("15.00"),
        preparation_time=5,
        is_available=True
    )
    db.add(item1)
    db.commit()
    db.refresh(item1)

    from datetime import datetime, timedelta
    now_dt = datetime.now()
    slot = PickupSlot(
        slot_date=now_dt.date(),
        start_time=(now_dt + timedelta(minutes=30)).time(),
        end_time=(now_dt + timedelta(minutes=90)).time(),
        max_orders=10,
        current_orders=0,
        estimated_wait_minutes=5
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    admin = User(
        registration_number="BOTADMIN",
        name="Bot Admin",
        email="botadmin@test.com",
        phone_number="9876543299",
        password_hash=hash_password("Password1!"),
        role=UserRole.ADMIN
    )
    db.add(admin)
    db.commit()

    return {"stall": stall, "menu_item": item1, "slot": slot, "admin": admin}


def test_whatsapp_webhook_verification(client):
    res = client.get("/webhook?hub.mode=subscribe&hub.verify_token=munchbot_secret_token&hub.challenge=999888777")
    assert res.status_code == 200
    assert res.text == "999888777"


def test_whatsapp_chatbot_ordering_flow(client, setup_bot_data):
    phone = "919876543210"
    item_id = setup_bot_data["menu_item"].id
    slot_id = setup_bot_data["slot"].id
    admin = setup_bot_data["admin"]

    # 1. Send HI
    res = client.post("/webhook", json={"from": phone, "text": "HI"})
    assert res.status_code == 200
    assert "Available Food Stalls" in res.json()["reply"]

    # 1.5 Select stall 1
    res = client.post("/webhook", json={"from": phone, "text": "1"})
    assert res.status_code == 200

    # 2. Select item number 1
    res = client.post("/webhook", json={"from": phone, "text": "1"})
    assert res.status_code == 200

    # 2.5 Send DONE
    res = client.post("/webhook", json={"from": phone, "text": "DONE"})
    assert res.status_code == 200

    # 3. View & select slot 1 (places order)
    res = client.post("/webhook", json={"from": phone, "text": "1"})
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "Order Placed Successfully" in reply
    assert "ORD" in reply

    # Extract order number/id from orders DB
    login_res = client.post("/auth/login", data={"username": admin.registration_number, "password": "Password1!"})
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    pending_res = client.get("/admin/orders/pending", headers=admin_headers)
    assert pending_res.status_code == 200
    orders = pending_res.json()
    assert len(orders) >= 1
    order_id = orders[0]["id"]

    # 6. Admin confirms & marks ready
    client.patch(f"/admin/orders/{order_id}/confirm", headers=admin_headers)
    client.patch(f"/admin/orders/{order_id}/prepare", headers=admin_headers)
    ready_res = client.patch(f"/admin/orders/{order_id}/ready", headers=admin_headers)
    assert ready_res.status_code == 200

    # 7. Check that outbound WhatsApp message was dispatched with OTP
    assert len(SENT_MESSAGES) > 0
    ready_msgs = [m for m in SENT_MESSAGES if "Pickup OTP" in m["text"]]
    assert len(ready_msgs) >= 1
    assert ready_res.json()["otp"] in ready_msgs[0]["text"]
