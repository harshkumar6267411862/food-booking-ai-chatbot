"""
cleanup_admin_users.py
----------------------
Deletes all ADMIN-role users from the database EXCEPT the seeded
system admin (admin@test.com / AD000001).

Run from the project root:
    python scripts/cleanup_admin_users.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.enums.user_role import UserRole

KEEP_EMAIL = "admin@test.com"  # The seeded system admin — never delete this


def cleanup():
    db = SessionLocal()
    try:
        # Find all ADMIN users excluding the seeded one
        admins_to_delete = (
            db.query(User)
            .filter(
                User.role == UserRole.ADMIN,
                User.email != KEEP_EMAIL,
            )
            .all()
        )

        if not admins_to_delete:
            print("No stall admin users found to delete. DB is already clean.")
            return

        print(f"Found {len(admins_to_delete)} stall admin(s) to delete:")
        for admin in admins_to_delete:
            print(
                f"  - ID={admin.id} | reg={admin.registration_number} "
                f"| stall_id={admin.stall_id} | email={admin.email}"
            )

        # Non-interactive for automation
        for admin in admins_to_delete:
            db.delete(admin)

        db.commit()
        print(f"\nDeleted {len(admins_to_delete)} stall admin(s) successfully.")
        print("   Stalls are now unassigned and ready for fresh registration.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cleanup()
