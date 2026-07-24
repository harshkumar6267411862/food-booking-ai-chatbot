from sqlalchemy.orm import Session
from datetime import datetime
from app.enums.chat_state import ChatState
from app.models.user_session import UserSession


def get_session_by_user_id(db: Session, user_id: int) -> UserSession | None:
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .first()
    )


def create_session(db: Session, user_id: int) -> UserSession:
    session = UserSession(
        user_id=user_id,
        state=ChatState.INITIAL,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_or_create_session(db: Session, user_id: int) -> UserSession:
    session = get_session_by_user_id(db, user_id)

    if session:
        return session

    return create_session(db, user_id)


def update_chat_state(
    db: Session,
    session: UserSession,
    new_state: ChatState,
) -> UserSession:
    session.state = new_state

    db.commit()
    db.refresh(session)

    return session


def get_selected_stall(
    session: UserSession,
) -> int | None:
    return session.selected_stall_id

def update_selected_stall(
    db: Session,
    session: UserSession,
    stall_id: int | None,
) -> UserSession:
    session.selected_stall_id = stall_id

    db.commit()
    db.refresh(session)

    return session

def reset_session(
    db: Session,
    session: UserSession,
) -> UserSession:
    """
    Reset the chatbot session to its initial ordering state.
    Clears all temporary conversation data.
    """

    session.state = ChatState.SELECTING_STALL

    # Clear temporary selections
    session.selected_stall_id = None

    # Reset menu pagination
    session.current_menu_page = 1

    # Update timestamp
    session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(session)

    return session

def update_current_menu_page(
    db: Session,
    session: UserSession,
    page: int,
) -> UserSession:

    session.current_menu_page = page
    db.commit()
    db.refresh(session)

    return session