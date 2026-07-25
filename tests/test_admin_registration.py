import pytest
from datetime import time
from app.models.stall import FoodStall
from app.models.user import User
from app.enums.user_role import UserRole
from app.utils.security import hash_password

def test_admin_registration_and_profile_setup(client, db):
    # 1. Create a super admin and a stall
    admin = User(
        registration_number="AD000001",
        name="Super Admin",
        email="super@test.com",
        phone_number="9999999999",
        password_hash=hash_password("SuperSecret@123"),
        role=UserRole.ADMIN,
        profile_complete=True,
    )
    stall = FoodStall(
        name="Gupta Canteen",
        description="Best samosas",
        location="Block A",
        opening_time=time(8, 0),
        closing_time=time(20, 0),
    )
    db.add_all([admin, stall])
    db.commit()
    db.refresh(stall)

    # Login as Super Admin
    login_res = client.post(
        "/auth/login",
        data={"username": "AD000001", "password": "SuperSecret@123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get unassigned stalls
    unassigned_res = client.get("/admin/stalls/unassigned", headers=headers)
    assert unassigned_res.status_code == 200
    stalls = unassigned_res.json()
    assert len(stalls) == 1
    assert stalls[0]["name"] == "Gupta Canteen"

    # Register admin for Gupta Canteen
    reg_res = client.post(f"/admin/register?stall_id={stall.id}", headers=headers)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["stall_name"] == "Gupta Canteen"
    new_reg_num = reg_data["registration_number"]
    new_login_code = reg_data["login_code"]

    # Login as new admin
    new_login_res = client.post(
        "/auth/login",
        data={"username": new_reg_num, "password": new_login_code},
    )
    assert new_login_res.status_code == 200
    new_token = new_login_res.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # Verify user profile complete is False
    me_res = client.get("/users/me", headers=new_headers)
    assert me_res.status_code == 200
    assert me_res.json()["profile_complete"] is False

    # Complete profile
    setup_res = client.post(
        "/admin/profile/setup",
        json={"name": "Ramesh Gupta", "phone_number": "9876543210"},
        headers=new_headers,
    )
    assert setup_res.status_code == 200
    assert setup_res.json()["name"] == "Ramesh Gupta"
    assert setup_res.json()["profile_complete"] is True

    # Get assigned stall
    stall_res = client.get("/admin/profile/stall", headers=new_headers)
    assert stall_res.status_code == 200
    assert stall_res.json()["name"] == "Gupta Canteen"
