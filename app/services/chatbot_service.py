from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.enums.chat_state import ChatState
from app.enums.user_role import UserRole
from app.services.pickup_slot_service import get_available_pickup_slots
from app.services.order_service import create_order_from_cart,cancel_order
from app.repositories.user_session_repository import reset_session
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories.stall_repository import get_food_stall_by_id
from app.repositories.menu_item_repository import (
    get_menu_items_by_stall_id,
    get_food_stall_by_id,
    get_menu_item_by_id,
    
    )

from app.utils.stall_utils import is_stall_open
from app.repositories.user_repository import (
    create_user,
    get_user_by_phone,
    get_user_by_registration_number,
    update_user_name,
    update_user_registration_number,
)
from app.repositories.order_repository import (
    get_latest_active_order_by_user,
)
from app.enums.cancelled_by import CancelledBy
from app.repositories.user_session_repository import (
    get_or_create_session,
    update_chat_state,
    update_selected_stall,
    update_current_menu_page
)

from app.services.cart_service import (
    add_item_to_cart,
    get_cart_summary,
)

from app.services.stall_service import get_stalls
import math
from app.utils.validators import is_valid_registration_number

MENU_PAGE_SIZE = 10

def get_or_create_user(db: Session, phone_number: str) -> User:
    phone = phone_number.replace("whatsapp:", "").strip()

    user = get_user_by_phone(db, phone)

    if user:
        return user

    user = User(
        phone_number=phone,
        role=UserRole.STUDENT,
    )

    return create_user(db, user)


def handle_building_cart(
    db: Session,
    user: User,
    session: UserSession,
    text: str,
) -> str:

    text = text.strip().upper()
    
    if session.selected_stall_id is None:
        return "❌ No stall selected."

    menu_items = get_menu_items_by_stall_id(
        db,
        session.selected_stall_id,
    )

    total_pages = math.ceil(
        len(menu_items) / MENU_PAGE_SIZE
    )

    if text == "NEXT":

        update_current_menu_page(
            db,
            session,
            min(
                total_pages,
                session.current_menu_page + 1,
            ),
        )

        return handle_viewing_menu(
            db,
            user,
            session,
        )

    if text == "PREV":

        update_current_menu_page(
            db,
            session,
            max(
                1,
                session.current_menu_page - 1,
            ),
        )

        return handle_viewing_menu(
            db,
            user,
            session,
        )

    if text == "DONE":

        update_chat_state(
            db,
            session,
            ChatState.SELECTING_SLOT,
        )

        return handle_selecting_slot(
            db,
            user,
            session,
            "",
        )

    if not text.isdigit():
        return (
            "❌ Invalid input.\n\n"
            "Reply with:\n"
            "• Item Number\n"
            "• NEXT\n"
            "• PREV\n"
            "• DONE"
        )

    menu_item = get_menu_item_by_id(
        db,
        int(text),
    )

    if not menu_item:
        return "❌ Invalid menu item."

    if menu_item.stall_id != session.selected_stall_id:
        return "❌ That item doesn't belong to this stall."

    if not menu_item.is_available:
        return "❌ This item is currently unavailable."

    add_item_to_cart(
        db,
        user.id,
        menu_item,
    )

    response = (
        f"✅ *{menu_item.name}* added to your cart.\n\n"
    )

    response += get_cart_summary(
        db,
        user.id,
    )

    response += (
        "\n\nReply with:\n"
        "• Another Item Number\n"
        "• NEXT\n"
        "• PREV\n"
        "• DONE"
    )

    return response

def handle_whatsapp_message(
    db: Session,
    sender_phone: str,
    message_text: str,
) -> str:
    
    user = get_or_create_user(db, sender_phone)
    
    session = get_or_create_session(db, user.id)
    
    text = message_text.strip()


    if text.strip().upper() in [
        "HI",
        "HELLO",
        "START",
        "MENU",
        "RESET",
        "RESTART",
    ]:
        reset_session(db, session)
    
        return handle_selecting_stall(
            db,
            user,
            session,
            "",
        )
        
    if text.upper() == "CANCEL":
        return handle_cancel_order(
            db=db,
            user=user,
            session=session,
        )
        
    if text.upper() == "HELP":
        return (
            "🤖 *MunchBot Help*\n\n"
            "🍽️ *HI* - Start a new order\n"
            "❌ *CANCEL* - Cancel your pending order\n"
            "📖 *HELP* - Show this help menu\n\n"
            "Need anything else? Just reply with one of the commands above."
        )

    

    if session.state == ChatState.INITIAL:
        return handle_initial(
            db,
            user,
            session,
        )

    elif session.state == ChatState.WAITING_FOR_NAME:
        return handle_waiting_for_name(
            db,
            user,
            session,
            text,
        )

    elif session.state == ChatState.WAITING_FOR_REGISTRATION:
        return handle_waiting_for_registration(
            db,
            user,
            session,
            text,
        )

    elif session.state == ChatState.SELECTING_STALL:
        return handle_selecting_stall(
            db,
            user,
            session,
            text,
        )
    
    elif session.state == ChatState.VIEWING_MENU:
        return handle_viewing_menu(
            db,
            user,
            session,
        )
        
    elif session.state == ChatState.BUILDING_CART:
        return handle_building_cart(
            db,
            user,
            session,
            text,
        )
    
    elif session.state == ChatState.SELECTING_SLOT:
        return handle_selecting_slot(
            db,
            user,
            session,
            text,
        )

    return "Something went wrong."

def handle_initial(
    db: Session,
    user: User,
    session: UserSession,
) -> str:

    # Returning user
    if user.name and user.registration_number:

        update_chat_state(
            db,
            session,
            ChatState.SELECTING_STALL,
        )

        return handle_selecting_stall(
            db,
            user,
            session,
            "",
        )

    # New user
    update_chat_state(
        db,
        session,
        ChatState.WAITING_FOR_NAME,
    )

    return (
        "👋 Welcome to *MunchBot*! 🍕\n\n"
        "I'm your food ordering assistant.\n\n"
        "Before we begin...\n\n"
        "😊 What's your name?"
    )

def handle_viewing_menu(
    db: Session,
    user: User,
    session: UserSession,
) -> str:

    if session.selected_stall_id is None:
        update_chat_state(
            db,
            session,
            ChatState.SELECTING_STALL,
        )

        return "⚠️ Please select a food stall first."

    stall = get_food_stall_by_id(
        db,
        session.selected_stall_id,
    )

    if not stall:
        return "❌ Selected stall no longer exists."

    menu_items = get_menu_items_by_stall_id(
        db,
        stall.id,
    )

    if not menu_items:
        return (
            f"🍽 *{stall.name}*\n\n"
            "No menu items are available right now."
        )

    total_pages = math.ceil(
        len(menu_items) / MENU_PAGE_SIZE
    )

    # Prevent invalid page numbers
    current_page = max(
        1,
        min(session.current_menu_page, total_pages),
    )

    start = (current_page - 1) * MENU_PAGE_SIZE
    end = start + MENU_PAGE_SIZE

    page_items = menu_items[start:end]

    response = (
        f"🍽 *{stall.name}*\n\n"
        f"📄 *Page {current_page}/{total_pages}*\n\n"
    )

    for item in page_items:
        response += (
            f"{item.id}. {item.name} - ₹{item.current_price}\n"
        )

    response += "\n"

    if current_page > 1:
        response += "⬅️ Reply *PREV* for previous page.\n"

    if current_page < total_pages:
        response += "➡️ Reply *NEXT* for next page.\n"

    response += (
        "\nReply with:\n"
        "• Item Number\n"
        "• NEXT\n"
        "• PREV"
    )

    update_chat_state(
        db,
        session,
        ChatState.BUILDING_CART,
    )

    return response

def handle_selecting_stall(
    db: Session,
    user: User,
    session: UserSession,
    text: str,
) -> str:

    stalls = get_stalls(
        db,
        only_open=True,
    )

    if not stalls:
        return "⚠️ No food stalls are currently open."

    # User has not selected a stall yet
    if session.selected_stall_id is None:

        # First visit to this state (or invalid input)
        if not text.isdigit():

            name = user.name or "Student"

            response = (
                f"👋 Welcome, {name}!\n\n"
                "🏪 *Available Food Stalls*\n\n"
            )

            for stall in stalls:
                response += f"{stall.id}. {stall.name}\n"

            response += "\nReply with the stall number."

            return response

        stall = get_food_stall_by_id(
            db,
            int(text),
        )

        if not stall or not is_stall_open(stall):
            return (
                "❌ Invalid stall number.\n\n"
                "Please choose one of the available stalls."
            )

        update_selected_stall(
            db,
            session,
            stall.id,
        )
        
        update_current_menu_page(
            db,
            session,
            1,
        )

        update_chat_state(
            db,
            session,
            ChatState.VIEWING_MENU,
        )

        return handle_viewing_menu(
            db,
            user,
            session,
        )

    return "Loading today's menu..."

def handle_waiting_for_registration(
    db: Session,
    user: User,
    session: UserSession,
    text: str,
) -> str:

    text = text.strip()

    if not is_valid_registration_number(text):
        return (
            "❌ Invalid Registration Number.\n\n"
            "Please enter a valid registration number."
        )

    existing = get_user_by_registration_number(
        db,
        text,
    )

    if existing and existing.id != user.id:
        return (
            "⚠️ This registration number is already registered.\n"
            "Please contact the administrator."
        )

    update_user_registration_number(
        db,
        user,
        text,
    )

    update_chat_state(
        db,
        session,
        ChatState.SELECTING_STALL,
    )

    return (
        f"🎉 Registration completed successfully!\n\n"
        f"Welcome, {user.name}! 👋\n\n"
        + handle_selecting_stall(
            db,
            user,
            session,
            "",
        )
    )
    

def handle_waiting_for_name(
    db: Session,
    user: User,
    session: UserSession,
    text: str,
) -> str:

    text = text.strip()

    update_user_name(
        db,
        user,
        text,
    )

    update_chat_state(
        db,
        session,
        ChatState.WAITING_FOR_REGISTRATION,
    )

    return (
        f"Nice to meet you, {text}! 😊\n\n"
        "Please enter your Registration Number."
    )
    
def handle_selecting_slot(
    db: Session,
    user: User,
    session: UserSession,
    text: str,
) -> str:

    available_slots = get_available_pickup_slots(db)

    if not available_slots:
        return (
            "❌ No pickup slots are currently available.\n"
            "Please try again later."
        )

    # First time entering this state
    if text == "":

        message = "🕒 *Available Pickup Slots*\n\n"

        for index, slot in enumerate(available_slots, start=1):

            message += (
                f"{index}. "
                f"{slot.start_time.strftime('%I:%M %p')} - "
                f"{slot.end_time.strftime('%I:%M %p')}\n"
            )

        message += (
            "\nReply with the slot number."
        )

        return message

    # User input validation
    if not text.isdigit():
        return "❌ Please reply with a valid slot number."

    slot_number = int(text)

    if (
        slot_number < 1
        or slot_number > len(available_slots)
    ):
        return "❌ Invalid slot number."

    selected_slot = available_slots[slot_number - 1]

    order = create_order_from_cart(
        db=db,
        user_id=user.id,
        pickup_slot_id=selected_slot.id,
    )

    reset_session(
        db=db,
        session=session,
    )

    return (
        "🎉 *Order Placed Successfully!*\n\n"
        f"🧾 Order Number: {order.order_number}\n"
        f"💰 Total: ₹{order.total_amount}\n"
        f"🕒 Pickup Time: "
        f"{selected_slot.start_time.strftime('%I:%M %p')} - "
        f"{selected_slot.end_time.strftime('%I:%M %p')}\n\n"
        "Thank you for ordering with MunchBot! 🍽️\n\n"
        'Reply "HI" anytime to place another order.'
    )
    
def handle_cancel_order(
    db: Session,
    user: User,
    session: UserSession,
) -> str:
    """
    Cancel the user's latest active order.
    """

    order = get_latest_active_order_by_user(
        db=db,
        user_id=user.id,
    )

    if order is None:
        return (
            "❌ You don't have any active orders to cancel."
        )

    try:
        cancel_order(
            db=db,
            order_id=order.id,
            cancel_reason="Cancelled by student via WhatsApp.",
            cancelled_by=CancelledBy.USER,
            user_id=user.id,
        )

        reset_session(
            db=db,
            session=session,
        )

        return (
            f"✅ Your order *{order.order_number}* has been cancelled successfully.\n\n"
            "Reply *HI* whenever you'd like to place a new order."
        )

    except HTTPException as e:

        if e.status_code == 400:
            return (
                "❌ Your order can no longer be cancelled because "
                "it has already been accepted by the cafeteria."
            )

        raise