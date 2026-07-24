from sqlalchemy.orm import Session

from app.models.user import User

def get_user_by_registration_number(db: Session,registration_number: str,):
    return (
        db.query(User).filter(User.registration_number == registration_number).first()
    )
    
def get_user_by_email(db: Session, email: str,):
    return(
        db.query(User).filter(User.email == email).first()
    )

def create_user(db: Session, user: User,):
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

def get_user_by_phone(db: Session, phone_number: str):
    return (
        db.query(User).filter(User.phone_number == phone_number).first()
    )
    
def update_user_name(
    db: Session,
    user: User,
    name: str,
) -> User:
    user.name = name

    db.commit()
    db.refresh(user)

    return user


def update_user_registration_number(
    db: Session,
    user: User,
    registration_number: str,
) -> User:
    user.registration_number = registration_number

    db.commit()
    db.refresh(user)

    return user