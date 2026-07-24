import getpass
from secrets import randbelow

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.enums.user_role import UserRole
from app.models.user import User
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_registration_number,
)
from app.utils.security import hash_password


def generate_admin_registration_number(db: Session) -> str:
    """
    Generates a unique admin registration number.

    Example:
        AD483921
    """

    while True:
        registration_number = f"AD{randbelow(900000) + 100000}"

        existing_admin = get_user_by_registration_number(
            db=db,
            registration_number=registration_number,
        )

        if not existing_admin:
            return registration_number


def create_admin():

    db = SessionLocal()

    try:

        print("=" * 60)
        print("Create New Administrator")
        print("=" * 60)

        name = input("Admin Name        : ").strip()
        email = input("Email             : ").strip()
        phone_number = input("Phone Number      : ").strip()
        password = getpass.getpass("Password          : ")

        existing_email = get_user_by_email(
            db=db,
            email=email,
        )

        if existing_email:
            print("\nAn admin with this email already exists.")
            return

        admin = User(
            registration_number=generate_admin_registration_number(db),
            name=name,
            email=email,
            phone_number=phone_number,
            role=UserRole.ADMIN,
            password_hash=hash_password(password),
        )

        created_admin = create_user(
            db=db,
            user=admin,
        )

        print("\n" + "=" * 60)
        print("Administrator Created Successfully")
        print("=" * 60)
        print(f"Registration Number : {created_admin.registration_number}")
        print(f"Name                : {created_admin.name}")
        print(f"Email               : {created_admin.email}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()